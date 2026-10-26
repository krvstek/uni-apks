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

import os
import re
import sys
from pathlib import Path

from curl_cffi import requests as curl_requests

from src.core.logger import IS_GITHUB, abort, epr, pr

_BACKTICK_RE = re.compile(r"`([^`]+)`")


def _require_ci(script: str) -> None:
    if not IS_GITHUB:
        abort(f"'{script}' is only available in GitHub Actions")

def _parse_final_md(final_md: Path) -> tuple[list[str], str, list[str]]:
    green_lines: list[str] = []
    microg_line: str = ""
    changelog_lines: list[str] = []
    for line in final_md.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- 🟢"):
            green_lines.append(_BACKTICK_RE.sub(r"\1", stripped.removeprefix("- ")))
        elif not microg_line and stripped.startswith("▶️"):
            microg_line = stripped
        elif stripped.startswith("[🔗"):
            if m := re.search(r"\[(.*?)]\((.*?)\)", stripped):
                link_text, url = m.group(1), m.group(2)
                org = url.split("/")[3] if url.count("/") >= 3 else ""
                changelog_lines.append(f"[{link_text} ({org})]({url})" if org else stripped)
            else:
                changelog_lines.append(stripped)
    return green_lines, microg_line, changelog_lines

def _build_message(brand: str, green_lines: list[str], microg_line: str, changelog_lines: list[str]) -> str:
    parts: list[str] = [f"*New build! ({brand.capitalize()})*", ""]
    parts.extend(green_lines)
    if microg_line:
        parts.extend(["", microg_line])
    if changelog_lines:
        parts.append("")
        parts.extend(changelog_lines)
    return "\n".join(parts)

def notify(brand: str, final_md_path: Path | str = "final.md") -> None:
    token = os.getenv("TG_TOKEN")
    chat = os.getenv("TG_CHAT")
    if not token or not chat:
        epr("TG_TOKEN or TG_CHAT not set, skipping notification")
        return

    path = Path(final_md_path)
    if not path.is_file() or path.stat().st_size == 0:
        epr(f"'{final_md_path}' not found or empty, skipping notification")
        return

    green_lines, microg_line, changelog_lines = _parse_final_md(path)
    if not green_lines:
        epr("No build results found in final.md, skipping notification")
        return

    msg = _build_message(brand, green_lines, microg_line, changelog_lines)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat, "text": msg, "parse_mode": "Markdown", "link_preview_options": {"is_disabled": True}}
    pr(f"Sending Telegram notification for '{brand}' to '{chat}'")
    # noinspection PyArgumentList
    with curl_requests.Session() as session:
        resp = session.post(url, json=payload, timeout=(5, 10))
        if resp.status_code != 200:
            epr(f"Telegram API error {resp.status_code}: {resp.text}")
        else:
            pr("Telegram notification sent successfully")

def main() -> None:
    _require_ci("telegram.py")
    match sys.argv[1:]:
        case ["notify", brand]:
            notify(brand)
        case ["notify", brand, final_md]:
            notify(brand, final_md)
        case _:
            abort("Usage: telegram.py notify <brand> [final_md_path]")

if __name__ == "__main__":
    main()
