import base64
import os
import shutil
import tempfile
import zipfile
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from copy import replace
from pathlib import Path

from src.core.config import BUILD_DIR, TEMP_DIR, AppEntry, Config, parse_app_entries
from src.core.logger import abort, epr, pr
from src.core.network import NetworkManager
from src.core.patcher import PatcherCLI, PatcherError
from src.core.prebuilts import APKSIGNER, Prebuilts, fetch_prebuilts, get_highest_ver
from src.scrapers.base import AppMetadata, BaseScraper


class BuilderError(Exception):
    pass

def _make_scraper(source: str, net: NetworkManager) -> BaseScraper:
    from src.scrapers.apkmirror import APKMirrorScraper
    from src.scrapers.archive import ArchiveScraper
    from src.scrapers.uptodown import UptodownScraper

    match source:
        case "apkmirror":
            return APKMirrorScraper(net)
        case "uptodown":
            return UptodownScraper(net)
        case "archive":
            return ArchiveScraper(net)
        case _:
            raise ValueError(f"Unknown APK source: {source!r}")

def _get_scraper(src: str, url: str, net: NetworkManager, cache: dict) -> tuple[BaseScraper, AppMetadata]:
    if src not in cache:
        scraper = _make_scraper(src, net)
        cache[src] = (scraper, scraper.fetch_metadata(url))
    return cache[src]

def _find_pkg_name(entry: AppEntry, net: NetworkManager) -> tuple[str, str, dict]:
    cache: dict = {}
    for src, url in entry.dl_urls.items():
        try:
            _, metadata = _get_scraper(src, url, net, cache)
            if not metadata.pkg_name:
                raise ValueError("Empty package name")
            pr(f"Package name of '{entry.table}' is '{metadata.pkg_name}'")
            return metadata.pkg_name, src, cache
        except Exception as exc:
            epr(f"Could not find {entry.table} in {src}: {exc}")
    raise BuilderError(f"Package name not found for '{entry.table}'")

def _resolve_version(entry: AppEntry, patcher: PatcherCLI, list_patches: str, pkg_name: str, dl_from: str, cache: dict) -> tuple[str, bool]:
    match entry.version:
        case "auto":
            version = patcher.get_last_supported_version(list_patches, pkg_name, entry.included_patches)
            force = False
        case "latest":
            version = None
            force = True
        case specific:
            version = specific
            force = True

    if not version:
        _, metadata = cache[dl_from]
        pkgvers = metadata.versions
        try:
            version = get_highest_ver(pkgvers)
        except ValueError:
            version = pkgvers[0] if pkgvers else ""
        if not version:
            raise BuilderError(f"Could not determine version for '{entry.table}'")

    pr(f"Choosing version '{version}' for {entry.table}")
    return version, force

def _download_apk(entry: AppEntry, version: str, arch: str, pkg_name: str, net: NetworkManager, cache: dict) -> tuple[Path, Path]:
    arch_f = arch.replace(" ", "")
    version_f = version.replace(" ", "").lstrip("v")
    stock_apk = TEMP_DIR / f"{pkg_name}-{version_f}-{arch_f}.apk"
    stock_apkm = stock_apk.with_name(f"{stock_apk.name}.apkm")
    if stock_apk.exists() or stock_apkm.exists():
        return stock_apk, stock_apkm

    for src, url in entry.dl_urls.items():
        pr(f"Downloading '{entry.table}' from '{src}'")
        try:
            scraper, _ = _get_scraper(src, url, net, cache)
            scraper.download(url, version, stock_apk, arch, entry.dpi)
            if stock_apk.exists() or stock_apkm.exists():
                return stock_apk, stock_apkm
        except Exception as exc:
            epr(f"Failed to fetch '{entry.table}' from '{src}' (version='{version}', arch='{arch}'): {exc}")

    raise BuilderError(f"Stock APK not found for '{entry.table}'")

def _extract_base_apk(apkm: Path, pkg_name: str, dest_dir: Path) -> Path:
    with zipfile.ZipFile(apkm, "r") as zf:
        for name in ("base.apk", f"{pkg_name}.apk"):
            if name in zf.namelist():
                zf.extract(name, dest_dir)
                return dest_dir / name
    raise BuilderError(f"Neither 'base.apk' nor '{pkg_name}.apk' found inside {apkm.name}")

def _verify_sig(stock_apk: Path, stock_apkm: Path, pkg_name: str, patcher: PatcherCLI, table: str) -> None:
    try:
        if stock_apkm.exists():
            with tempfile.TemporaryDirectory(dir=TEMP_DIR) as tmp_dir:
                valid = patcher.check_signature(_extract_base_apk(stock_apkm, pkg_name, Path(tmp_dir)), pkg_name)
        else:
            valid = patcher.check_signature(stock_apk, pkg_name)
    except BuilderError as exc:
        raise BuilderError(f"Sig check failed for '{table}': {exc}") from exc
    if not valid:
        raise BuilderError(f"APK signature mismatch for '{table}'")

