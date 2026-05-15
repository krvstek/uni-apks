import json
import re
from pathlib import Path

from src.core.config import CONFIG_PATH, load_toml, parse_app_entries, parse_config
from src.core.logger import abort, epr

_RE_CLI_START = re.compile(r"^>.*CLI:")
_RE_CHANGELOG_END = re.compile(r"^\[.*Changelog\]")


def get_matrix(source: str) -> None:
    try:
        data = load_toml(CONFIG_PATH)
    except (FileNotFoundError, ValueError) as exc:
        abort(f"Config error: {exc}")

    main_cfg = parse_config(data)
    source_lower = source.lower()
    include: list[dict[str, str]] = []
    for entry in parse_app_entries(data, main_cfg):
        if not entry.enabled or entry.brand.lower() != source_lower:
            continue
        if entry.arch == "both":
            include.extend([{"id": entry.table, "arch": "arm64-v8a"}, {"id": entry.table, "arch": "arm-v7a"}])
        else:
            include.append({"id": entry.table})

    if not include:
        abort(f"No apps found for patch source '{source}'")

    print(json.dumps({"include": include}, ensure_ascii=False))

def combine_logs(logs_dir: Path | str) -> None:
    logs = sorted(Path(logs_dir).rglob("build.md"))
    if not logs:
        return

    green_lines: list[str] = []
    microg_line = ""
    collected: list[str] = []
    for log in logs:
        capturing = False
        current: list[str] = []
        for raw in log.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("- 🟢"):
                green_lines.append(f"{line}  ")
            elif not microg_line and line.startswith("▶️") and "MicroG" in line:
                microg_line = line
            if _RE_CLI_START.match(line):
                capturing = True
                current = []
            if capturing:
                current.append(f"{line}  ")
                if _RE_CHANGELOG_END.match(line):
                    collected.append("\n".join(current))
                    capturing = False

        if capturing:
            epr(f"Warning: unclosed CLI section in '{log}' - changelog end marker not found")

    if green_lines:
        print("\n".join(green_lines), end="\n\n")
    if microg_line:
        print(microg_line, end="\n\n")
    if unique := list(dict.fromkeys(collected)):
        print("\n\n".join(unique))