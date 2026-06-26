import os  # noqa: I001
import re
import shutil
import signal
import subprocess
import sys
from copy import replace
from pathlib import Path

from src.core.builder import run_build
from src.core.config import BUILD_DIR, CONFIG_PATH, TEMP_DIR, VALID_ARCHES, AppEntry, load_toml, parse_app_entries, parse_config
from src.core.logger import abort, epr, pr
from src.core.network import NetworkManager

_shutting_down = False


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.is_file():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"\'')

def _require_java(min_version: int = 21) -> None:
    if not shutil.which("java"):
        abort(f"Java not found. Please install Java {min_version} or higher")

    result = subprocess.run(["java", "-version"], capture_output=True, text=True)
    match = re.search(r'version "(\d+)', result.stderr)
    if not match:
        abort("Could not determine Java version")
    assert match

    version = int(match.group(1))
    if version < min_version:
        abort(f"Java {version} found, but Java {min_version}+ is required")

def _build(target_app: str | None = None, arch_override: str | None = None) -> int:
    _require_java()
    data = load_toml(CONFIG_PATH)
    main_cfg = parse_config(data)
    pr(f"Loaded config '{CONFIG_PATH}'")
    entries: list[AppEntry] = [e for e in parse_app_entries(data, main_cfg) if e.enabled and (not target_app or e.table == target_app)]
    if target_app and not entries:
        abort(f"App '{target_app}' not found in config")

    if arch_override:
        entries = [replace(e, arch=arch_override) for e in entries]

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for cl in TEMP_DIR.glob("*/changelog.md"):
        cl.write_text("", encoding="utf-8")

    Path("build.md").write_text("", encoding="utf-8")
    with NetworkManager() as net:
        success = run_build(entries, main_cfg, net)
    return 0 if success else 1

def _clear() -> int:
    for directory in (TEMP_DIR, BUILD_DIR):
        if directory.exists():
            shutil.rmtree(directory)
            pr(f"Removed '{directory}'")
        else:
            pr(f"'{directory}' already clean")

    if (build_md := Path("build.md")).exists():
        build_md.unlink()
        pr("Removed 'build.md'")
    return 0

def _sigint_handler(sig: int, frame: object) -> None:
    global _shutting_down
    if _shutting_down:
        return

    _shutting_down = True
    epr("Interrupted by user")
    for tmp in TEMP_DIR.rglob("tmp*"):
        shutil.rmtree(tmp, ignore_errors=True)
    for ks in TEMP_DIR.glob("*.keystore"):
        ks.unlink(missing_ok=True)
    os._exit(130)

def main() -> None:
    signal.signal(signal.SIGINT, _sigint_handler)
    _load_dotenv()
    match sys.argv[1:]:
        case []:
            sys.exit(_build())
        case ["clear"]:
            sys.exit(_clear())
        case [target, *rest] if not rest or rest[0] in VALID_ARCHES:
            sys.exit(_build(target_app=target, arch_override=rest[0] if rest else None))
        case [_, arch]:
            abort(f"Unknown arch '{arch}'. Valid: {', '.join(sorted(VALID_ARCHES))}")
        case _:
            epr(f"Unknown command: {' '.join(sys.argv[1:])}")
            abort("Usage: main.py [target] [arch] | clear")

if __name__ == "__main__":
    main()