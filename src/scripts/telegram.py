import os
import re
import sys
from pathlib import Path

from src.core.logger import IS_GITHUB, abort, epr, pr
from src.core.network import NetworkManager


def _require_ci(script: str) -> None:
    if not IS_GITHUB:
        abort(f"'{script}' is only available in GitHub Actions")

def _parse_final_md(final_md: Path) -> tuple[list[str], str, str]:
    green_lines: list[str] = []
    microg_line: str = ""
    changelog_line: str = ""
    for line in final_md.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- 🟢"):
            green_lines.append(re.sub(r"`([^`]+)`", r"\1", stripped.removeprefix("- ")))
        elif stripped.startswith("▶️"):
            microg_line = stripped
        elif stripped.startswith("[🔗"):
            changelog_line = stripped

    return green_lines, microg_line, changelog_line

def _build_message(brand: str, green_lines: list[str], microg_line: str, changelog_line: str) -> str:
    parts: list[str] = [f"*New build! ({brand.capitalize()})*", ""]
    parts.extend(green_lines)
    if microg_line:
        parts.extend(["", microg_line])
    if changelog_line:
        parts.extend(["", changelog_line])

    return "\n".join(parts)

def notify(brand: str, final_md_path: str = "final.md") -> None:
    token = os.getenv("TG_TOKEN")
    chat = os.getenv("TG_CHAT")
    if not token or not chat:
        epr("TG_TOKEN or TG_CHAT not set, skipping notification")
        return

    path = Path(final_md_path)
    if not path.exists() or not path.stat().st_size:
        epr(f"'{final_md_path}' not found or empty, skipping notification")
        return

    green_lines, microg_line, changelog_line = _parse_final_md(path)
    if not green_lines:
        epr("No build results found in final.md, skipping notification")
        return

    msg = _build_message(brand, green_lines, microg_line, changelog_line)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat, "text": msg, "parse_mode": "Markdown", "link_preview_options": {"is_disabled": True}}
    pr(f"Sending Telegram notification for '{brand}' to '{chat}'")
    with NetworkManager() as net:
        resp = net.session.post(url, json=payload, timeout=(5, 10))
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