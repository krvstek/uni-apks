import json
import os
import sys
from datetime import datetime

from src.core.config import CONFIG_PATH, load_toml, parse_app_entries, parse_config
from src.core.logger import IS_GITHUB, abort, epr
from src.core.network import NetworkManager, ResourceNotFoundError


def _require_ci(script: str) -> None:
    if not IS_GITHUB:
        abort(f"'{script}' is only available in GitHub Actions")

def _fetch_latest_release(source: str, net: NetworkManager) -> tuple[str, str]:
    scheme, clean_src = source.split(":", 1)
    if scheme == "gitlab":
        project = clean_src.replace("/", "%2F")
        upstream_rel = json.loads(net.get(f"https://gitlab.com/api/v4/projects/{project}/releases/permalink/latest"))
        changelog_text = upstream_rel.get("description", "") or ""
        upstream_date = upstream_rel.get("released_at", "") or ""
    else:
        upstream_rel = json.loads(net.get(f"https://api.github.com/repos/{clean_src}/releases/latest", headers=net._gh_headers))
        changelog_text = upstream_rel.get("body", "") or ""
        upstream_date = upstream_rel.get("published_at", "") or ""

    return changelog_text, upstream_date

def _fetch_our_releases(repo: str, net: NetworkManager) -> dict[str, str]:
    our_releases_by_brand: dict[str, str] = {}
    try:
        our_releases_raw = net.get(f"https://api.github.com/repos/{repo}/releases?per_page=100", headers=net._gh_headers)
        for rel in json.loads(our_releases_raw):
            tag = rel.get("tag_name", "")
            brand = tag.split("-", 1)[1] if "-" in tag else ""
            if brand and brand not in our_releases_by_brand:
                our_releases_by_brand[brand] = rel.get("published_at", "") or ""
    except Exception as exc:
        epr(f"Failed to fetch our releases: {exc}")
        our_releases_by_brand = {}
    return our_releases_by_brand

def get_matrix(source: str) -> None:
    data = load_toml(CONFIG_PATH)
    main_cfg = parse_config(data)
    source_lower = source.lower()
    filter_changelog = os.getenv("FILTER_CHANGELOG", "false").lower() == "true"
    patches_source = ""
    has_changelog_keywords = False
    for entry in parse_app_entries(data, main_cfg):
        if entry.enabled and entry.brand.lower() == source_lower:
            patches_source = entry.patches_source
            if entry.changelog_keywords:
                has_changelog_keywords = True
                break

    changelog_text = ""
    if filter_changelog and has_changelog_keywords and patches_source:
        with NetworkManager() as net:
            repo = os.getenv("GITHUB_REPOSITORY")
            if repo:
                our_releases_by_brand = _fetch_our_releases(repo, net)
                our_date = our_releases_by_brand.get(source_lower, "")
                if our_date:
                    try:
                        changelog_text, _ = _fetch_latest_release(patches_source, net)
                    except Exception as exc:
                        epr(f"Failed to fetch changelog for '{patches_source}': {exc}")

    include: list[dict[str, str]] = []
    for entry in parse_app_entries(data, main_cfg):
        if not entry.enabled or entry.brand.lower() != source_lower:
            continue

        if filter_changelog and entry.changelog_keywords and changelog_text and not any(kw in changelog_text.lower() for kw in entry.changelog_keywords):
            continue

        if entry.arch == "both":
            include.extend([{"id": entry.table, "arch": "arm64-v8a"}, {"id": entry.table, "arch": "armeabi-v7a"}])
        else:
            include.append({"id": entry.table})

    if not include:
        abort(f"No apps found for patch source '{source}'")

    print(json.dumps({"include": include}, ensure_ascii=False))

def check_builds_needed(force_all: bool = False) -> None:
    data = load_toml(CONFIG_PATH)
    main_cfg = parse_config(data)
    seen: dict[str, str] = {}
    for entry in parse_app_entries(data, main_cfg):
        if not entry.enabled:
            continue
        brand = entry.brand.lower()
        if brand not in seen:
            seen[brand] = entry.patches_source

    if not seen:
        print(json.dumps([]))
        return

    if force_all:
        print(json.dumps(list(seen.keys())))
        return

    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        abort("GITHUB_REPOSITORY environment variable is not set")

    with NetworkManager() as net:
        our_releases_by_brand = _fetch_our_releases(repo, net)

        brands_to_build: list[str] = []
        for brand, patches_source in seen.items():
            our_date = our_releases_by_brand.get(brand, "")
            upstream_date = ""
            changelog_text = ""
            try:
                changelog_text, upstream_date = _fetch_latest_release(patches_source, net)
            except ResourceNotFoundError:
                epr(f"No upstream release found for '{patches_source}', skipping brand '{brand}'")
                continue
            except Exception as exc:
                epr(f"Failed to fetch upstream release for '{patches_source}': {exc}")
                brands_to_build.append(brand)
                continue

            if not our_date:
                brands_to_build.append(brand)
            elif upstream_date and datetime.fromisoformat(upstream_date) > datetime.fromisoformat(our_date):
                has_apps = False
                for app in parse_app_entries(data, main_cfg):
                    if app.enabled and app.brand.lower() == brand and (not app.changelog_keywords or any(kw in changelog_text.lower() for kw in app.changelog_keywords)):
                        has_apps = True
                        break
                if not has_apps:
                    continue
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