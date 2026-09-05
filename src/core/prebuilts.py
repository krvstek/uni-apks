# ---------------------------------------------------------
# Copyright (C) 2026 krvstek (Original Author)
# Copyright (C) 2026 The uni-apks Contributors (Modifications)
# 
# DO NOT REMOVE OR ALTER THIS COPYRIGHT HEADER.
# This file is part of uni-apks.
# Canonical source: https://github.com/krvstek/uni-apks
#
# Licensed under the GNU GPLv3. You may modify this file,
# but you MUST keep this original copyright notice intact
# and prominently state any changes made.
# See the AUTHORS file in the root directory for details.
# ---------------------------------------------------------

import json
import re
from pathlib import Path
from typing import Any

from src.core.config import TEMP_DIR
from src.core.logger import pr, wpr
from src.core.network import NetworkManager

APKSIGNER: Path = Path("bin/apksigner.jar")
_KNOWN_PREFIXES = ("gitlab:", "github:")


class PrebuiltsError(Exception):
    pass

def _ver_key(ver: str) -> tuple[int, ...]:
    base = ver.split("-")[0]
    return tuple(int(x) for x in re.findall(r"\d+", base)) or (0,)

def _strip_src_prefix(src: str) -> str:
    for prefix in _KNOWN_PREFIXES:
        if src.startswith(prefix):
            return src.removeprefix(prefix)
    raise PrebuiltsError(f"Unknown source scheme in {src!r}, expected one of {_KNOWN_PREFIXES}")

def get_highest_ver(versions: list[str]) -> str:
    clean = [v.strip() for v in versions if v.strip()]
    if not clean:
        raise ValueError("Empty version list")
    return max(clean, key=_ver_key)

def fetch_cli(cli_src: str, cli_ver: str, net: NetworkManager) -> Path:
    cli_org = _strip_src_prefix(cli_src).split("/")[0]
    cli_dir = TEMP_DIR / cli_org.lower()
    cli_dir.mkdir(parents=True, exist_ok=True)
    jar, changelog = _fetch_single_asset(cli_src, "CLI", cli_ver, "jar", cli_dir, net)
    if changelog:
        with (cli_dir / "changelog.md").open("a", encoding="utf-8") as f:
            f.write(changelog)
    return jar

def fetch_mpp(src: str, ver: str, net: NetworkManager) -> Path:
    org = _strip_src_prefix(src).split("/")[0]
    cl_dir = TEMP_DIR / org.lower()
    cl_dir.mkdir(parents=True, exist_ok=True)
    mpp, changelog = _fetch_single_asset(src, "Patches", ver, "mpp", cl_dir, net)
    if changelog:
        with (cl_dir / "changelog.md").open("a", encoding="utf-8") as f:
            f.write(changelog)
    return mpp

def _get_target_asset(assets: list[dict[str, Any]], ext: str, src: str, ver: str) -> dict[str, Any]:
    suffix = f".{ext}"
    matches: list[dict[str, Any]] = []
    non_dev: list[dict[str, Any]] = []
    for a in assets:
        name = a.get("name", "")
        if not name.endswith(suffix):
            continue
        matches.append(a)
        if "-dev" not in name:
            non_dev.append(a)

    target = non_dev if (len(matches) > 1 and non_dev) else matches
    if not target:
        raise PrebuiltsError(f"No asset (.{ext}) found for {src} @ {ver}")

    if len(target) > 1:
        wpr(f"More than 1 asset found for {src} @ {ver}, falling back to the first one")
    return target[0]

def _build_changelog(tag: str, org: str, name: str, tag_name: str, gitlab: bool, clean_src: str) -> str:
    changelog = f"> ⚙️ » {tag}: `{org}/{name}`  \n"
    if tag == "Patches" and tag_name:
        if gitlab:
            changelog += f"[🔗 » Changelog](https://gitlab.com/{clean_src}/-/releases/{tag_name})\n\n"
        else:
            changelog += f"[🔗 » Changelog](https://github.com/{clean_src}/releases/tag/{tag_name})\n\n"
    return changelog

def _fetch_single_asset(src: str, tag: str, ver: str, ext: str, cl_dir: Path, net: NetworkManager) -> tuple[Path, str]:
    gitlab = src.startswith("gitlab:")
    clean_src = _strip_src_prefix(src)
    org = clean_src.split("/")[0]
    if gitlab:
        project = clean_src.replace("/", "%2F")
        base_url = f"https://gitlab.com/api/v4/projects/{project}/releases"
    else:
        base_url = f"https://api.github.com/repos/{clean_src}/releases"

    release = None
    if ver == "dev":
        releases = json.loads(net.get(base_url) if gitlab else net.get(base_url, headers=net.gh_headers))
        ver = get_highest_ver([r["tag_name"] for r in releases if r.get("tag_name")])
    elif ver == "latest":
        latest_url = f"{base_url}/permalink/latest" if gitlab else f"{base_url}/latest"
        release = json.loads(net.get(latest_url) if gitlab else net.get(latest_url, headers=net.gh_headers))
        ver = release.get("tag_name", "")

    if file := _find_cached(cl_dir, ver, ext):
        tag_name = _tag_from_filename(file)
        return file, _build_changelog(tag, org, file.name, tag_name, gitlab, clean_src)

    if release is None:
        release_url = f"{base_url}/{ver}" if gitlab else f"{base_url}/tags/{ver}"
        release = json.loads(net.get(release_url) if gitlab else net.get(release_url, headers=net.gh_headers))

    raw_assets = release.get("assets", {}).get("links", []) if gitlab else release.get("assets", [])
    asset = _get_target_asset(raw_assets, ext, src, ver)
    file = cl_dir / asset["name"]
    for old_file in cl_dir.glob(f"*.{ext}"):
        if old_file.is_file() and not old_file.name.startswith("tmp."):
            old_file.unlink(missing_ok=True)

    asset_url = (asset.get("direct_asset_url") or asset["url"]) if gitlab else asset["url"]
    pr(f"Getting '{asset['name']}' from '{asset_url}'")
    if gitlab:
        net.download(asset_url, file)
    else:
        net.download(asset_url, file, headers=net.gh_headers | {"Accept": "application/octet-stream"})

    tag_name = release.get("tag_name", "")
    return file, _build_changelog(tag, org, asset["name"], tag_name, gitlab, clean_src)

def _find_cached(dir_path: Path, name_ver: str, ext: str) -> Path | None:
    pattern = f"*.{ext}" if name_ver == "*" else f"*{name_ver.lstrip('v')}*.{ext}"
    candidates: list[Path] = []
    for f in dir_path.glob(pattern):
        if not f.is_file() or f.name.startswith("tmp."):
            continue
        candidates.append(f)
    return max(candidates, key=lambda f: _ver_key(f.name), default=None)

def _tag_from_filename(file: Path) -> str:
    m = re.search(r"-(\d[\w.]*)(?:-[^.]+)?\.\w+$", file.name)
    if m:
        return f"v{m.group(1)}"
    return ""