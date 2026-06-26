import os
import random
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from curl_cffi import requests
from curl_cffi.requests import exceptions as req_exc

from src.core.logger import epr

_RETRY_DELAYS = (2, 4)
_MAX_ATTEMPTS = len(_RETRY_DELAYS) + 1


class NetworkError(Exception):
    pass

class ResourceNotFoundError(NetworkError):
    """Raised when a remote resource returns HTTP 404."""

def _get_lock(locks: dict, mu: threading.Lock, key) -> threading.Lock:
    with mu:
        return locks.setdefault(key, threading.Lock())

def _retry_sleep(attempt: int) -> None:
    if attempt <= len(_RETRY_DELAYS):
        time.sleep(_RETRY_DELAYS[attempt - 1] + random.uniform(0, 1))

def _handle_status(resp, url: str, attempt: int) -> bool:
    if resp.status_code == 404:
        raise ResourceNotFoundError(f"Not found (404): {url}")

    if resp.status_code == 403 or resp.status_code >= 500:
        epr(f"HTTP {resp.status_code} for {url}, attempt {attempt}/{_MAX_ATTEMPTS}")
        return True

    if resp.status_code >= 400:
        resp.raise_for_status()
    return False

class NetworkManager:
    def __init__(self) -> None:
        self.session = requests.Session(impersonate="chrome146")
        token = os.getenv("GITHUB_TOKEN")
        self._gh_headers: dict[str, str] = {"Authorization": f"token {token}"} if token else {}
        self._domain_locks: dict[str, threading.Lock] = {}
        self._domain_mu = threading.Lock()
        self._dest_locks: dict[Path, threading.Lock] = {}
        self._dest_mu = threading.Lock()

    def get(self, url: str, headers: dict[str, str] | None = None) -> str:
        netloc = urlparse(url).netloc
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                with _get_lock(self._domain_locks, self._domain_mu, netloc):
                    time.sleep(0.5)
                    resp = self.session.get(url, timeout=(5, 10), allow_redirects=True, headers=headers, verify=True)

                if _handle_status(resp, url, attempt):
                    _retry_sleep(attempt)
                    continue

                return resp.text
            except req_exc.RequestException as exc:
                last_exc = exc
                epr(f"Request error for {url}, attempt {attempt}/{_MAX_ATTEMPTS}: {exc}")
                _retry_sleep(attempt)
        raise NetworkError(f"Request failed after {_MAX_ATTEMPTS} attempts: {url}") from last_exc

    def download(self, url: str, dest: Path, headers: dict[str, str] | None = None) -> None:
        if dest.exists():
            return

        with _get_lock(self._dest_locks, self._dest_mu, dest):
            if dest.exists():
                return

            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(f"tmp.{dest.name}")
            tmp.unlink(missing_ok=True)
            netloc = urlparse(url).netloc
            last_exc: Exception | None = None
            for attempt in range(1, _MAX_ATTEMPTS + 1):
                try:
                    with _get_lock(self._domain_locks, self._domain_mu, netloc):
                        time.sleep(0.5)
                        resp = self.session.get(url, timeout=(5, 300), stream=True, allow_redirects=True, headers=headers, verify=True)

                    if _handle_status(resp, url, attempt):
                        _retry_sleep(attempt)
                        continue

                    with tmp.open("wb") as fh:
                        for chunk in resp.iter_content(chunk_size=1048576):
                            fh.write(chunk)
                    tmp.replace(dest)
                    return
                except req_exc.RequestException as exc:
                    tmp.unlink(missing_ok=True)
                    last_exc = exc
                    epr(f"Download error for {url}, attempt {attempt}/{_MAX_ATTEMPTS}: {exc}")
                    _retry_sleep(attempt)
            raise NetworkError(f"Download failed after {_MAX_ATTEMPTS} attempts: {url}") from last_exc

    def __enter__(self) -> "NetworkManager":
        return self

    def __exit__(self, *_: object) -> None:
        self.session.close()