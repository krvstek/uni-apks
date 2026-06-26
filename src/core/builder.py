import base64
import os
import re
import shutil
import tempfile
import zipfile
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

from src.core.config import BUILD_DIR, TEMP_DIR, AppEntry, Config
from src.core.logger import IS_GITHUB, epr, pr, wpr
from src.core.network import NetworkError, NetworkManager
from src.core.patcher import PatcherCLI, PatcherError, SignatureError
from src.core.prebuilts import APKSIGNER, fetch_cli, fetch_mpp, get_highest_ver
from src.scrapers.base import BaseScraper, DownloadResult, ScraperError

_failed_signatures: set[str] = set()


class BuilderError(Exception):
    pass

def _make_scraper(source: str, net: NetworkManager) -> BaseScraper:
    from src.scrapers.apkmirror import APKMirrorScraper
    from src.scrapers.github import GitHubScraper
    from src.scrapers.uptodown import UptodownScraper
    match source:
        case "apkmirror":
            return APKMirrorScraper(net)
        case "github":
            return GitHubScraper(net)
        case "uptodown":
            return UptodownScraper(net)
        case _:
            raise ValueError(f"Unknown APK source: {source!r}")

def _find_pkg_name(entry: AppEntry, scrapers: dict[str, BaseScraper]) -> tuple[str, str, set[str]]:
    failed: set[str] = set()
    for src, url in entry.dl_urls.items():
        try:
            metadata = scrapers[src].cached_metadata(url)
            pr(f"Package name of '{entry.table}' is '{metadata.pkg_name}'")
            return metadata.pkg_name, src, failed
        except (NetworkError, ScraperError) as exc:
            epr(f"Could not find '{entry.table}' in '{src}': {exc}")
            failed.add(src)
    raise BuilderError("Package name not found")

def _resolve_version(entry: AppEntry, patcher: PatcherCLI, list_patches: str, pkg_name: str, dl_from: str, scrapers: dict[str, BaseScraper]) -> tuple[str, bool]:
    if entry.version not in ("auto", "latest"):
        version, is_custom = entry.version, True
    elif entry.version == "auto" and (v := patcher.get_last_supported_version(list_patches, pkg_name, entry.patches)):
        version, is_custom = v, False
    else:
        versions = scrapers[dl_from].cached_metadata(entry.dl_urls[dl_from]).versions
        version = get_highest_ver(versions) if versions else ""
        if not version:
            raise BuilderError("Could not determine version")
        is_custom = entry.version != "auto"

    pr(f"Choosing version '{version}' for '{entry.table}'")
    return version, is_custom

def _download_apk(entry: AppEntry, version: str, arch: str, pkg_name: str, scrapers: dict[str, BaseScraper], dl_from: str, failed_sources: set[str]) -> DownloadResult:
    arch_f = arch.replace(" ", "")
    version_f = version.replace(" ", "").lstrip("v")
    base_name = f"{pkg_name}-v{version_f}-{arch_f}.apk"
    stock_apk = TEMP_DIR / base_name
    if stock_apk.exists():
        return DownloadResult(path=stock_apk, is_bundle=False)

    stock_apkm = stock_apk.with_suffix(".apkm")
    if stock_apkm.exists():
        return DownloadResult(path=stock_apkm, is_bundle=True)

    ordered_sources = [dl_from] + [src for src in entry.dl_urls if src != dl_from]
    for src in ordered_sources:
        if src in failed_sources:
            continue

        url = entry.dl_urls[src]
        pr(f"Downloading '{entry.table}' from '{src}'")
        try:
            return scrapers[src].download(url, version, stock_apk, arch, entry.dpi)
        except (NetworkError, ScraperError) as exc:
            epr(f"Failed to fetch '{entry.table}' from '{src}' (version='{version}', arch='{arch}'): {exc}")
    raise BuilderError("Stock APK not found")

