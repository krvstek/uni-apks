import json
import os
from pathlib import Path

from src.core.config import CONFIG_PATH, load_toml, parse_app_entries, parse_config
from src.core.logger import abort, epr, wpr
from src.core.network import NetworkManager, ResourceNotFoundError


def get_matrix(source: str) -> None:
    data = load_toml(CONFIG_PATH)
    main_cfg = parse_config(data)
    source_lower = source.lower()
    include: list[dict[str, str]] = []
    for entry in parse_app_entries(data, main_cfg):
        if not entry.enabled or entry.brand.lower() != source_lower:
            continue

        if entry.arch == "both":
            include.extend([{"id": entry.table, "arch": "arm64-v8a"}, {"id": entry.table, "arch": "armeabi-v7a"}])
        else:
            include.append({"id": entry.table})

    if not include:
        abort(f"No apps found for patch source '{source}'")

    print(json.dumps({"include": include}, ensure_ascii=False))

def check_builds_needed() -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        abort("GITHUB_REPOSITORY environment variable is not set")

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

    with NetworkManager() as net:
        our_releases_by_brand: dict[str, str] = {}
        try:
            our_releases_raw = net.gh_get(f"https://api.github.com/repos/{repo}/releases?per_page=100")
            for rel in json.loads(our_releases_raw):
                tag = rel.get("tag_name", "")
                brand = tag.split("-", 1)[1] if "-" in tag else ""
                if brand in seen and brand not in our_releases_by_brand:
                    our_releases_by_brand[brand] = rel.get("published_at", "") or ""
        except Exception as exc:
            epr(f"Failed to fetch our releases: {exc}")
            our_releases_by_brand = {}

        brands_to_build: list[str] = []
        for brand, patches_source in seen.items():
            our_date = our_releases_by_brand.get(brand, "")
            upstream_date = ""
            try:
                upstream_rel = json.loads(net.gh_get(f"https://api.github.com/repos/{patches_source}/releases/latest"))
                upstream_date = upstream_rel.get("published_at", "") or ""
            except ResourceNotFoundError:
                epr(f"No upstream release found for '{patches_source}', skipping brand '{brand}'")
                continue
            except Exception as exc:
                epr(f"Failed to fetch upstream release for '{patches_source}': {exc}")
                brands_to_build.append(brand)
                continue

            if not our_date or upstream_date > our_date:
                brands_to_build.append(brand)

    print(json.dumps(brands_to_build))

def _parse_log_file(log: Path, green_lines: list[str], collected: list[str]) -> str:
    microg_line = ""
    capturing = False
    current: list[str] = []
    with log.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            if line.startswith("- 🟢"):
                green_lines.append(f"{line}  ")
            elif not microg_line and line.startswith("▶️") and "MicroG" in line:
                microg_line = line

            if line.startswith(">") and "CLI:" in line:
                capturing = True
                current = []

            if capturing:
                current.append(f"{line}  ")
                if line.startswith("[") and "Changelog]" in line:
                    collected.append("\n".join(current))
                    capturing = False

    if capturing:
        wpr(f"Unclosed CLI section in '{log}', changelog end marker not found")

    return microg_line

def combine_logs(logs_dir: Path | str) -> None:
    logs = sorted(Path(logs_dir).rglob("build*.md"))
    if not logs:
        return

    green_lines: list[str] = []
    collected: list[str] = []
    microg_line = ""

    for log in logs:
        m_line = _parse_log_file(log, green_lines, collected)
        if not microg_line:
            microg_line = m_line

    if green_lines:
        print("\n".join(green_lines), end="\n\n")

    if microg_line:
        print(microg_line, end="\n\n")

    if unique := list(dict.fromkeys(collected)):
        print("\n\n".join(unique))