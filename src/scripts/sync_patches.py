# ---------------------------------------------------------
# Copyright (C) 2026 The uni-apks Contributors
#
# Licensed under the GNU GPLv3.
# ---------------------------------------------------------

import os
import re
import json
import shutil
import zipfile
import subprocess
import urllib.request
from pathlib import Path

SUBMODULES = [
    {
        "name": "morphe-patches",
        "path": "patches/morphe-patches",
        "repo": "MorpheApp/morphe-patches",
        "host": "github",
        "icon": "🧩"
    },
    {
        "name": "piko",
        "path": "patches/piko",
        "repo": "crimera/piko",
        "host": "github",
        "icon": "🦊"
    },
    {
        "name": "x-shim",
        "path": "patches/x-shim",
        "repo": "inotia00/x-shim",
        "host": "gitlab",
        "icon": "⚙️"
    },
    {
        "name": "rushiranpise-morphe-patches",
        "path": "patches/rushiranpise-morphe-patches",
        "repo": "rushiranpise/morphe-patches",
        "host": "github",
        "icon": "🛡️"
    },
    {
        "name": "paresh-patches",
        "path": "patches/paresh-patches",
        "repo": "Paresh-Maheshwari/paresh-patches",
        "host": "gitlab",
        "icon": "🔥"
    },
    {
        "name": "hoo-dles-morphe-patches",
        "path": "patches/hoo-dles-morphe-patches",
        "repo": "hoo-dles/morphe-patches",
        "host": "github",
        "icon": "💎"
    }
]

def log(msg: str) -> None:
    print(f"[SYNC] {msg}")

