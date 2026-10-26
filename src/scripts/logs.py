# ---------------------------------------------------------
# Copyright (C) 2026 krvstek
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

import sys
from pathlib import Path

from src.core.logger import IS_GITHUB, abort


def _require_ci(script: str) -> None:
    if not IS_GITHUB:
        abort(f"'{script}' is only available in GitHub Actions")

def _parse_log_file(log: Path, green_lines: list[str], collected: list[str]) -> str:
    microg_line = ""
    lines = [s for ln in log.read_text(encoding="utf-8").splitlines() if (s := ln.strip())]
    for i, line in enumerate(lines):
        if line.startswith("- 🟢"):
            green_lines.append(f"{line}  ")
        elif not microg_line and line.startswith("▶️") and "MicroG" in line:
            microg_line = line
        elif line.startswith("> ⚙️ » CLI:"):
            collected.append(f"{line}  ")
        elif line.startswith("> ⚙️ » Patches:"):
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            collected.append(f"{line}  \n{next_line}  ")
    return microg_line

def combine_logs(logs_dir: Path | str = "logs") -> None:
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

def main() -> None:
    _require_ci("logs.py")
    match sys.argv[1:]:
        case ["combine-logs"]:
            combine_logs()
        case ["combine-logs", logs_dir]:
            combine_logs(logs_dir)
        case _:
            abort("Usage: logs.py combine-logs [dir]")

if __name__ == "__main__":
    main()
