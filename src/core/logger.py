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

import os
import sys
from typing import Never

IS_GITHUB = os.getenv("GITHUB_ACTIONS") == "true"
_interrupted = False


def is_interrupted() -> bool:
    return _interrupted

def mark_interrupted() -> None:
    global _interrupted
    _interrupted = True

def _log(color: str, symbol: str, msg: str, gh_level: str | None = None) -> None:
    if IS_GITHUB and gh_level:
        print(f"::{gh_level}::{msg}", file=sys.stderr)
    else:
        print(f"\033[0;{color}m[{symbol}] {msg}\033[0m", file=sys.stderr)

def pr(msg: str) -> None:
    _log("32", "+", msg)

def epr(msg: str) -> None:
    _log("31", "-", msg, "error")

def wpr(msg: str) -> None:
    _log("33", "!", msg, "warning")

def abort(msg: str) -> Never:
    epr(f"ABORT: {msg}")
    sys.exit(1)