def run_cmd(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    res = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def get_default_branch(sub_path: Path) -> str:
    # Query default branch of submodule
    code, out, _ = run_cmd(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=sub_path)
    if code == 0 and out:
        return out.split("/")[-1]
    # Fallback checking common branch names
    for branch in ("main", "master", "dev"):
        code, _, _ = run_cmd(["git", "show-ref", f"refs/remotes/origin/{branch}"], cwd=sub_path)
        if code == 0:
            return branch
    return "main"

def fetch_upstream_release(repo: str, host: str, dest_dir: Path) -> Path | None:
    """Fallback: Downloads compiled .mpp/.jar file from upstream releases."""
    log(f"Falling back to download compiled release for '{repo}'...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    repo_name = repo.split("/")[1]
    try:
        if host == "github":
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp:
                rel_data = json.loads(resp.read().decode())
            assets = rel_data.get("assets", [])
            target_asset = None
            for asset in assets:
                name = asset.get("name", "")
                if name.endswith(".mpp") or name.endswith(".jar"):
                    target_asset = asset
                    break
            if target_asset:
                file_url = target_asset["browser_download_url"]
                dest_path = dest_dir / f"{repo_name}-latest.mpp"
                log(f"Downloading release asset to {dest_path.name}")
                urllib.request.urlretrieve(file_url, dest_path)
                return dest_path
        elif host == "gitlab":
            project = repo.replace("/", "%2F")
            url = f"https://gitlab.com/api/v4/projects/{project}/releases/permalink/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp:
                rel_data = json.loads(resp.read().decode())
            # Find links ending with .mpp or .jar
            assets = rel_data.get("assets", {}).get("links", [])
            for asset in assets:
                name = asset.get("name", "")
                if name.endswith(".mpp") or name.endswith(".jar"):
                    file_url = asset.get("direct_asset_url") or asset.get("url")
                    dest_path = dest_dir / f"{repo_name}-latest.mpp"
                    log(f"Downloading GitLab release asset to {dest_path.name}")
                    urllib.request.urlretrieve(file_url, dest_path)
                    return dest_path
    except Exception as exc:
        log(f"Failed to fetch release for {repo}: {exc}")
    return None

def build_submodule(sub_path: Path, dest_dir: Path) -> Path | None:
    """Attempts to build the submodule using Gradle wrapper."""
    log(f"Building submodule '{sub_path.name}' via Gradle...")
    gradlew = sub_path / "gradlew"
    if os.name == "nt":
        gradlew = sub_path / "gradlew.bat"
        
    if not gradlew.exists():
        log(f"Gradle wrapper not found in '{sub_path.name}'.")
        return None
        
    # Run gradle build
    code, out, err = run_cmd([str(gradlew), "build", "-x", "test"], cwd=sub_path)
    if code != 0:
        log(f"Gradle build failed for '{sub_path.name}': {err}")
        return None
        
    # Search for compiled jar files in build/libs/
    build_libs = sub_path / "build" / "libs"
    if not build_libs.exists():
        # Check subprojects/patches/build/libs/ (common in multi-module gradle projects)
        for p in sub_path.glob("**/build/libs"):
            if p.is_dir():
                build_libs = p
                break
                
    if build_libs.exists():
        jars = [f for f in build_libs.glob("*.jar") if not f.name.endswith("-sources.jar") and not f.name.endswith("-javadoc.jar")]
        if jars:
            # Pick the largest jar or first
            jars.sort(key=lambda f: f.stat().st_size, reverse=True)
            compiled_jar = jars[0]
            dest_path = dest_dir / f"{sub_path.name}-latest.mpp"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(compiled_jar, dest_path)
            log(f"Successfully compiled patches package: {dest_path.name}")
            return dest_path
            
    log(f"No built jar file found for '{sub_path.name}'.")
    return None

def parse_patches_from_jar(jar_path: Path) -> list[dict]:
    """Tries to extract patches metadata from patches.json inside jar."""
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith("patches.json"):
                    with zf.open(name) as fp:
                        return json.loads(fp.read().decode())
    except Exception as exc:
        log(f"Could not read patches.json from jar '{jar_path.name}': {exc}")
    return []

def parse_patches_from_sources(sub_path: Path) -> list[dict]:
    # Prioritize static patches-list.json or patches.json in the repository root
    for fname in ("patches-list.json", "patches.json", "patches-bundle.json"):
        p_file = sub_path / fname
        if p_file.exists():
            try:
                data = json.loads(p_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "patches" in data:
                    return data["patches"]
                elif isinstance(data, list):
                    return data
            except Exception as exc:
                log(f"Failed to parse static JSON '{fname}' in '{sub_path.name}': {exc}")

    """Regex fallback: parses @Patch annotations from Kotlin source files."""
    patches = []
    # Pattern to find @Patch annotations
    patch_re = re.compile(
        r'@Patch\s*\((.*?)\)\s*(?:class|object)',
        re.DOTALL
    )
    
    # Pattern to parse fields inside @Patch
    name_re = re.compile(r'name\s*=\s*"([^"]+)"')
    desc_re = re.compile(r'description\s*=\s*"([^"]+)"')
    pkg_re = re.compile(r'compatiblePackages\s*=\s*(?:\[(.*?)\]|compatiblePackage\((.*?)\))', re.DOTALL)
    
    for path in sub_path.glob("**/*.kt"):
        try:
            content = path.read_text(encoding="utf-8")
            for match in patch_re.finditer(content):
                annotation = match.group(1)
                
                name_match = name_re.search(annotation)
                desc_match = desc_re.search(annotation)
                
                if name_match:
                    name = name_match.group(1)
                    desc = desc_match.group(1) if desc_match else ""
                    
                    # Try to extract compatible packages
                    compat_pkgs = []
                    pkg_match = pkg_re.search(annotation)
                    if pkg_match:
                        pkg_str = pkg_match.group(1) or pkg_match.group(2) or ""
                        # Find all package strings (e.g. com.google.android.youtube)
                        compat_pkgs = re.findall(r'"([\w\.]+)"', pkg_str)
                    
                    patches.append({
                        "name": name,
                        "description": desc,
                        "compatiblePackages": [{"name": p} for p in compat_pkgs] if compat_pkgs else []
                    })
        except Exception:
            continue
    return patches

def sync_all() -> None:
    updated_any = False
    all_patches_meta = []
    
    for sub in SUBMODULES:
        sub_path = Path(sub["path"])
        repo = sub["repo"]
        host = sub["host"]
        org_name = repo.split("/")[0].lower()
        repo_name = repo.split("/")[1].lower()
        dest_dir = Path("testing/patches") / org_name
        
        log(f"=== Synchronizing submodule '{sub['name']}' ===")
        
        # 1. Fetch updates
        run_cmd(["git", "fetch", "origin"], cwd=sub_path)
        branch = get_default_branch(sub_path)
        
        # Check if submodule has updates
        code, out, _ = run_cmd(["git", "log", f"HEAD..origin/{branch}"], cwd=sub_path)
        has_update = (code == 0 and bool(out))
        
        # Determine if we already have the localized patches file
        local_files = list(dest_dir.glob(f"*{repo_name}*"))
        has_local_file = bool(local_files)
        
        if has_update or not has_local_file:
            log(f"Submodule '{sub['name']}' has updates or is missing localized file. Pulling latest...")
            run_cmd(["git", "checkout", f"origin/{branch}"], cwd=sub_path)
            updated_any = True
            
            # Clean old files
            for f in dest_dir.glob(f"*{repo_name}*"):
                f.unlink(missing_ok=True)
                
            # Compile locally
            mpp_path = build_submodule(sub_path, dest_dir)
            if not mpp_path:
                # Fallback to downloading compiled assets
                mpp_path = fetch_upstream_release(repo, host, dest_dir)
        else:
            log(f"Submodule '{sub['name']}' is already up-to-date.")
            mpp_path = local_files[0] if local_files else None
            
        # Parse patch details for README documentation
        patches = []
        if mpp_path:
            patches = parse_patches_from_jar(mpp_path)
        if not patches:
            patches = parse_patches_from_sources(sub_path)
            
        log(f"Parsed {len(patches)} patches for '{sub['name']}'")
        all_patches_meta.append({
            "submodule": sub["name"],
            "repo": repo,
            "icon": sub["icon"],
            "patches": patches
        })
        
    # Regenerate README
    update_readme(all_patches_meta)
    log("=== Patch synchronization complete! ===")

def update_readme(all_meta: list[dict]) -> None:
    log("Regenerating Supported Patches section in README.md...")
    readme_path = Path("README.md")
    if not readme_path.exists():
        log("README.md not found. Skipping README update.")
        return
        
    content = readme_path.read_text(encoding="utf-8")
    
    # Generate Markdown Table
    md = [
        "| Source | Patch Name | Description | Targets |",
        "|:---:|:---|:---|:---|"
    ]
    
    for entry in all_meta:
        sub_name = entry["submodule"]
        repo = entry["repo"]
        icon = entry["icon"]
        patches = entry["patches"]
        
        url = f"https://github.com/{repo}" if "github" in repo else f"https://gitlab.com/{repo}"
        
        if not patches:
            md.append(f"| {icon} | **[{sub_name}]({url})** | Localized patch bundle (no metadata available) | Any |")
            continue
            
        for patch in patches:
            name = patch.get("name", "Unnamed Patch")
            desc = (patch.get("description") or "").replace("\n", " ").replace("|", "\\|")
            
            targets = []
            compat_pkgs = patch.get("compatiblePackages") or []
            for pkg in compat_pkgs:
                if isinstance(pkg, dict):
                    pkg_name = pkg.get("packageName") or pkg.get("name", "")
                else:
                    pkg_name = str(pkg)
                if pkg_name:
                    targets.append(f"`{pkg_name.split('.')[-1]}`")
                
            targets_str = ", ".join(targets) if targets else "Any"
            md.append(f"| {icon} | **[{name}]({url})** | {desc} | {targets_str} |")
            
    md_table = "\n".join(md)
    
    # Replace in README
    start_tag = "<!-- SUPPORTED_PATCHES_START -->"
    end_tag = "<!-- SUPPORTED_PATCHES_END -->"
    
    pattern = re.compile(rf"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)
    replacement = f"{start_tag}\n\n{md_table}\n\n{end_tag}"
    
    if pattern.search(content):
        new_content = pattern.sub(replacement, content)
        readme_path.write_text(new_content, encoding="utf-8")
        log("Successfully updated README.md.")
    else:
        log("Placeholder comments for Supported Patches not found in README.md.")

if __name__ == "__main__":
    sync_all()