def _extract_base_apk(apkm: Path, pkg_name: str, dest_dir: Path) -> Path:
    with zipfile.ZipFile(apkm, "r") as zf:
        names = zf.NameToInfo
        for name in ("base.apk", f"{pkg_name}.apk"):
            if name in names:
                zf.extract(name, dest_dir)
                return dest_dir / name
    raise BuilderError(f"Neither 'base.apk' nor '{pkg_name}.apk' found inside {apkm.name}")

def _verify_sig(dl_result: DownloadResult, pkg_name: str, patcher: PatcherCLI, table: str, skip_sigcheck: bool, strict_sigcheck: bool) -> None:
    if skip_sigcheck:
        wpr(f"Skipping APK signature verification for '{table}'")
        return

    if not patcher.has_signature(pkg_name):
        msg = f"No signature entry found in sig.txt for '{pkg_name}'"
        if strict_sigcheck:
            raise SignatureError(msg)

        wpr(f"{msg}, skipping it")
        return

    if not dl_result.is_bundle:
        if not patcher.check_signature(dl_result.path, pkg_name):
            raise SignatureError("APK signature mismatch")
        return

    with tempfile.TemporaryDirectory(dir=TEMP_DIR) as tmp_dir:
        apk_path = _extract_base_apk(dl_result.path, pkg_name, Path(tmp_dir))
        if not patcher.check_signature(apk_path, pkg_name):
            raise SignatureError("Bundle APK signature mismatch")

def _apply_patch(entry: AppEntry, arch: str, version: str, force: bool, patcher: PatcherCLI, list_patches: str, dl_result: DownloadResult) -> Path:
    arch_f = arch.replace(" ", "")
    version_f = version.replace(" ", "").lstrip("v")
    auto_patches = patcher.resolve_auto_patches(list_patches)
    final_args = patcher.build_patch_args(patches=entry.patches, extra_args=entry.patcher_args, arch=arch, auto_patches=auto_patches, exclusive=entry.exclusive_patches, force=force)
    base_name = f"{entry.app_name.lower().replace(" ", "-")}-{entry.brand.lower().replace(" ", "-")}"
    apk_name = f"{base_name}-v{version_f}-{arch_f}.apk"
    patched_apk = TEMP_DIR / apk_name

    pr(f"Building '{entry.table}'")
    patcher.patch(dl_result.path, patched_apk, final_args)
    apk_output = BUILD_DIR / apk_name
    shutil.move(patched_apk, apk_output)
    return apk_output

def _build_single(entry: AppEntry, arch: str, label: str, net: NetworkManager, patcher: PatcherCLI, strict_sigcheck: bool) -> str | None:
    if entry.table in _failed_signatures:
        epr(f"Skipped '{label}' due to previous signature mismatch")
        return None

    try:
        scrapers = {src: _make_scraper(src, net) for src in entry.dl_urls}
        pkg_name, dl_from, failed_sources = _find_pkg_name(entry, scrapers)
        list_patches = patcher.list_patches(pkg_name)
        version, force = _resolve_version(entry, patcher, list_patches, pkg_name, dl_from, scrapers)
        dl_result = _download_apk(entry, version, arch, pkg_name, scrapers, dl_from, failed_sources)
        _verify_sig(dl_result, pkg_name, patcher, label, entry.skip_sigcheck, strict_sigcheck)
        apk_output = _apply_patch(entry, arch, version, force, patcher, list_patches, dl_result)
        pr(f"Built {label}: '{apk_output}'")
        github_asset_name = re.sub(r"\.+", ".", re.sub(r"[^a-zA-Z0-9@+\-_.]", ".", apk_output.name))
        ver_str = f"[`{version}`](https://github.com/{os.getenv('GITHUB_REPOSITORY')}/releases/download/{{TAG}}/{github_asset_name})" if IS_GITHUB else f"`{version}`"
        return f"- 🟢 » {label}: {ver_str}"
    except (BuilderError, PatcherError, ScraperError, NetworkError, SignatureError) as exc:
        if isinstance(exc, SignatureError):
            _failed_signatures.add(entry.table)

        epr(f"Building '{label}' failed! {exc}")
        return None

