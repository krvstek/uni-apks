<div align="center">
<a href="#-features"><img src="https://readme-typing-svg.demolab.com/?font=Google+Sans&size=25&pause=1000&color=4500FF&center=true&vCenter=true&random=false&width=550&lines=%F0%9F%93%A6+Pre-built+APKs+from+various+patch+sources"></a>

[![Build Status](https://img.shields.io/github/actions/workflow/status/krvstek/uni-apks/build.yml?style=flat-square&logo=githubactions&logoColor=%23FFFFFF&label=Build%20Status&color=%234500FF)](https://github.com/krvstek/uni-apks/actions/workflows/build.yml)   [![Python 3.13](https://img.shields.io/badge/Python-3.13+-4500FF?style=flat-square&logo=python&logoColor=%23FFFFFF)](https://www.python.org/downloads/)   [![Built with uv](https://img.shields.io/badge/Built%20with-uv-4500FF?style=flat-square&logo=uv&logoColor=%23FFFFFF)](https://github.com/astral-sh/uv)
<br>
[![Release](https://img.shields.io/github/release-date/krvstek/uni-apks?display_date=created_at&style=flat-square&logo=android&logoColor=%23FFFFFF&label=Release&color=%234500FF)](https://github.com/krvstek/uni-apks/releases/latest)   [![Downloads](https://img.shields.io/github/downloads/krvstek/uni-apks/total?style=flat-square&logo=simpleanalytics&logoColor=%23FFFFFF&label=Downloads&color=%234500FF)](https://github.com/krvstek/uni-apks#-list-of-apps-in-this-repository)   [![Views](https://hitscounter.dev/api/hit?url=https%3A%2F%2Fgithub.com%2Fkrvstek%2Funi-apks&label=Views&icon=eye-fill&color=%234500ff&message=&style=flat-square&tz=Europe%2FWarsaw)](https://github.com/krvstek/uni-apks#-list-of-apps-in-this-repository)
<br>

Here you will find a step-by-step technical guide on how to set up your environment, run the patching script, customize the build configuration, and contribute to the project's development.
</div>

## 💻 Build Locally

1. 📋 **Requirements**:

- [Git](https://git-scm.com/downloads)
- [Python](https://www.python.org/downloads/latest/python3.13)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Java](https://adoptium.net/temurin/releases?version=21&os=any&arch=any)

2. 📥 **Installation**:

```bash
git clone --depth 1 https://github.com/krvstek/uni-apks.git
cd uni-apks
```

No further setup needed, as `uv` handles the Python environment and dependencies automatically.

3. ▶️ **Running**:

```bash
uv run main.py # build all apps
uv run main.py SomeApp # build a specific app
uv run main.py SomeApp arm64-v8a # build with arch override
uv run main.py clear # remove build/, temp/ and build.md
```

Output APKs are saved to `build/`.

## ⚙️ Configuration

All configuration lives in `config.toml` in the project root. Top-level keys define defaults inherited by every app entry. Each app is a TOML table.

```toml
[SomeApp]
apkmirror-dlurl = "https://www.apkmirror.com/apk/inc/app"
# uptodown-dlurl = "https://app.en.uptodown.com/android"
# github-dlurl = "https://github.com/<owner>/<repo>/releases/tag/app"
```

1. 📱 **Available options**:

| 🔑 Key | 📝 Description | 🔤 Default | 📌 Scope |
|:------:|:--------------:|:----------:|:--------:|
| `parallel-jobs` | Number of concurrent builds | `CPU count` | Global |
| `brand` | Used in output filenames | `Morphe` | Global / Per-app |
| `patches-version` | Patches version to fetch (`latest`, `dev`, or a specific version string) | `latest` | Global / Per-app |
| `cli-version` | CLI version to fetch (`latest`, `dev`, or a specific version string) | `latest` | Global / Per-app |
| `patches-source` | GitHub or GitLab repo for patches (`github:owner/repo` or `gitlab:owner/repo`) | `github:MorpheApp/morphe-patches` | Global / Per-app |
| `cli-source` | GitHub or GitLab repo for CLI (`github:owner/repo` or `gitlab:owner/repo`) | `github:MorpheApp/morphe-cli` | Global / Per-app |
| `strict-sigcheck` | Fail the build if an app is missing from `sig.txt` (see note below) | `true` | **Global only** |
| `app-name` | Display name used in output filename | `table name` | Per-app |
| `arch` | Target architecture (`all`, `both`, `arm64-v8a`, `armeabi-v7a`, `x86_64`, `x86`) | `all` | Per-app |
| `version` | Target version (`auto`, `latest`, or a specific version string) | `auto` | Per-app |
| `apkmirror-dlurl` | APKMirror page URL | `-` | Per-app |
| `uptodown-dlurl` | Uptodown page URL | `-` | Per-app |
| `github-dlurl` | GitHub Releases page URL | `-` | Per-app |
| `included-patches` | Patches to include - names must be single-quoted | `-` | Per-app |
| `excluded-patches` | Patches to exclude - names must be single-quoted | `-` | Per-app |
| `exclusive-patches` | Only apply `included-patches`, exclude everything else | `false` | Per-app |
| `patcher-args` | Extra arguments passed directly to Morphe CLI | `-` | Per-app |
| `skip-sigcheck` | Completely bypasses signature checks for this app (see note below) | `false` | **Per-app only** |
| `enabled` | Set to `false` to skip this entry | `true` | Per-app |

> [!NOTE]
> If a patch name contains a single quote, you must wrap the specific patch name in escaped double quotes.  
> Example: `included-patches = "'Example patch' \"Hide 'Example button'\" 'Another example patch'"`

2. 🔏 **Signature verification flags**:

The build system includes two independent flags for controlling APK signature verification.

* `strict-sigcheck` **(Global root level only | Default: `true`)**  
Controls the strict requirement for `sig.txt`:
> - When set to `false`, the build will not fail if an app is missing from `sig.txt` (useful for forks and local testing). If a signature entry does exist, it is still verified normally.

* `skip-sigcheck` **(Per-app [AppName] level only | Default: `false`)**  
Acts as a total bypass of signature verification for one specific app.
> - When set to `true`, the build completely ignores `sig.txt` and native APK certificate checks for that app. Use this only for pre-modified APKs (e.g. with PairIP removed) where the original certificate is gone.


**How to add a signature entry to `sig.txt`** (only needed when `skip-sigcheck` is `false`):

> * **Method 1 (Quick):** Copy the original SHA-256 fingerprint directly from a trusted source like **APKMirror** (listed on every APK download page).
> * **Method 2 (Manual):** Use the provided toolchain on the original, unmodified APK: `java -jar apksigner.jar verify --print-certs <app.apk>`
> 
> Format for `sig.txt`: `<sha256-fingerprint>  <package.name>`

3. ➕ **Adding a new patch source**:

- Add your app entries to `config.toml` with the appropriate `patches-source` and `brand` fields (see the configuration table above for all available options).
- Add a new job to `.github/workflows/ci.yml` so the CI picks up your brand automatically. Copy the block below and replace every occurrence of `<brand>` with your brand name in **lowercase** (must match the `brand` value set in `config.toml`):
```yaml
build-<brand>:
  name: build (<brand>)
  needs: check-versions
  if: contains(fromJson(needs.check-versions.outputs.build_matrix), '<brand>')
  uses: ./.github/workflows/build.yml
  with:
    patch_source: '<brand>'
  secrets: inherit
```

4. 🔑 **Keystore**:

To sign APKs with a custom keystore, create a `.env` file in the project root:

```env
KEYSTORE_BASE64=<base64-encoded keystore>
KEYSTORE_PASS=<keystore password>
KEYSTORE_ALIAS=<keystore alias>
```

To encode an existing keystore:

```bash
base64 -w 0 my.keystore
```

On **GitHub Actions**, set `KEYSTORE_BASE64`, `KEYSTORE_PASS` and `KEYSTORE_ALIAS` as repository secrets under **Settings → Secrets and variables → Actions** instead of a `.env` file, as they are passed to the build automatically.

If no keystore is configured, `morphe.keystore` is used as a fallback if it exists in the project root. If neither is present, the CLI signs with its built-in debug keystore. On **GitHub Actions** this means every release will have a different signature, making app updates **impossible**.

## 🤝 Contributing

1. 🐞 **Bug reports**:

For bugs in the **build script itself**, use the [Script Bug Report](https://github.com/krvstek/uni-apks/issues/new?template=script.yml) template. For bugs in **patched applications**, use the [Build Result Bug Report](https://github.com/krvstek/uni-apks/issues/new?template=build.yml) template.

2. **💡 Suggestions**:

Feature ideas belong in the [Discussions](https://github.com/krvstek/uni-apks/discussions) tab, as this keeps the issue tracker focused on bugs.

3. **🛠️ Pull Requests**:

Pull requests are welcome. AI-assisted contributions are accepted, but all changes must be manually reviewed before submitting, as you are responsible for every line you put your name on. I reserve the right to reject any contribution that does not align with the project's vision.

---

<p align="center"><i>Maintained with ❤️ by <a href="https://github.com/krvstek">krvstek</a></i></p>