def _apply_patch(entry: AppEntry, arch: str, version: str, force: bool, patcher: PatcherCLI, list_patches: str, stock_apk: Path, stock_apkm: Path) -> Path:
    app_name_l = entry.app_name.lower().replace(" ", "-")
    brand_f = entry.brand.lower().replace(" ", "-")
    arch_f = arch.replace(" ", "")
    version_f = version.replace(" ", "").lstrip("v")
    auto_patches = [p for p in patcher.resolve_auto_patches(list_patches) if p]
    final_args = patcher.build_patch_args(included_patches=entry.included_patches, excluded_patches=entry.excluded_patches, exclusive=entry.exclusive_patches, extra_args=entry.patcher_args, arch=arch, auto_patches=auto_patches, force=force)
    base_name = f"{app_name_l}-{brand_f}"
    patched_apk = TEMP_DIR / f"{base_name}-{version_f}-{arch_f}.apk"
    stock_input = stock_apkm if stock_apkm.exists() else stock_apk

    pr(f"Building '{entry.table}'")
    patcher.patch(stock_input, patched_apk, final_args)

    apk_output = BUILD_DIR / f"{base_name}-v{version_f}-{arch_f}.apk"
    shutil.move(patched_apk, apk_output)
    return apk_output

def _build_single(entry: AppEntry, arch: str, label: str, net: NetworkManager, patcher: PatcherCLI) -> str | None:
    try:
        pkg_name, dl_from, cache = _find_pkg_name(entry, net)
        list_patches = patcher.list_patches(pkg_name)
        version, force = _resolve_version(entry, patcher, list_patches, pkg_name, dl_from, cache)
        stock_apk, stock_apkm = _download_apk(entry, version, arch, pkg_name, net, cache)
        _verify_sig(stock_apk, stock_apkm, pkg_name, patcher, label)
        apk_output = _apply_patch(entry, arch, version, force, patcher, list_patches, stock_apk, stock_apkm)
        pr(f"Built {label}: '{apk_output}'")
        if os.getenv("GITHUB_ACTIONS") == "true":
            return f"- 🟢 » {label}: [`{version}`](../../releases/download/{{TAG}}/{apk_output.name})"
        return f"- 🟢 » {label}: `{version}`"
    except (BuilderError, PatcherError, ValueError, Exception) as exc:
        epr(f"Building '{label}' failed! {exc}")
        return None

def run_build(data: dict[str, object], config: Config, net: NetworkManager, target_app: str | None = None, arch_override: str | None = None) -> bool:
    entries = [e for e in parse_app_entries(data, config) if e.enabled and (not target_app or e.table == target_app)]
    if target_app and not entries:
        abort(f"App '{target_app}' not found in config")

    if arch_override:
        entries = [replace(e, arch=arch_override) for e in entries]

    build_mode = os.getenv("BUILD_MODE", "")
    futures: list[Future[str | None]] = []
    ks_path: Path | None = None
    prebuilts_cache: dict[tuple[str, str, str, str], Prebuilts] = {}
    if ks_b64 := os.getenv("KEYSTORE_BASE64", ""):
        with tempfile.NamedTemporaryFile(dir=TEMP_DIR, suffix=".keystore", delete=False) as tf:
            tf.write(base64.b64decode(ks_b64))
            ks_path = Path(tf.name)
    
    patcher_cache: dict[tuple[str, str, str, str], PatcherCLI] = {}
    try:
        with ThreadPoolExecutor(max_workers=config.parallel_jobs) as pool:
            for entry in entries:
                if not entry.dl_from:
                    epr(f"No 'dlurl' option was set for '{entry.table}'")
                    continue

                patches_ver = "dev" if build_mode == "dev" else entry.patches_version
                prebuilts_key = (entry.cli_source, entry.cli_version, entry.patches_source, patches_ver)

                try:
                    if prebuilts_key not in prebuilts_cache:
                        prebuilts_cache[prebuilts_key] = fetch_prebuilts(cli_src=entry.cli_source, cli_ver=entry.cli_version, patches_src=entry.patches_source, patches_ver=patches_ver, net=net)
                    prebuilts = prebuilts_cache[prebuilts_key]
                except Exception as exc:
                    epr(f"Could not get prebuilts for '{entry.table}': {exc}")
                    continue

                if prebuilts_key not in patcher_cache:
                    patcher_cache[prebuilts_key] = PatcherCLI(prebuilts.cli_jar, prebuilts.patches_mpp, APKSIGNER, ks_path=ks_path)

                patcher = patcher_cache[prebuilts_key]
                arches = ("arm64-v8a", "arm-v7a") if entry.arch == "both" else (entry.arch,)

                for arch in arches:
                    label = entry.table if entry.arch == "all" else f"{entry.table} ({arch})"
                    futures.append(pool.submit(_build_single, entry, arch, label, net, patcher))
    finally:
        if ks_path:
            ks_path.unlink(missing_ok=True)

    for tmp in TEMP_DIR.rglob("tmp*"):
        shutil.rmtree(tmp, ignore_errors=True)

    log_lines: list[str] = []
    for fut in as_completed(futures):
        try:
            if r := fut.result():
                log_lines.append(r)
        except Exception as exc:
            epr(f"Build task raised unhandled exception: {exc}")

    if not log_lines:
        epr("All builds failed")
        return False

    changelogs = "".join(cl.read_text(encoding="utf-8") for cl in sorted(TEMP_DIR.glob("*/changelog.md")))
    Path("build.md").write_text("\n".join([*log_lines, "", "▶️ » Install [MicroG-RE](https://github.com/MorpheApp/MicroG-RE/releases) for YouTube and YT Music APKs\n", changelogs]), encoding="utf-8")
    pr("Done")
    return True