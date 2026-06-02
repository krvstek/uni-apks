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
    patches_version: str
    cli_version: str
    patches_source: str
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
    included_patches: list[str]
    excluded_patches: list[str]
    exclusive_patches: bool
    patches_source: str
    cli_source: str
    patches_version: str
    cli_version: str
    skip_sigcheck: bool
    enabled: bool

    @property
    def dl_from(self) -> str | None:
        return next(iter(self.dl_urls), None)

def load_toml(path: Path) -> dict[str, object]:
    with path.open("rb") as fp:
        return tomllib.load(fp)

def _parse_bool(value: object, field: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"'{field}' must be a boolean (true/false without quotes), got {type(value).__name__}")

def parse_config(data: dict[str, object]) -> Config:
    return Config(
        parallel_jobs=int(data.get("parallel-jobs", os.cpu_count() or 1)),
        brand=str(data.get("brand", "Morphe")),
        patches_version=str(data.get("patches-version", "latest")),
        cli_version=str(data.get("cli-version", "latest")),
        patches_source=str(data.get("patches-source", "github:MorpheApp/morphe-patches")),
        cli_source=str(data.get("cli-source", "github:MorpheApp/morphe-cli")),
        strict_sigcheck=_parse_bool(data.get("strict-sigcheck", True), "strict-sigcheck"),
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

        inc_raw = str(t.get("included-patches", ""))
        exc_raw = str(t.get("excluded-patches", ""))
        for name, raw in (("included-patches", inc_raw), ("excluded-patches", exc_raw)):
            if raw and "'" not in raw:
                raise ValueError(f"Patch names inside {name} for '{table_name}' must be quoted")

        entries.append(AppEntry(
            table=table_name,
            app_name=str(t.get("app-name", table_name)),
            brand=str(t.get("brand", main.brand)),
            arch=arch,
            dpi=str(t.get("dpi", "")),
            version=str(t.get("version", "auto")),
            dl_urls=dl_urls,
            patcher_args=shlex.split(str(t.get("patcher-args", ""))),
            included_patches=shlex.split(inc_raw),
            excluded_patches=shlex.split(exc_raw),
            exclusive_patches=_parse_bool(t.get("exclusive-patches", False), "exclusive-patches"),
            patches_source=str(t.get("patches-source", main.patches_source)),
            cli_source=str(t.get("cli-source", main.cli_source)),
            patches_version=str(t.get("patches-version", main.patches_version)),
            cli_version=str(t.get("cli-version", main.cli_version)),
            skip_sigcheck=_parse_bool(t.get("skip-sigcheck", False), "skip-sigcheck"),
            enabled=_parse_bool(t.get("enabled", True), "enabled"),
        ))
    return entries