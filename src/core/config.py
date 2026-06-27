import os
import shlex
import tomllib
from dataclasses import dataclass
from pathlib import Path

TEMP_DIR: Path = Path("temp")
BUILD_DIR: Path = Path("build")
CONFIG_PATH: Path = Path("config.toml")
SOURCES: tuple[str, ...] = ("github", "apkmirror", "uptodown")
VALID_ARCHES: frozenset[str] = frozenset({"both", "all", "arm64-v8a", "armeabi-v7a", "x86_64", "x86"})


@dataclass(slots=True, frozen=True)
class Config:
    parallel_jobs: int
    cli_version: str
    cli_source: str
    brand: str
    strict_sigcheck: bool

@dataclass(slots=True, frozen=True)
class AppEntry:
    table: str
    app_name: str
    brand: str
    arch: str
    dpi: str
    version: str
    dl_urls: dict[str, str]
    patcher_args: list[str]
    patches: dict[str, dict]
    exclusive_patches: bool
    cli_source: str
    cli_version: str
    skip_sigcheck: bool
    enabled: bool
    changelog_keywords: list[str]

def load_toml(path: Path) -> dict[str, object]:
    with path.open("rb") as fp:
        return tomllib.load(fp)

def _parse_bool(d: dict[str, object], key: str, default: bool) -> bool:
    value = d.get(key, default)
    if isinstance(value, bool):
        return value

    raise ValueError(f"'{key}' must be a boolean (true/false without quotes), got {type(value).__name__}")

def parse_config(data: dict[str, object]) -> Config:
    return Config(
        parallel_jobs=int(data.get("parallel-jobs", os.process_cpu_count() or 1)),
        brand=str(data.get("brand", "Morphe")),
        cli_version=str(data.get("cli-version", "latest")),
        cli_source=str(data.get("cli-source", "github:MorpheApp/morphe-cli")),
        strict_sigcheck=_parse_bool(data, "strict-sigcheck", True),
    )

def parse_app_entries(data: dict[str, object], main: Config) -> list[AppEntry]:
    entries: list[AppEntry] = []
    for table_name, t in data.items():
        if not isinstance(t, dict):
            continue

        if (arch := str(t.get("arch", "all"))) not in VALID_ARCHES:
            raise ValueError(f"Wrong arch '{arch}' for '{table_name}'")

        dl_urls: dict[str, str] = {}
        for src in SOURCES:
            url = t.get(f"{src}-dlurl")
            if isinstance(url, str):
                dl_urls[src] = url.rstrip("/").removesuffix("download").rstrip("/")

        raw_patches = t.get("patches", {})
        if not isinstance(raw_patches, dict):
            raise ValueError(f"'patches' for '{table_name}' must be a TOML table")

        patches: dict[str, dict] = {}
        for k, v in raw_patches.items():
            if isinstance(v, list):
                patches[str(k)] = {"version": "latest", "include": [str(p) for p in v], "exclude": []}
            elif isinstance(v, dict):
                patches[str(k)] = {"version": str(v.get("version", "latest")), "include": [str(p) for p in v.get("include", [])], "exclude": [str(p) for p in v.get("exclude", [])]}

        raw_keywords = t.get("changelog-keywords")
        if raw_keywords is not None and not isinstance(raw_keywords, list):
            raise ValueError(f"'changelog-keywords' must be a list for '{table_name}'")

        keywords: list[str] = []
        for k in (raw_keywords or []):
            s = str(k).strip()
            if s:
                keywords.append(s.lower())

        entries.append(AppEntry(
            table=table_name,
            app_name=str(t.get("app-name", table_name.replace("-", " "))),
            brand=str(t.get("brand", main.brand)),
            arch=arch,
            dpi=str(t.get("dpi", "")),
            version=str(t.get("version", "auto")),
            dl_urls=dl_urls,
            patcher_args=shlex.split(str(t.get("patcher-args", ""))),
            patches=patches,
            exclusive_patches=_parse_bool(t, "exclusive-patches", False),
            cli_source=str(t.get("cli-source", main.cli_source)),
            cli_version=str(t.get("cli-version", main.cli_version)),
            skip_sigcheck=_parse_bool(t, "skip-sigcheck", False),
            enabled=_parse_bool(t, "enabled", True),
            changelog_keywords=keywords,
        ))
    return entries