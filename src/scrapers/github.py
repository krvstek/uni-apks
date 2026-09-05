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

import json
import re
from pathlib import Path
from typing import Any

from src.core.network import NetworkManager, ResourceNotFoundError
from src.scrapers.base import AppMetadata, BaseScraper, DownloadResult, ScraperError

_ARCH_SUFFIX = re.compile(r"(?:-(all|arm64-v8a|armeabi-v7a|x86_64|x86))?(?:\.apk\.apkm|\.apk|\.apkm)$", re.I)
_GH_URL = re.compile(r"github\.com/([^/]+)/([^/]+)/releases/tag/([^/]+)")


class GitHubReleasesError(ScraperError):
    pass

class GitHubScraper(BaseScraper):
    def __init__(self, net: NetworkManager) -> None:
        super().__init__(net)
        self._assets: list[dict[str, Any]] = []

    def fetch_metadata(self, url: str) -> AppMetadata:
        m = _GH_URL.search(url)
        if not m:
            raise GitHubReleasesError(f"Invalid GitHub release URL: {url}")

        owner, repo, tag = m.groups()
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
        try:
            release = json.loads(self.net.get(api_url, headers=self.net.gh_headers))
        except ResourceNotFoundError:
            raise GitHubReleasesError(f"Release tag '{tag}' not found in '{owner}/{repo}'") from None

        pkg_name = release.get("name") or tag
        self._assets = release.get("assets", [])
        prefix = f"{pkg_name}-"
        seen: dict[str, None] = {}
        for asset in self._assets:
            name = asset.get("name", "")
            if not name.startswith(prefix) or not name.endswith((".apk", ".apkm")):
                continue

            seen[_ARCH_SUFFIX.sub("", name.removeprefix(prefix))] = None
        return AppMetadata(pkg_name=pkg_name, versions=list(seen) or [tag])

    def download(self, url: str, version: str, dest: Path, arch: str, dpi: str, version_code: str | None = None) -> DownloadResult:
        if not self._assets:
            self.fetch_metadata(url)

        version_f = version.replace(" ", "").lstrip("v")
        apk_assets = [a for a in self._assets if a["name"].endswith((".apk", ".apkm"))]
        asset = None
        for a in apk_assets:
            name = a["name"]
            if version_f and version_f not in name:
                continue

            m = _ARCH_SUFFIX.search(name)
            file_arch = m.group(1).lower() if m and m.group(1) else "all"
            if arch in ("all", "both"):
                if file_arch != "all":
                    continue
            else:
                if file_arch not in (arch, "all"):
                    continue

            asset = a
            break

        if asset is None:
            raise GitHubReleasesError(f"No matching variant found for arch '{arch}'")

        is_bundle = asset["name"].endswith(".apkm")
        out_path = dest.with_suffix(".apkm") if is_bundle else dest
        self.net.download(asset["browser_download_url"], out_path, headers=self.net.gh_headers | {"Accept": "application/octet-stream"})
        return DownloadResult(path=out_path, is_bundle=is_bundle)