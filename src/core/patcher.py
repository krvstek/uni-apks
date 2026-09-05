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

import contextlib
import os
import re
import subprocess
from pathlib import Path

from src.core.config import PatchSpec
from src.core.logger import pr, wpr
from src.core.prebuilts import get_highest_ver

_SECRET_PATTERNS = re.compile(r"(keystore-password=|keystore-entry-password=)\S+")


class PatcherError(Exception):
    pass

class SignatureError(PatcherError):
    """Raised when sig.txt has no entry for a package, or apksigner reports a hash mismatch."""

def _run_java(*args: str | Path, capture: bool = True, timeout: int = 600) -> str:
    result = subprocess.run(["java", *(str(a) for a in args)], capture_output=capture, text=True, timeout=timeout)
    combined = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        redacted = _SECRET_PATTERNS.sub(r"\1***", combined)
        raise PatcherError(redacted.strip())
    return combined

def _parse_patch_block(output: str, patch_name: str, pkg_name: str) -> list[str]:
    pattern = rf"Name:\s*{re.escape(patch_name)}\n.*?Package name:\s*{re.escape(pkg_name)}\s*\n\s*Compatible versions:\s*\n(.*?)(?:\n\s*Package name:|\n\s*Version codes:|\n\n|\Z)"
    if m := re.search(pattern, output, re.DOTALL | re.IGNORECASE):
        return [v.strip() for v in m.group(1).splitlines() if v.strip()]
    return []

def _parse_versions_output(output: str) -> list[str]:
    marker = "Most common compatible versions:\n"
    if marker not in output:
        return []

    block = output.split(marker)[1].split("\n\n")[0]
    versions: list[str] = []
    for line in block.splitlines():
        parts = line.split()
        if parts:
            versions.append(parts[0])
    return versions

def _extract_version_code(output: str, version: str, arch: str) -> str | None:
    arch_map = {
        "arm64-v8a": "ARM64_V8A", "armeabi-v7a": "ARMEABI_V7A", 
        "x86": "X86", "x86_64": "X86_64"
    }
    target_arch = arch_map.get(arch.lower(), "ARM64_V8A")
    if m := re.search(rf"{re.escape(version)}.*?{target_arch}=(\d+)", output, re.IGNORECASE):
        return m.group(1)
    return None

def _redact_args(args: list[str | Path]) -> list[str]:
    return [_SECRET_PATTERNS.sub(r"\1***", str(a)) for a in args]

