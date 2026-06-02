import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.core.config import TEMP_DIR
from src.core.logger import pr, wpr
from src.core.network import NetworkManager

APKSIGNER: Path = Path("bin/apksigner.jar")
_KNOWN_PREFIXES = ("gitlab:", "github:")


class PrebuiltsError(Exception):
    pass

@dataclass(slots=True, frozen=True)
class Prebuilts:
    cli_jar: Path
    patches_mpp: Path

def _ver_key(ver: str) -> tuple[int, ...]:
    base = ver.split("-")[0]
    return tuple(int(x) for x in re.findall(r"\d+", base)) or (0,)

def _strip_src_prefix(src: str) -> str:
    for prefix in _KNOWN_PREFIXES:
        if src.startswith(prefix):
            return src[len(prefix):]
    raise PrebuiltsError(f"Unknown source scheme in {src!r}, expected one of {_KNOWN_PREFIXES}")

def get_highest_ver(versions: list[str]) -> str:
    clean = [v.strip() for v in versions if v.strip()]
    if not clean:
        raise ValueError("Empty version list")

    return max(clean, key=_ver_key)

def fetch_prebuilts(cli_src: str, cli_ver: str, patches_src: str, patches_ver: str, net: NetworkManager) -> Prebuilts:
    patches_org = _strip_src_prefix(patches_src).split("/")[0]
    cli_org = _strip_src_prefix(cli_src).split("/")[0]
    cl_dir = TEMP_DIR / patches_org.lower()
    cli_dir = TEMP_DIR / cli_org.lower()
    cl_dir.mkdir(parents=True, exist_ok=True)
    cli_dir.mkdir(parents=True, exist_ok=True)

    pr(f"Getting prebuilts ({patches_org})")
    cli_jar, cli_cl = _fetch_single_asset(cli_src, "CLI", cli_ver, "cli", "jar", cli_dir, net)
    patches_mpp, patches_cl = _fetch_single_asset(patches_src, "Patches", patches_ver, "patches", "mpp", cl_dir, net)
    combined = cli_cl + patches_cl
    if combined:
        with (cl_dir / "changelog.md").open("a", encoding="utf-8") as f:
            f.write(combined)

    return Prebuilts(cli_jar=cli_jar, patches_mpp=patches_mpp)

def _get_target_asset(assets: list, ext: str, src: str, ver: str) -> dict:
    matches = [a for a in assets if a.get("name", "").endswith(f".{ext}")]
    non_dev = [a for a in matches if "-dev" not in a.get("name", "")]
    target = non_dev if (len(matches) > 1 and non_dev) else matches
    if not target:
        raise PrebuiltsError(f"No asset (.{ext}) found for {src} @ {ver}")

    if len(target) > 1:
        wpr(f"More than 1 asset found for {src} @ {ver}, falling back to the first one")

    return target[0]

def _fetch_single_asset(src: str, tag: str, ver: str, fprefix: str, ext: str, cl_dir: Path, net: NetworkManager) -> tuple[Path, str]:
    gitlab = src.startswith("gitlab:")
    clean_src = _strip_src_prefix(src)
    if gitlab:
        project = clean_src.replace("/", "%2F")
        base_url = f"https://gitlab.com/api/v4/projects/{project}/releases"
    else:
        base_url = f"https://api.github.com/repos/{clean_src}/releases"

    release = None
    if ver == "dev":
        releases = json.loads(net.get(base_url) if gitlab else net.gh_get(base_url))
        ver = get_highest_ver([r["tag_name"] for r in releases if r.get("tag_name")])
    elif ver == "latest":
        latest_url = f"{base_url}/permalink/latest" if gitlab else f"{base_url}/latest"
        release = json.loads(net.get(latest_url) if gitlab else net.gh_get(latest_url))
        ver = release.get("tag_name", "")

    if file := _find_cached(cl_dir, fprefix, ver, ext, exclude_dev=False):
        tag_name = _tag_from_filename(file)
        if tag == "Patches" and tag_name:
            if gitlab:
                changelog = f"[🔗 » Changelog](https://gitlab.com/{clean_src}/-/releases/{tag_name})\n\n"
            else:
                changelog = f"[🔗 » Changelog](https://github.com/{clean_src}/releases/tag/{tag_name})\n\n"
        else:
            changelog = ""
        return file, changelog

    if release is None:
        release_url = f"{base_url}/{ver}" if gitlab else f"{base_url}/tags/{ver}"
        release = json.loads(net.get(release_url) if gitlab else net.gh_get(release_url))

    raw_assets = release.get("assets", {}).get("links", []) if gitlab else release.get("assets", [])
    asset = _get_target_asset(raw_assets, ext, src, ver)
    file = cl_dir / asset["name"]
    for old_file in cl_dir.glob(f"*{fprefix}-*.{ext}"):
        if old_file.is_file() and not old_file.name.startswith("tmp."):
            old_file.unlink(missing_ok=True)

    asset_url = (asset.get("direct_asset_url") or asset["url"]) if gitlab else asset["url"]
    pr(f"Getting '{asset['name']}' from '{asset_url}'")
    if gitlab:
        net.download(asset_url, file)
    else:
        net.gh_download(asset_url, file)
    tag_name = release.get("tag_name", "")
    changelog = f"> ⚙️ » {tag}: `{clean_src.split('/')[0]}/{asset['name']}`  \n"
    if tag == "Patches" and tag_name:
        if gitlab:
            changelog += f"[🔗 » Changelog](https://gitlab.com/{clean_src}/-/releases/{tag_name})\n\n"
        else:
            changelog += f"[🔗 » Changelog](https://github.com/{clean_src}/releases/tag/{tag_name})\n\n"

    return file, changelog

def _find_cached(dir_path: Path, fprefix: str, name_ver: str, ext: str, exclude_dev: bool) -> Path | None:
    pattern = f"*{fprefix}-*.{ext}" if name_ver == "*" else f"*{fprefix}-{name_ver.lstrip('v')}*.{ext}"
    candidates: list[Path] = []
    for f in dir_path.glob(pattern):
        if not f.is_file() or f.name.startswith("tmp."):
            continue
        if exclude_dev and "-dev" in f.name:
            continue
        candidates.append(f)

    return max(candidates, key=lambda f: _ver_key(f.name), default=None)

def _tag_from_filename(file: Path) -> str:
    m = re.search(r"-(\d[\w.]*)(?:-[^.]+)?\.\w+$", file.name)
    if m:
        return f"v{m.group(1)}"
    return ""