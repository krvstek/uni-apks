import os
import re
import shutil
import subprocess
from pathlib import Path

from src.core.logger import pr, wpr
from src.core.prebuilts import get_highest_ver

_SECRET_PATTERNS = re.compile(r"(keystore-password=|keystore-entry-password=)\S+")


class PatcherError(Exception):
    pass

class SignatureError(PatcherError):
    """Raised when sig.txt has no entry for a package, or apksigner reports a hash mismatch."""

def _arch_to_libs(arch: str) -> str:
    match arch:
        case "armeabi-v7a" | "arm64-v8a" | "x86" | "x86_64":
            return arch
        case _:
            return "arm64-v8a,armeabi-v7a"

def _run_java(*args: str | Path, capture: bool = True, timeout: int = 600) -> str:
    result = subprocess.run(["java", *(str(a) for a in args)], capture_output=capture, text=True, timeout=timeout)
    combined = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        redacted = _SECRET_PATTERNS.sub(r"\1***", combined)
        raise PatcherError(redacted.strip())
    return combined

def _parse_patch_block(output: str, patch_name: str) -> list[str]:
    if m := re.search(rf"Name:\s*{re.escape(patch_name)}\n.*?Compatible versions:\s*\n(.*?)(?:\n\n|\Z)", output, re.DOTALL | re.IGNORECASE):
        return [v.strip() for v in m.group(1).splitlines() if v.strip()]
    return []

def _parse_versions_output(output: str) -> list[str]:
    marker = "Most common compatible versions:\n"
    if marker not in output:
        return []

    block = output.split(marker)[1].split("\n\n")[0]
    versions = []
    for line in block.splitlines():
        clean_ver = line.split("(")[0].strip()
        if clean_ver:
            versions.append(clean_ver)

    return versions

def _redact_args(args: list[str | Path]) -> list[str]:
    return [_SECRET_PATTERNS.sub(r"\1***", str(a)) for a in args]

class PatcherCLI:
    def __init__(self, cli_jar: Path, patches_mpp: Path, apksigner: Path, ks_path: Path | None = None, sig_file: Path = Path("sig.txt")) -> None:
        self.cli_jar = cli_jar
        self.patches_mpp = patches_mpp
        self.apksigner = apksigner
        self.ks_path = ks_path
        self._signatures: dict[str, str] = {}
        if sig_file.exists():
            for line in sig_file.read_text(encoding="utf-8").splitlines():
                if parts := line.split():
                    self._signatures[parts[-1]] = parts[0].lower()

    def has_signature(self, pkg_name: str) -> bool:
        expected = self._signatures.get(pkg_name)
        return bool(expected and expected.strip())

    def list_patches(self, pkg_name: str) -> str:
        return _run_java("-jar", self.cli_jar, "list-patches", "--patches", self.patches_mpp, "-f", pkg_name, "-v", "-p", timeout=60)

    def list_versions(self, pkg_name: str) -> str:
        return _run_java("-jar", self.cli_jar, "list-versions", "--patches", self.patches_mpp, "-f", pkg_name, timeout=60)

    def get_last_supported_version(self, list_patches_output: str, pkg_name: str, included_patches: list[str]) -> str | None:
        if included_patches and (all_vers := [v for p in included_patches for v in _parse_patch_block(list_patches_output, p)]):
            return get_highest_ver(all_vers)

        versions_output = self.list_versions(pkg_name)
        if "Any" in versions_output:
            return None

        if not (versions := _parse_versions_output(versions_output)):
            raise PatcherError(f"No patches found for '{pkg_name}' in patches '{self.patches_mpp}'")
        return get_highest_ver(versions)

    def resolve_auto_patches(self, list_patches_output: str) -> tuple[str, str]:
        microg_patch = ""
        psu_patch = ""
        for line in list_patches_output.splitlines():
            if not line.lower().startswith("name:"):
                continue

            patch_name = line[5:].strip()
            name_lower = patch_name.lower()
            if "gmscore" in name_lower or "microg" in name_lower:
                microg_patch = patch_name
            elif "disable play store updates" in name_lower:
                psu_patch = patch_name

        return microg_patch, psu_patch

    def build_patch_args(self, included_patches: list[str], excluded_patches: list[str], exclusive: bool, extra_args: list[str], arch: str, auto_patches: list[str], force: bool = False) -> list[str]:
        active_auto = {p for p in auto_patches if p}
        p_args: list[str] = ["-f"] if force else []
        for patch_list, flag, action in ((excluded_patches, "-d", "exclude"), (included_patches, "-e", "include")):
            for p in patch_list:
                if p in active_auto:
                    wpr(f"You can't {action} '{p}' patch as that's done by builder automatically")
                else:
                    p_args.extend((flag, p))

        if exclusive:
            p_args.append("--exclusive")

        p_args.extend(extra_args)
        for auto_p in active_auto:
            p_args.extend(("-e", auto_p))
        p_args.extend(("--striplibs", _arch_to_libs(arch)))
        return p_args

    def patch(self, stock_apk: Path, output_apk: Path, patch_args: list[str]) -> None:
        tmp_files_dir = output_apk.parent / f"tmp-{output_apk.stem}"
        base_cmd = ["-jar", self.cli_jar, "patch", stock_apk, "--purge", "-o", output_apk, "-p", self.patches_mpp, "-t", tmp_files_dir]
        ks_args: list[str] = []
        if self.ks_path and (ks_pass := os.getenv("KEYSTORE_PASS", "")) and (ks_alias := os.getenv("KEYSTORE_ALIAS", "")):
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
        finally:
            shutil.rmtree(tmp_files_dir, ignore_errors=True)

    def check_signature(self, apk: Path, pkg_name: str) -> bool:
        expected = self._signatures.get(pkg_name)
        if not expected:
            return True

        try:
            output = _run_java("--enable-native-access=ALL-UNNAMED", "-jar", self.apksigner, "verify", "--print-certs", apk)
            return expected.lower() in output.lower()
        except PatcherError:
            return False