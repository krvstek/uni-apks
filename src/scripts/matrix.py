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
import os
import re
import sys
from datetime import datetime
from typing import Any

from src.core.config import CONFIG_PATH, AppEntry, load_toml, parse_app_entries, parse_config
from src.core.logger import IS_GITHUB, abort, epr
from src.core.network import NetworkManager, ResourceNotFoundError
from src.core.prebuilts import get_highest_ver, ver_key

_APK_ASSET_RE = re.compile(r"^([a-z0-9\-]+)-v(.+?)(?:-(?:all|arm64-v8a|armeabi-v7a|x86_64|x86))?\.apk$", re.IGNORECASE)


def _require_ci(script: str) -> None:
    if not IS_GITHUB:
        abort(f"'{script}' is only available in GitHub Actions")

def _fetch_latest_release(source: str, net: NetworkManager, version: str = "latest") -> tuple[str, str]:
    scheme, _, clean_src = source.partition(":")
    upstream_rel: dict[str, Any]
    if scheme == "gitlab":
        project = clean_src.replace("/", "%2F")
        upstream_rel = json.loads(net.get(f"https://gitlab.com/api/v4/projects/{project}/releases/permalink/latest"))
        changelog_text = str(upstream_rel.get("description") or "")
        upstream_date = str(upstream_rel.get("released_at") or "")
    elif version == "dev":
        releases: list[dict[str, Any]] = json.loads(net.get(f"https://api.github.com/repos/{clean_src}/releases?per_page=1", headers=net.gh_headers))
        upstream_rel = releases[0] if releases else {}
        changelog_text = str(upstream_rel.get("body") or "")
        upstream_date = str(upstream_rel.get("published_at") or "")
    else:
        upstream_rel = json.loads(net.get(f"https://api.github.com/repos/{clean_src}/releases/latest", headers=net.gh_headers))
        changelog_text = str(upstream_rel.get("body") or "")
        upstream_date = str(upstream_rel.get("published_at") or "")
    return changelog_text, upstream_date

def _fetch_our_releases(repo: str, net: NetworkManager) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    our_releases_by_brand: dict[str, str] = {}
    built_versions_by_brand: dict[str, dict[str, str]] = {}
    try:
        our_releases_raw = net.get(f"https://api.github.com/repos/{repo}/releases?per_page=100", headers=net.gh_headers)
        releases: list[dict[str, Any]] = json.loads(our_releases_raw)
        for rel in releases:
            tag = str(rel.get("tag_name") or "")
            brand = tag.partition("-")[2].lower()
            if not brand:
                continue
            if brand not in our_releases_by_brand:
                our_releases_by_brand[brand] = str(rel.get("published_at") or "")
            brand_built = built_versions_by_brand.setdefault(brand, {})
            for asset in rel.get("assets", []):
                name = str(asset.get("name") or "")
                if m := _APK_ASSET_RE.match(name):
                    base_name, ver = m.group(1).lower(), m.group(2)
                    if base_name not in brand_built:
                        brand_built[base_name] = ver
    except Exception as exc:
        epr(f"Failed to fetch our releases: {exc}")
    return our_releases_by_brand, built_versions_by_brand

def is_newer_version(new_ver: str, old_ver: str | None) -> bool:
    if not old_ver:
        return True
    if new_ver == old_ver:
        return False
    k_new = ver_key(new_ver)
    k_old = ver_key(old_ver)
    if k_new != k_old:
        return k_new > k_old
    full_new = tuple(int(x) for x in re.findall(r"\d+", new_ver))
    full_old = tuple(int(x) for x in re.findall(r"\d+", old_ver))
    return full_new > full_old

def _fetch_latest_source_version(entry: AppEntry, net: NetworkManager, scrapers: dict[str, Any]) -> str | None:
    from src.scrapers.apkmirror import APKMirrorScraper
    from src.scrapers.github import GitHubScraper

    for src, url in entry.dl_urls.items():
        if src not in scrapers:
            if src == "apkmirror":
                scrapers[src] = APKMirrorScraper(net)
            elif src == "github":
                scrapers[src] = GitHubScraper(net)
            else:
                continue
        try:
            metadata = scrapers[src].cached_metadata(url)
            if metadata.versions:
                return get_highest_ver(metadata.versions)
        except Exception as exc:
            epr(f"Failed to fetch source version for '{entry.table}' from '{src}': {exc}")
    return None

def _load_entries() -> list[AppEntry]:
    data = load_toml(CONFIG_PATH)
    return parse_app_entries(data, parse_config(data))

