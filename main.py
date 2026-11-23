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

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from src.core.builder import run_build
from src.core.config import BUILD_DIR, CONFIG_PATH, CONFIGS_DIR, TEMP_DIR, VALID_ARCHES, AppEntry, discover_brand_configs, load_global_config, load_toml, parse_app_entries
from src.core.logger import abort, epr, is_interrupted, mark_interrupted, pr
from src.core.network import NetworkManager


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

    version = int(match.group(1))
    if version < min_version:
        abort(f"Java {version} found, but Java {min_version}+ is required")

def _build(target_brands: list[str] | None = None, target_apps: list[str] | None = None, arch_override: str | None = None, dpi_override: str | None = None) -> int:
    _require_java()
    main_cfg = load_global_config(CONFIG_PATH)
    if CONFIG_PATH.is_file():
        pr(f"Loaded global config '{CONFIG_PATH}'")

    brand_configs = discover_brand_configs()
    if not brand_configs:
        abort(f"No brand configs found in '{CONFIGS_DIR}'")

    if target_brands is not None:
        unique_brands = list(dict.fromkeys(b.lower() for b in target_brands))
        if missing_brands := [b for b in unique_brands if b not in brand_configs]:
            label = ", ".join(f"'{b}'" for b in missing_brands)
            abort(f"Brand {label} not found in '{CONFIGS_DIR}'" if len(missing_brands) == 1 else f"Brands {label} not found in '{CONFIGS_DIR}'")
        selected_brands = {b: brand_configs[b] for b in unique_brands}
    else:
        selected_brands = brand_configs

    entries_by_brand: dict[str, list[AppEntry]] = {}
    for brand_key, cfg_path in selected_brands.items():
        data = load_toml(cfg_path)
        pr(f"Loaded config '{cfg_path}'")
        entries_by_brand[brand_key] = [e for e in parse_app_entries(data, main_cfg, brand=cfg_path.parent.name) if e.enabled]

    entries: list[AppEntry] = [e for brand_entries in entries_by_brand.values() for e in brand_entries]
    if target_apps is not None:
        unique_targets = list(dict.fromkeys(target_apps))
        by_table: dict[str, list[tuple[str, AppEntry]]] = {}
        for brand_key, brand_entries in entries_by_brand.items():
            for e in brand_entries:
                by_table.setdefault(e.table, []).append((brand_key, e))

        if missing := [t for t in unique_targets if t not in by_table]:
            label = ", ".join(f"'{t}'" for t in missing)
            abort(f"App {label} not found in config" if len(missing) == 1 else f"Apps {label} not found in config")

        selected: list[AppEntry] = []
        for t in unique_targets:
            matches = by_table[t]
            if len(matches) > 1:
                brands_str = ", ".join(b for b, _ in matches)
                abort(f"App '{t}' exists in multiple brands ({brands_str}); specify --brand")
            selected.append(matches[0][1])
        entries = selected

    if arch_override is not None:
        entries = [replace(e, arch=arch_override) for e in entries]

    if dpi_override is not None:
        entries = [replace(e, dpi=dpi_override) for e in entries]

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for cl in TEMP_DIR.glob("*/changelog.md"):
        cl.write_text("", encoding="utf-8")

    Path("build.md").write_text("", encoding="utf-8")
    with NetworkManager() as net:
        success = run_build(entries, main_cfg, net)
    return 0 if success else 1

def _clear() -> int:
    cleaned = False
    for directory in (TEMP_DIR, BUILD_DIR):
        if directory.exists():
            shutil.rmtree(directory)
            cleaned = True

    if (build_md := Path("build.md")).exists():
        build_md.unlink()
        cleaned = True

    pr("Cleaned successfully" if cleaned else "Already clean")
    return 0

def _sigint_handler(_sig: int, _frame: object) -> None:
    if is_interrupted():
        return

    mark_interrupted()
    epr("Interrupted by user")
    for tmp in TEMP_DIR.rglob("tmp*"):
        shutil.rmtree(tmp, ignore_errors=True)
    for ks in TEMP_DIR.glob("*.keystore"):
        ks.unlink(missing_ok=True)
    os._exit(130)

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Build and patch Android APKs configured in configs/<brand>/config.toml.",
    )
    parser.add_argument(
        "--brand",
        nargs="+",
        action="extend",
        metavar="BRAND",
        help="Brand folder name(s) in configs/ to build",
    )
    parser.add_argument(
        "--target",
        nargs="+",
        action="extend",
        metavar="APP",
        help="TOML table name(s) of specific app(s) to build",
    )
    parser.add_argument(
        "--arch",
        choices=sorted(VALID_ARCHES),
        help="Override target architecture",
    )
    parser.add_argument(
        "--dpi",
        help="Override target screen DPI (e.g. nodpi, 480dpi, all, or comma-separated list)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Remove build/, temp/, and build.md instead of building",
    )
    args = parser.parse_args(argv)
    if args.clear and any(v is not None for v in (args.brand, args.target, args.arch, args.dpi)):
        parser.error("--clear cannot be used together with --brand, --target, --arch, or --dpi")
    return args

def main() -> None:
    signal.signal(signal.SIGINT, _sigint_handler)
    args = _parse_args()
    if args.clear:
        sys.exit(_clear())

    _load_dotenv()
    sys.exit(_build(target_brands=args.brand, target_apps=args.target, arch_override=args.arch, dpi_override=args.dpi))

if __name__ == "__main__":
    main()