class PatcherCLI:
    def __init__(self, cli_jar: Path, mpp_map: dict[tuple[str, str], Path], apksigner: Path, ks_path: Path | None = None, sig_file: Path = Path("sig.txt")) -> None:
        self.cli_jar = cli_jar
        self.mpp_map = mpp_map
        self.apksigner = apksigner
        self.ks_path = ks_path
        self._signatures: dict[str, str] = {}
        if sig_file.exists():
            for line in sig_file.read_text(encoding="utf-8").splitlines():
                if parts := line.split():
                    self._signatures[parts[-1]] = parts[0].lower()

    def has_signature(self, pkg_name: str) -> bool:
        expected = self._signatures.get(pkg_name)
        return bool(expected)

    def list_patches(self, pkg_name: str, experimental: bool = False) -> str:
        extra = ["-x"] if experimental else []
        return "".join(_run_java("-jar", self.cli_jar, "list-patches", "--patches", mpp, "-f", pkg_name, "-v", "-p", *extra, timeout=60) for mpp in self.mpp_map.values())

    def list_versions(self, pkg_name: str, experimental: bool = False) -> str:
        extra = ["-x"] if experimental else []
        parts: list[str] = []
        for mpp in self.mpp_map.values():
            with contextlib.suppress(PatcherError):
                parts.append(_run_java("-jar", self.cli_jar, "list-versions", "--patches", mpp, "-f", pkg_name, *extra, timeout=60))
        return "\n".join(parts)

    def get_last_supported_version(self, list_patches_output: str, pkg_name: str, patches: dict[str, PatchSpec], arch: str = "arm64-v8a", experimental: bool = False) -> tuple[str, str | None] | None:
        all_included = [p for spec in patches.values() for p in spec["include"]]
        all_vers: list[str] = []
        for p in all_included:
            all_vers.extend(_parse_patch_block(list_patches_output, p, pkg_name))
        if all_vers:
            highest = get_highest_ver(all_vers)
            return (highest, _extract_version_code(list_patches_output, highest, arch)) if highest else None

        versions_output = self.list_versions(pkg_name, experimental)
        if "Any" in versions_output:
            return None

        if not (versions := _parse_versions_output(versions_output)):
            raise PatcherError(f"No patches found for '{pkg_name}'")
        highest = get_highest_ver(versions)
        return (highest, _extract_version_code(versions_output, highest, arch)) if highest else None

    def resolve_auto_patches(self, list_patches_output: str) -> tuple[str, str]:
        microg_patch = psu_patch = ""
        for line in list_patches_output.splitlines():
            line_lower = line.lower()
            if not line_lower.startswith("name:"):
                continue

            patch_name = line[5:].strip()
            name_lower = patch_name.lower()
            if "gmscore" in name_lower or "microg" in name_lower:
                microg_patch = patch_name
            elif "disable play store updates" in name_lower:
                psu_patch = patch_name
        return microg_patch, psu_patch

    def build_patch_args(self, patches: dict[str, PatchSpec], extra_args: list[str], arch: str, auto_patches: tuple[str, str], exclusive: bool = False, force: bool = False) -> list[str]:
        active_auto = {p for p in auto_patches if p}
        p_args: list[str] = ["-f"] if force else []
        for src, spec in patches.items():
            p_args.extend(("--patches", str(self.mpp_map[(src, spec["version"])])))
            for p in spec["include"]:
                if p in active_auto:
                    wpr(f"You can't include '{p}' patch as that's done by builder automatically")
                else:
                    p_args.extend(("-e", p))
            for p in spec["exclude"]:
                p_args.extend(("-d", p))
        if exclusive:
            p_args.append("--exclusive")

        p_args.extend(extra_args)
        for auto_p in active_auto:
            p_args.extend(("-e", auto_p))
        p_args.extend(("--striplibs", "arm64-v8a,armeabi-v7a" if arch == "all" else arch))
        return p_args

    def patch(self, stock_apk: Path, output_apk: Path, patch_args: list[str]) -> None:
        base_cmd = ["-jar", self.cli_jar, "patch", stock_apk, "-o", output_apk]
        ks_args: list[str] = []
        if self.ks_path and (ks_pass := os.getenv("KEYSTORE_PASS")) and (ks_alias := os.getenv("KEYSTORE_ALIAS")):
            ks_args = [f"--keystore={self.ks_path}", f"--keystore-entry-password={ks_pass}", f"--keystore-password={ks_pass}", f"--signer={ks_alias}", f"--keystore-entry-alias={ks_alias}"]
        elif Path("morphe.keystore").exists():
            ks_args = ["--keystore=morphe.keystore"]

        pr(" ".join(_redact_args(["java", *base_cmd, *ks_args, *patch_args])))
        try:
            _run_java(*base_cmd, *ks_args, *patch_args, capture=False)
        except subprocess.TimeoutExpired:
            output_apk.unlink(missing_ok=True)
            raise PatcherError(f"Patching '{stock_apk.name}' failed, process timed out after 10 minutes") from None
        except PatcherError as exc:
            output_apk.unlink(missing_ok=True)
            raise PatcherError(f"Patching '{stock_apk.name}' failed:\n{exc}") from exc

    def check_signature(self, apk: Path, pkg_name: str) -> bool:
        expected = self._signatures.get(pkg_name)
        if not expected:
            return True

        try:
            output = _run_java("--enable-native-access=ALL-UNNAMED", "-jar", self.apksigner, "verify", "--print-certs", apk)
            return expected.lower() in output.lower()
        except PatcherError:
            return False