def get_matrix(source: str) -> None:
    source_lower = source.lower()
    filter_changelog = os.getenv("FILTER_CHANGELOG", "false").lower() == "true"
    patches_source = ""
    is_prerelease = False
    staged: list[AppEntry] = []
    for entry in _load_entries():
        if not entry.enabled or entry.brand.lower() != source_lower:
            continue
        if not patches_source:
            patches_source = next(iter(entry.patches), "")
        if any(spec["version"] == "dev" for spec in entry.patches.values()):
            is_prerelease = True
        staged.append(entry)

    changelog_text = ""
    patches_updated = True
    built_versions_by_brand: dict[str, dict[str, str]] = {}
    scrapers: dict[str, Any] = {}

    if filter_changelog:
        with NetworkManager() as net:
            repo = os.getenv("GITHUB_REPOSITORY")
            if repo and patches_source:
                our_releases_by_brand, built_versions_by_brand = _fetch_our_releases(repo, net)
                our_date = our_releases_by_brand.get(source_lower, "")
                version = "dev" if is_prerelease else "latest"
                try:
                    changelog_text, upstream_date = _fetch_latest_release(patches_source, net, version=version)
                    if our_date and upstream_date:
                        patches_updated = datetime.fromisoformat(upstream_date) > datetime.fromisoformat(our_date)
                except Exception as exc:
                    epr(f"Failed to fetch changelog for '{patches_source}': {exc}")

            changelog_lower = changelog_text.lower()
            brand_built = built_versions_by_brand.get(source_lower, {})
            include: list[dict[str, str]] = []

            for entry in staged:
                base_name = f"{entry.app_name.lower().replace(' ', '-')}-{source_lower}"
                built_ver = brand_built.get(base_name)
                has_new_apk = False
                if entry.track_apk and entry.dl_urls:
                    source_ver = _fetch_latest_source_version(entry, net, scrapers)
                    if source_ver and is_newer_version(source_ver, built_ver):
                        has_new_apk = True

                if patches_updated:
                    if entry.changelog_keywords and changelog_text and not any(kw in changelog_lower for kw in entry.changelog_keywords):
                        if not has_new_apk:
                            continue
                else:
                    if not entry.track_apk or not has_new_apk:
                        continue

                if entry.arch == "both":
                    include.extend([{"id": entry.table, "arch": "arm64-v8a"}, {"id": entry.table, "arch": "armeabi-v7a"}])
                else:
                    include.append({"id": entry.table})
    else:
        include = []
        for entry in staged:
            if entry.arch == "both":
                include.extend([{"id": entry.table, "arch": "arm64-v8a"}, {"id": entry.table, "arch": "armeabi-v7a"}])
            else:
                include.append({"id": entry.table})

    if not include:
        abort(f"No apps found for patch source '{source}'")
    print(json.dumps({"include": include, "prerelease": is_prerelease}, ensure_ascii=False))

def check_builds_needed(force_all: bool = False) -> None:
    seen: dict[str, str] = {}
    dev_brands: set[str] = set()
    entries = _load_entries()
    for entry in entries:
        if not entry.enabled:
            continue
        brand = entry.brand.lower()
        if brand not in seen:
            seen[brand] = next(iter(entry.patches), "")
        if any(spec["version"] == "dev" for spec in entry.patches.values()):
            dev_brands.add(brand)

    if not seen:
        print(json.dumps([]))
        return

    if force_all:
        print(json.dumps(list(seen.keys())))
        return

    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        abort("GITHUB_REPOSITORY environment variable is not set")

    entries_by_brand: dict[str, list[AppEntry]] = {}
    for entry in entries:
        if entry.enabled:
            entries_by_brand.setdefault(entry.brand.lower(), []).append(entry)

    with NetworkManager() as net:
        our_releases_by_brand, built_versions_by_brand = _fetch_our_releases(repo, net)
        scrapers: dict[str, Any] = {}
        brands_to_build: list[str] = []

        for brand, patches_source in seen.items():
            our_date = our_releases_by_brand.get(brand, "")
            try:
                changelog_text, upstream_date = _fetch_latest_release(patches_source, net, version="dev" if brand in dev_brands else "latest")
            except ResourceNotFoundError:
                epr(f"No upstream release found for '{patches_source}', skipping brand '{brand}'")
                continue
            except Exception as exc:
                epr(f"Failed to fetch upstream release for '{patches_source}': {exc}")
                brands_to_build.append(brand)
                continue

            patches_updated = (not our_date) or (bool(upstream_date) and datetime.fromisoformat(upstream_date) > datetime.fromisoformat(our_date))
            if patches_updated:
                changelog_lower = changelog_text.lower()
                has_apps = False
                for app in entries_by_brand.get(brand, []):
                    if not app.changelog_keywords or any(kw in changelog_lower for kw in app.changelog_keywords):
                        has_apps = True
                        break
                if has_apps:
                    brands_to_build.append(brand)
                    continue

            # Check if any app with track_apk has a newer version on source
            brand_built = built_versions_by_brand.get(brand, {})
            apk_update_found = False
            for app in entries_by_brand.get(brand, []):
                if not app.track_apk or not app.dl_urls:
                    continue
                base_name = f"{app.app_name.lower().replace(' ', '-')}-{brand}"
                built_ver = brand_built.get(base_name)
                source_ver = _fetch_latest_source_version(app, net, scrapers)
                if source_ver and is_newer_version(source_ver, built_ver):
                    apk_update_found = True
                    break

            if apk_update_found:
                brands_to_build.append(brand)

    print(json.dumps(brands_to_build))

def main() -> None:
    _require_ci("matrix.py")
    match sys.argv[1:]:
        case ["get-matrix"]:
            check_builds_needed()
        case ["get-matrix-force"]:
            check_builds_needed(force_all=True)
        case ["get-matrix", source]:
            get_matrix(source)
        case _:
            abort("Usage: matrix.py get-matrix [source] | get-matrix-force")

if __name__ == "__main__":
    main()
