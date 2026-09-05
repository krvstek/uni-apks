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
import random
import threading
import time
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from curl_cffi import requests
from curl_cffi.requests import Response
from curl_cffi.requests import exceptions as req_exc

from src.core.logger import epr

_RETRY_DELAYS = (2, 4)
_MAX_ATTEMPTS = len(_RETRY_DELAYS) + 1
_SOLVER_URL = os.getenv("CF_SOLVER_URL", "http://localhost:8000")


class NetworkError(Exception):
    pass

class ResourceNotFoundError(NetworkError):
    """Raised when a remote resource returns HTTP 404."""

def _get_lock[KT](locks: dict[KT, threading.Lock], mu: threading.Lock, key: KT) -> threading.Lock:
    with mu:
        return locks.setdefault(key, threading.Lock())

def _retry_sleep(attempt: int) -> None:
    if attempt <= len(_RETRY_DELAYS):
        time.sleep(_RETRY_DELAYS[attempt - 1] + random.uniform(0, 1))

def _is_challenge(resp: Response) -> bool:
    if resp.status_code == 403:
        return True

    if resp.status_code == 503:
        body = (resp.text or "").lower()
        return "just a moment" in body or "turnstile" in body or "cf-mitigated" in resp.headers
    return False

def _handle_status(resp: Response, url: str, attempt: int) -> bool:
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
        self.session = requests.Session(impersonate="chrome150")
        token = os.getenv("GITHUB_TOKEN")
        self._gh_headers: dict[str, str] = {"Authorization": f"token {token}"} if token else {}
        self._domain_locks: dict[str, threading.Lock] = {}
        self._domain_mu = threading.Lock()
        self._dest_locks: dict[Path, threading.Lock] = {}
        self._dest_mu = threading.Lock()

    def _reset_session(self) -> None:
        self.session.close()
        self.session = requests.Session(impersonate="chrome150")

    @property
    def gh_headers(self) -> dict[str, str]:
        return self._gh_headers

    def _solve_challenge(self, url: str) -> bool:
        self._reset_session()
        try:
            resp = requests.get(f"{_SOLVER_URL}/cookies", params={"url": url}, timeout=60)
            if resp.status_code != 200:
                return False

            resp_any: Any = resp
            data = cast(dict[str, Any], resp_any.json())
            cookies = data.get("cookies", {})
            user_agent = data.get("user_agent")
            if isinstance(cookies, dict):
                for k, v in cast(dict[str, str], cookies).items():
                    self.session.cookies.set(k, v)
            elif isinstance(cookies, list):
                for c in cast(list[dict[str, str]], cookies):
                    if "name" in c and "value" in c:
                        self.session.cookies.set(c["name"], c["value"])

            if user_agent:
                self.session.headers["User-Agent"] = user_agent
            return True
        except (req_exc.RequestException, Exception) as exc:
            epr(f"Challenge solver error for {url}: {exc}")
            return False

    def get(self, url: str, headers: dict[str, str] | None = None) -> str:
        netloc = urlparse(url).netloc
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                with _get_lock(self._domain_locks, self._domain_mu, netloc):
                    time.sleep(0.5)
                    resp = self.session.get(url, timeout=(5, 10), allow_redirects=True, headers=headers, verify=True)

                if _is_challenge(resp):
                    epr(f"JS challenge detected for {url}, attempting solver bypass ({attempt}/{_MAX_ATTEMPTS})")
                    self._solve_challenge(url)
                    _retry_sleep(attempt)
                    continue

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

                    if _is_challenge(resp):
                        epr(f"JS challenge detected for {url}, attempting solver bypass ({attempt}/{_MAX_ATTEMPTS})")
                        self._solve_challenge(url)
                        _retry_sleep(attempt)
                        continue

                    if _handle_status(resp, url, attempt):
                        _retry_sleep(attempt)
                        continue

                    with tmp.open("wb") as fh:
                        resp_any: Any = resp
                        for chunk in cast(list[bytes], resp_any.iter_content(chunk_size=1048576)):
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