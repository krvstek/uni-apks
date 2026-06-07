import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.core.network import NetworkManager, ResourceNotFoundError
from src.scrapers.base import AppMetadata, BaseScraper, DownloadResult, ScraperError


def _parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")

class APKMirrorError(ScraperError):
    pass

class APKMirrorScraper(BaseScraper):
    def __init__(self, net: NetworkManager) -> None:
        super().__init__(net)
        self._resp_html: str = ""
        self._category: str = ""
        self._release_urls: dict[str, str] = {}

    def fetch_metadata(self, url: str) -> AppMetadata:
        self._resp_html = self.net.get(url)
        self._category = url.rstrip("/").split("/")[-1]
        m = re.search(r"play\.google\.com/store/apps/details\?id=([\w.]+)", self._resp_html)
        if not m:
            raise APKMirrorError("Package name not found")

        soup = _parse_html(self.net.get(f"https://www.apkmirror.com/uploads/?appcategory={self._category}"))
        versions: list[str] = []
        for a in soup.select("#primary a.fontBlack[href*='-release/']"):
            text = a.get_text(strip=True)
            if "beta" in text.lower() or "alpha" in text.lower():
                continue
            v = text.split()[-1]
            self._release_urls[v] = urljoin("https://www.apkmirror.com", a["href"])
            versions.append(v)

        return AppMetadata(pkg_name=m.group(1), versions=versions)

    def download(self, url: str, version: str, dest: Path, arch: str, dpi: str) -> DownloadResult:
        release_url = self._release_urls.get(version)
        if release_url is None:
            search_html = self.net.get(f"{url.rstrip('/')}/?s={version}")
            soup = _parse_html(search_html)
            for a in soup.select("a.fontBlack[href*='-release/']"):
                if version in a.get_text() and f"/{self._category}/" in a.get("href", ""):
                    release_url = urljoin("https://www.apkmirror.com", a["href"])
                    break

        if release_url is None:
            raise APKMirrorError("Version not found")

        try:
            release_html = self.net.get(release_url)
        except ResourceNotFoundError:
            raise APKMirrorError("Version not found") from None

        is_bundle = False
        soup_release = _parse_html(release_html)
        if soup_release.select_one("div.table-row.headerFont:last-child"):
            dl_url = self._pick_variant(soup_release, dpi, arch)
            if dl_url is None:
                raise APKMirrorError("No matching variant found")
            release_html = self.net.get(dl_url[0])
            is_bundle = dl_url[1] == "BUNDLE"

        soup_dl = _parse_html(release_html)
        btn = soup_dl.select_one("a.btn")
        btn_url = urljoin("https://www.apkmirror.com", btn["href"])
        soup_final = _parse_html(self.net.get(btn_url))
        dl_link = soup_final.select_one("span > a[rel=nofollow]")
        final_url = urljoin("https://www.apkmirror.com", dl_link["href"])
        out_path = dest.with_suffix(".apkm") if is_bundle else dest
        self.net.download(final_url, out_path)
        return DownloadResult(path=out_path, is_bundle=is_bundle)

    def _pick_variant(self, soup, dpi: str, arch: str) -> tuple[str, str] | None:
        rows = soup.select("div.table-row.headerFont")
        for bt in ("APK", "BUNDLE"):
            url_found = self._search(rows, dpi, arch, bt)
            if url_found:
                return url_found, bt
        return None

    def _search(self, rows: list, dpi: str, arch: str, bundle_type: str) -> str:
        apparch = {"universal", "noarch", "arm64-v8a + armeabi-v7a", "arm64-v8a + armeabi"}
        if arch != "all":
            apparch.add(arch)

        for row in reversed(rows):
            link = row.select_one("div.table-cell:first-child > a")
            if not link or not link.get("href"):
                continue

            cells = row.select("div.table-cell")
            if len(cells) < 4:
                continue

            badge = cells[0].select_one(".apkm-badge")
            b_type = badge.get_text(strip=True).upper() if badge else "APK"
            arch_text = cells[1].get_text(strip=True)
            dpi_text = cells[3].get_text(strip=True)
            dpi_ok = not dpi_text or re.match(r"\d+-640dpi", dpi_text) or dpi_text in {"nodpi", "anydpi"} or (dpi and dpi_text == dpi)
            if b_type == bundle_type and arch_text in apparch and dpi_ok:
                return urljoin("https://www.apkmirror.com", str(link["href"]))

        return ""