def _submit_entries(entries: list[AppEntry], pool: ThreadPoolExecutor, net: NetworkManager, ks_path: Path | None, strict_sigcheck: bool) -> list[Future[str | None]]:
    futures: list[Future[str | None]] = []
    cli_cache: dict[tuple[str, str], Path] = {}
    for e in entries:
        if not e.dl_urls:
            continue

        key = (e.cli_source, e.cli_version)
        if key not in cli_cache:
            try:
                cli_cache[key] = fetch_cli(e.cli_source, e.cli_version, net)
            except Exception as exc:
                epr(f"Could not fetch CLI '{e.cli_source}': {exc}")

    all_patch_srcs = {(src, spec["version"]) for e in entries if e.dl_urls for src, spec in e.patches.items()}
    mpp_map: dict[tuple[str, str], Path] = {}
    for src, ver in all_patch_srcs:
        try:
            mpp_map[(src, ver)] = fetch_mpp(src, ver, net)
        except Exception as exc:
            epr(f"Could not fetch patches from '{src}': {exc}")

    for entry in entries:
        if not entry.dl_urls:
            epr(f"No 'dlurl' option was set for '{entry.table}'")
            continue
        if not entry.patches:
            epr(f"No 'patches' table defined for '{entry.table}'")
            continue

        cli_key = (entry.cli_source, entry.cli_version)
        if cli_key not in cli_cache:
            continue

        app_mpp_map = {(src, spec["version"]): mpp_map[(src, spec["version"])] for src, spec in entry.patches.items() if (src, spec["version"]) in mpp_map}
        if not app_mpp_map:
            epr(f"No patch files available for '{entry.table}'")
            continue

        patcher = PatcherCLI(cli_cache[cli_key], app_mpp_map, APKSIGNER, ks_path=ks_path)
        arches = ("arm64-v8a", "armeabi-v7a") if entry.arch == "both" else (entry.arch,)
        for arch in arches:
            label = entry.app_name if entry.arch == "all" else f"{entry.app_name} ({arch})"
            futures.append(pool.submit(_build_single, entry, arch, label, net, patcher, strict_sigcheck))
    return futures

def run_build(entries: list[AppEntry], config: Config, net: NetworkManager) -> bool:
    if not entries:
        epr("No entries to build")
        return False

    ks_path: Path | None = None
    if ks_b64 := os.getenv("KEYSTORE_BASE64"):
        with tempfile.NamedTemporaryFile(dir=TEMP_DIR, suffix=".keystore", delete=False) as tf:
            tf.write(base64.b64decode(ks_b64))
            ks_path = Path(tf.name)

    try:
        with ThreadPoolExecutor(max_workers=config.parallel_jobs) as pool:
            futures = _submit_entries(entries, pool, net, ks_path, config.strict_sigcheck)
    finally:
        if ks_path:
            ks_path.unlink(missing_ok=True)

    for tmp in TEMP_DIR.rglob("tmp*"):
        shutil.rmtree(tmp, ignore_errors=True)

    log_lines: list[str] = []
    for fut in as_completed(futures):
        if r := fut.result():
            log_lines.append(r)

    if not log_lines:
        epr("All builds failed")
        return False

    raw = "".join(cl.read_text(encoding="utf-8") for cl in sorted(TEMP_DIR.glob("*/changelog.md")))
    block_re = re.compile(r"^> ⚙️ » (CLI|Patches):.*?(?=^> ⚙️ »|\Z)", re.MULTILINE | re.DOTALL)
    cli_blocks: list[str] = []
    patch_blocks: list[str] = []
    for m in block_re.finditer(raw):
        (cli_blocks if m.group(1) == "CLI" else patch_blocks).append(m.group())
    changelogs = "".join(cli_blocks) + "".join(patch_blocks)
    microg_line = "▶️ » Install [MicroG-RE](https://github.com/MorpheApp/MicroG-RE/releases) to enable Google account sign-in for supported apps\n"
    Path("build.md").write_text("\n".join([*log_lines, "", microg_line, changelogs]), encoding="utf-8")
    pr("Done")
    return True