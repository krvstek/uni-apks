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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

from src.core.network import NetworkManager


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")

class ScraperError(Exception):
    """Raised for scraper-layer failures: DOM parsing, regex mismatches, missing assets"""

@dataclass(slots=True, frozen=True)
class AppMetadata:
    pkg_name: str
    versions: list[str]

@dataclass(slots=True, frozen=True)
class DownloadResult:
    path: Path
    is_bundle: bool = False

class BaseScraper(ABC):
    def __init__(self, net: NetworkManager) -> None:
        self.net = net
        self._cache: dict[str, AppMetadata] = {}

    def cached_metadata(self, url: str) -> AppMetadata:
        if url not in self._cache:
            self._cache[url] = self.fetch_metadata(url)
        return self._cache[url]

    @abstractmethod
    def fetch_metadata(self, url: str) -> AppMetadata:
        pass

    @abstractmethod
    def download(self, url: str, version: str, dest: Path, arch: str, dpi: str, version_code: str | None = None) -> DownloadResult:
        pass