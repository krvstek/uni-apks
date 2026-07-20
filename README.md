# 📦 Uni-APKs (Testing Pipeline)

[![Build Status](https://img.shields.io/github/actions/workflow/status/krvstek/uni-apks/ci.yml?style=flat-square&logo=githubactions&logoColor=%23FFFFFF&label=Build%20Status&color=%234500FF)](https://github.com/krvstek/uni-apks/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/Python-3.13+-4500FF?style=flat-square&logo=python&logoColor=%23FFFFFF)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-Channel-4500FF?style=flat-square&logo=telegram&logoColor=%23FFFFFF)](https://t.me/uni_apks)

This repository automates the compilation and patching of popular Android applications. By using Git submodules, all patch sources are fully localized within this repository. Upstream patch changes are monitored daily, compiled on CI/CD, and used to build updated, ad-free, and customized APKs.

---

## 🔥 Features

- 🛑 **Ad-blocking:** Removes video and layout advertisements inside modified apps.
- ⭐ **Customization:** Customize app themes, icons, names, and internal branding.
- 📂 **Patch Localization:** Keeps all patch source code localized via Git submodules.
- ⚡ **Incremental Builds:** Skips rebuilding unaffected APKs to save CI runtime.
- 🔒 **Certificate Integrity:** All built APKs can be verified using certificate fingerprints to prevent tampering.

---

## 📂 Repository Structure

```
├── .github/
│   └── workflows/
│       ├── ci.yml               # Daily cron job checking upstream patches
│       └── build.yml            # Main APK building & testing pipeline
├── bin/
│   └── apksigner.jar            # Patcher helper tools (apksigner)
├── patches/                     # Localized patch submodules (Git history preserved)
│   ├── morphe-patches/
│   ├── piko/
│   └── ...
├── src/
│   ├── core/
│   │   ├── builder.py           # Core app patching logic
│   │   ├── config.py            # TOML config parsing
│   │   ├── network.py           # Rate-limited HTTP download manager
│   │   └── patcher.py           # Patcher CLI wrapper
│   └── scripts/
│       ├── sync_patches.py      # Automates submodule fetch & Gradle compile
│       └── matrix.py            # Determines incremental build scopes
├── testing/
│   └── patches/                 # Localized compiled .mpp patch binaries
├── config.toml                  # App configurations, patch versions, and rules
├── main.py                      # Main entrypoint CLI
└── README.md                    # Project manual (this file)
```

---

## ⚙️ Branching Workflow & Maintenance

This repository follows a strict branching workflow to guarantee production stability:

1. **`Testing` Branch**: All daily cron jobs, automated patch updates, code optimizations, and APK builds target the `Testing` branch first.
2. **Validation**: All builds are uploaded as workflow artifacts on the `Testing` branch and verified for compilation success, artifact integrity, and logs.
3. **`main` Branch**: The `main` branch is kept stable and only receives changes via Pull Requests merged from `Testing` after all verification checks have passed.

---

## ⏰ Automated Update & Synchronization

1. **Daily Cron Job**: Runs daily at `10:00 UTC` on GitHub Actions to check for upstream commits across all patch submodules.
2. **Patch Compilation**: If an update is detected, the workflow fetches the changes, compiles the submodule using Gradle (`./gradlew build`), and outputs the compiled `.mpp` binary to `testing/patches/`. If compilation fails, it downloads the compiled release asset as a fallback.
3. **README Synchronization**: The patch details (names, descriptions, and compatibility) are parsed from the `.mpp` JAR and injected directly into the **Supported Patches** table below.
4. **Change Promotion**: The updated submodules, compiled patches, and updated `README.md` are committed and pushed to the `Testing` branch.
5. **Trigger Build**: Pushing new changes to `Testing` automatically triggers the **Build APKs** workflow.

---

## 🛠️ Local Installation & Usage Guide

### Prerequisites
- **Python 3.12+**
- **Java JDK 21+** (in PATH)

### Setup
Install Python dependencies:
```bash
python -m pip install beautifulsoup4 curl-cffi
```

### Running Builds Locally
Build an application defined in `config.toml` (e.g. YouTube or Reddit):
```bash
# Build Reddit for default architecture (arm64-v8a)
python main.py Reddit

# Build YouTube for a specific architecture
python main.py YouTube arm64-v8a

# Clean up temporary scratch directories
python main.py clear
```

---

## 🧩 Supported Patches

This section displays all supported patches and compatible packages, and is kept automatically synchronized by the patch sync script.

<!-- SUPPORTED_PATCHES_START -->

| Source | Patch Name | Description | Targets |
|:---:|:---|:---|:---|
| 🧩 | **[Add to queue](https://gitlab.com/MorpheApp/morphe-patches)** | Overrides the feed flyout 'Play next in queue' with the Morphe video queue. | `youtube` |
| 🧩 | **[Alternative thumbnails](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to replace video thumbnails using the DeArrow API or image captures from the video. | `youtube` |
| 🧩 | **[Ambient mode](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to bypass power saving restrictions for Ambient mode and disable it entirely or in fullscreen. | `youtube` |
| 🧩 | **[Bypass certificate checks](https://gitlab.com/MorpheApp/morphe-patches)** | Bypasses certificate checks which prevent YouTube Music from working on Android Auto. | `music` |
| 🧩 | **[Bypass image region restrictions](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to use a different host for user avatar and channel images and can fix missing images that are blocked in some countries. | `youtube` |
| 🧩 | **[Bypass link redirects](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to bypass redirects and open the original link directly. | `youtube` |
| 🧩 | **[Captions](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable captions from being automatically enabled or to set caption cookies. | `youtube` |
| 🧩 | **[Change form factor](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to change the UI appearance to a phone, tablet, or automotive device. | `youtube` |
| 🧩 | **[Change header](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to change the header logo in the top left corner of the app. | `music` |
| 🧩 | **[Change header](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to change the header logo in the top left corner of the app. | `youtube` |
| 🧩 | **[Change miniplayer color](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to change the miniplayer background color to match the fullscreen player. | `music` |
| 🧩 | **[Change package name](https://gitlab.com/MorpheApp/morphe-patches)** | Appends ".morphe" to the package name by default. Changing the package name of the app can lead to unexpected issues. | Any |
| 🧩 | **[Change start page](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to set which page the app opens in instead of the homepage. | `music` |
| 🧩 | **[Change start page](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to set which page the app opens in instead of the homepage. | `youtube` |
| 🧩 | **[Check watch history domain name resolution](https://gitlab.com/MorpheApp/morphe-patches)** | Checks if the device DNS server is preventing user watch history from being saved. | `music` |
| 🧩 | **[Check watch history domain name resolution](https://gitlab.com/MorpheApp/morphe-patches)** | Checks if the device DNS server is preventing user watch history from being saved. | `youtube` |
| 🧩 | **[Copy video link](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to display buttons in the video player to copy video links. | `youtube` |
| 🧩 | **[Custom branding](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to change the app icon and app name. Branding cannot be changed for mounted (root) installations. | `music` |
| 🧩 | **[Custom branding](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to change the app icon and app name. Branding cannot be changed for mounted (root) installations. | `youtube` |
| 🧩 | **[Custom branding name for Reddit](https://gitlab.com/MorpheApp/morphe-patches)** | Changes the Reddit app name to the name specified in patch options. | `frontpage` |
| 🧩 | **[Custom player overlay opacity](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to change the opacity of the video player background when player controls are visible. | `youtube` |
| 🧩 | **[Disable DRC audio](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable DRC (Dynamic Range Compression) audio. | `music` |
| 🧩 | **[Disable DRC audio](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable DRC (Dynamic Range Compression) audio. | `youtube` |
| 🧩 | **[Disable Play Store updates](https://gitlab.com/MorpheApp/morphe-patches)** | Disables Play Store updates by setting the version code to the maximum allowed. This patch does not work if the app is installed by mounting and may cause unexpected issues with some apps. | Any |
| 🧩 | **[Disable QUIC protocol](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable QUIC (Quick UDP Internet Connections) network protocol. | `music` |
| 🧩 | **[Disable QUIC protocol](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable QUIC (Quick UDP Internet Connections) network protocol. | `youtube` |
| 🧩 | **[Disable Shorts resuming on startup](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable Shorts from resuming on app startup when Shorts were last being watched. | `youtube` |
| 🧩 | **[Disable dislike redirection](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to prevent skipping to the next track when the dislike button is pressed. | `music` |
| 🧩 | **[Disable double tap actions](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable player double tap gestures. | `youtube` |
| 🧩 | **[Disable fullscreen gestures](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to selectively disable gestures for entering and exiting fullscreen mode. | `youtube` |
| 🧩 | **[Disable haptic feedback](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable haptic feedback in the player for various actions. | `youtube` |
| 🧩 | **[Disable layout updates](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable server side layout updates and use an older UI. | `youtube` |
| 🧩 | **[Disable modern home](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable the modern home UI. This patch works with Reddit 2026.24.0 and earlier. | `frontpage` |
| 🧩 | **[Disable player popup panels](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable panels (such as live chat) from opening automatically. | `youtube` |
| 🧩 | **[Disable rolling number animations](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable rolling number animations of video view count, user likes, and upload time. | `youtube` |
| 🧩 | **[Disable screenshot popup](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable the popup that appears when taking a screenshot. | `frontpage` |
| 🧩 | **[Disable sign in to TV popup](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to disable the popup asking to sign into a TV on the same local network. | `youtube` |
| 🧩 | **[Disable video codecs](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to disable HDR and VP9 codecs. | `youtube` |
| 🧩 | **[Double tap to seek](https://gitlab.com/MorpheApp/morphe-patches)** | Adds additional double-tap to seek values to the YouTube settings menu. | `youtube` |
| 🧩 | **[Downloads](https://gitlab.com/MorpheApp/morphe-patches)** | Adds support to download songs with an external downloader app using the in-app download button. | `music` |
| 🧩 | **[Downloads](https://gitlab.com/MorpheApp/morphe-patches)** | Adds support to download videos with an external downloader app using the in-app download button or a video player action button. | `youtube` |
| 🧩 | **[Enable debugging](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options for debugging and exporting Morphe logs to the clipboard. | `music` |
| 🧩 | **[Enable debugging](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options for debugging and exporting Morphe logs to the clipboard. | `youtube` |
| 🧩 | **[Enable exclusive audio playback](https://gitlab.com/MorpheApp/morphe-patches)** | Enables the option to play audio without video. | `music` |
| 🧩 | **[Enable forced miniplayer](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to enable forced miniplayer when switching between music videos, podcasts, or songs. | `music` |
| 🧩 | **[Enable swipe to dismiss miniplayer](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to enable dismissing the miniplayer by swiping down on it. | `music` |
| 🧩 | **[Exit fullscreen mode](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to automatically exit fullscreen mode when a video reaches the end. | `youtube` |
| 🧩 | **[Force original audio](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to always use the original audio track. | `music` |
| 🧩 | **[Force original audio](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to always use the original audio track. | `youtube` |
| 🧩 | **[GmsCore support](https://gitlab.com/MorpheApp/morphe-patches)** | Allows the app to work without root by using a different package name when patched using a GmsCore instead of Google Play Services. | `music` |
| 🧩 | **[GmsCore support](https://gitlab.com/MorpheApp/morphe-patches)** | Allows the app to work without root by using a different package name when patched using a GmsCore instead of Google Play Services. | `youtube` |
| 🧩 | **[Hide Ask button](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide Ask button in the search bar. | `frontpage` |
| 🧩 | **[Hide Reddit search](https://gitlab.com/MorpheApp/morphe-patches)** | Permanently hides the Reddit search in the contextual menu. This patch does not work with root mounting | `frontpage` |
| 🧩 | **[Hide Shorts components](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide components related to Shorts. | `youtube` |
| 🧩 | **[Hide Trending shelves](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide the Trending shelves from feed and search suggestions. | `frontpage` |
| 🧩 | **[Hide ads](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide fullscreen ads, Premium promotions and video ads. | `music` |
| 🧩 | **[Hide ads](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide ads. | `frontpage` |
| 🧩 | **[Hide ads](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide general ads, Premium promotions and video ads. | `youtube` |
| 🧩 | **[Hide autoplay preview](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide the autoplay preview at the end of videos. | `youtube` |
| 🧩 | **[Hide buttons](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide the cast, history, notification, and search buttons. | `music` |
| 🧩 | **[Hide communities shelf](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide the related or suggested communities shelf in subreddits. | `frontpage` |
| 🧩 | **[Hide end screen cards](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide suggested video cards at the end of videos. | `youtube` |
| 🧩 | **[Hide end screen suggested video](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide the suggested video at the end of videos. | `youtube` |
| 🧩 | **[Hide filter bar](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide the filter bar at the top of the homepage. | `music` |
| 🧩 | **[Hide flyout menu components](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide individual items from the player and queue flyout menus. | `music` |
| 🧩 | **[Hide info cards](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide info cards that creators add in the video player. | `youtube` |
| 🧩 | **[Hide layout components](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide general layout components. | `music` |
| 🧩 | **[Hide layout components](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide general layout components. | `youtube` |
| 🧩 | **[Hide music action buttons](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide action buttons under the player. | `music` |
| 🧩 | **[Hide navigation buttons](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide buttons in the navigation bar. | `frontpage` |
| 🧩 | **[Hide player flyout menu components](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide menu components that appear when pressing the gear icon in the video player. | `youtube` |
| 🧩 | **[Hide player overlay buttons](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide the player Cast, Autoplay, Captions, Previous & Next buttons, and the player control buttons background. | `youtube` |
| 🧩 | **[Hide related video overlay](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide the related video overlay shown when swiping up in fullscreen. | `youtube` |
| 🧩 | **[Hide related videos](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide related videos. | `youtube` |
| 🧩 | **[Hide sidebar components](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide the sidebar components. | `frontpage` |
| 🧩 | **[Hide timestamp](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to hide the timestamp in the bottom left of the video player. | `youtube` |
| 🧩 | **[Hide video action buttons](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide video action buttons in fullscreen and portrait modes. | `youtube` |
| 🧩 | **[Loop video](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to loop videos and display loop video button in the video player. | `youtube` |
| 🧩 | **[Media notification controls](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to disable the seekbar and previous/next buttons in the media notification and headphone controls. | `youtube` |
| 🧩 | **[Miniplayer](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to change the in-app minimized player. | `youtube` |
| 🧩 | **[Miniplayer previous and next buttons](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to show previous and next track buttons in the miniplayer. | `music` |
| 🧩 | **[Navigation bar](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide navigation bar, labels and buttons. | `music` |
| 🧩 | **[Navigation bar](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to hide and change the bottom navigation bar (such as the Shorts button)  and the upper navigation toolbar. Patching version 20.21.37 and lower also adds a setting to use a wide searchbar. | `youtube` |
| 🧩 | **[Network proxy](https://gitlab.com/MorpheApp/morphe-patches)** | Adds settings to route supported network requests through an HTTP or HTTPS proxy. | `music` |
| 🧩 | **[Network proxy](https://gitlab.com/MorpheApp/morphe-patches)** | Adds settings to route supported network requests through an HTTP or HTTPS proxy. | `youtube` |
| 🧩 | **[Open Shorts in regular player](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to open Shorts in the regular video player. | `youtube` |
| 🧩 | **[Open channel of live avatar](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to prevent a channel's current live video from opening when tapping its avatar. | `youtube` |
| 🧩 | **[Open links directly](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to skip over redirection URLs in external links. | `frontpage` |
| 🧩 | **[Open links externally](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to always open links in your browser instead of with the in-app-browser. | `frontpage` |
| 🧩 | **[Open links externally](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to always open links in your browser instead of with the in-app browser. | `youtube` |
| 🧩 | **[Open system share sheet](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to always open the system share sheet instead of the in-app share sheet. | `youtube` |
| 🧩 | **[Open videos fullscreen](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to automatically open videos in fullscreen portrait or landscape mode. | `youtube` |
| 🧩 | **[Override YouTube Music buttons](https://gitlab.com/MorpheApp/morphe-patches)** | Overrides YouTube Music buttons to open Morphe Music or any compatible third-party client. | `youtube` |
| 🧩 | **[Override certificate pinning](https://gitlab.com/MorpheApp/morphe-patches)** | Overrides certificate pinning, allowing to inspect traffic via a proxy. | Any |
| 🧩 | **[Play all](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to play all the videos from a channel and to display play all button in the video player. | `youtube` |
| 🧩 | **[Playback speed](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to customize available playback speeds, set a default playback speed, and show a speed dialog button in the video player. | `youtube` |
| 🧩 | **[Reload video](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to display reload video button in the video player. | `youtube` |
| 🧩 | **[Remember repeat state](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to remember the repeat state when playing a new track or playlist. | `music` |
| 🧩 | **[Remember shuffle state](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to remember the shuffle state when playing a new track or playlist. | `music` |
| 🧩 | **[Remove background playback restrictions](https://gitlab.com/MorpheApp/morphe-patches)** | Removes restrictions on background playback, including playing kids videos in the background. | `music` |
| 🧩 | **[Remove background playback restrictions](https://gitlab.com/MorpheApp/morphe-patches)** | Removes restrictions on background playback, including playing kids videos in the background. | `youtube` |
| 🧩 | **[Remove subreddit dialog](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to remove the NSFW community warning and notifications suggestion dialogs by dismissing them automatically. | `frontpage` |
| 🧩 | **[Remove viewer discretion dialog](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to remove the dialog that appears when opening a video that has been age-restricted by accepting it automatically. This does not bypass the age restriction. | `youtube` |
| 🧩 | **[Return YouTube Dislike](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to show the dislike count of videos with Return YouTube Dislike. | `youtube` |
| 🧩 | **[Sanitize sharing links](https://gitlab.com/MorpheApp/morphe-patches)** | Removes the tracking query parameters from shared links. | `music` |
| 🧩 | **[Sanitize sharing links](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to sanitize sharing links by removing tracking query parameters. | `frontpage` |
| 🧩 | **[Sanitize sharing links](https://gitlab.com/MorpheApp/morphe-patches)** | Removes the tracking query parameters from shared links. | `youtube` |
| 🧩 | **[Save to watch later](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to display save to watch later button in the video player. | `youtube` |
| 🧩 | **[Scrobbling](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to add played tracks to Last.fm and ListenBrainz. | `music` |
| 🧩 | **[Seekbar](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to disable precise seeking when swiping up on the seekbar, slide to seek instead of playing at 2x speed when pressing and holding, tapping the player seekbar to seek, hiding the video player seekbar, enabling seeking in livestreams, and expanding the livestream DVR duration. | `youtube` |
| 🧩 | **[Shorts autoplay](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to automatically play the next Short. | `youtube` |
| 🧩 | **[Show view count](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to show the view count of Posts. | `frontpage` |
| 🧩 | **[SponsorBlock](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to enable and configure SponsorBlock, which can skip non-music segments. | `music` |
| 🧩 | **[SponsorBlock](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to enable and configure SponsorBlock, which can skip undesired video segments such as sponsored content. | `youtube` |
| 🧩 | **[Spoof app version](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to trick the app into thinking you are running an older version. | `music` |
| 🧩 | **[Spoof app version](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to trick the app into thinking you are running an older version. | `youtube` |
| 🧩 | **[Spoof device dimensions](https://gitlab.com/MorpheApp/morphe-patches)** | Adds an option to spoof the device dimensions which can unlock higher video qualities. | `youtube` |
| 🧩 | **[Spoof signature](https://gitlab.com/MorpheApp/morphe-patches)** | Spoofs the signature of the app to fix notification issues. | `frontpage` |
| 🧩 | **[Spoof video streams](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to spoof the client video streams to fix playback. | `music` |
| 🧩 | **[Spoof video streams](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to spoof the client video streams to fix playback. | `youtube` |
| 🧩 | **[Swipe controls](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to enable and configure volume and brightness swipe controls. | `youtube` |
| 🧩 | **[Theme](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options for theming and applies a custom background theme (dark background theme defaults to pure black). | `music` |
| 🧩 | **[Theme](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options for theming and applies a custom background theme (dark background theme defaults to pure black). | `youtube` |
| 🧩 | **[Track crossfade](https://gitlab.com/MorpheApp/morphe-patches)** | Adds a true dual-player crossfade between consecutive tracks. Requires YouTube Music 9.00 or newer; on older versions the patch is a no-op. | `music` |
| 🧩 | **[Video quality](https://gitlab.com/MorpheApp/morphe-patches)** | Adds options to set default video qualities and always use the advanced video quality menu. | `youtube` |
| 🧩 | **[Voice over translation](https://gitlab.com/MorpheApp/morphe-patches)** | Adds additional voice over languages using text-to-speech synchronized to the video playback. | `youtube` |
| 🦊 | **[Add ability to copy media link](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Add settings](https://gitlab.com/crimera/piko)** | Adds settings to control preferences are patching | `android` |
| 🦊 | **[Allow user network certificate](https://gitlab.com/crimera/piko)** | Allows user network certificate for whitehat testing | `android` |
| 🦊 | **[Amoled theme](https://gitlab.com/crimera/piko)** | Replaces Instagram's dark-mode background greys with pure black for AMOLED displays. | `android` |
| 🦊 | **[Block redirecting to X Lite](https://gitlab.com/crimera/piko)** | Blocks redirecting to the new X Android UI on launch | `android` |
| 🦊 | **[Bring back twitter](https://gitlab.com/crimera/piko)** | Bring back old twitter logo and name | `android` |
| 🦊 | **[Browse tweet object](https://gitlab.com/crimera/piko)** | Adds an option to browse the tweet object in the share menu. | `android` |
| 🦊 | **[Change app icon](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Change like animation](https://gitlab.com/crimera/piko)** | Change the animation to one from existing Rings like animations | `android` |
| 🦊 | **[Change version code](https://gitlab.com/crimera/piko)** | Changes the version code of the app. This will turn off app store updates and allows downgrading an existing app install to an older app version. | `android`, `android` |
| 🦊 | **[Clear tracking params](https://gitlab.com/crimera/piko)** | Removes tracking parameters when sharing links | `android` |
| 🦊 | **[Clone](https://gitlab.com/crimera/piko)** | Changes the package name and the app name. This allows you to install the patched app alongside the original Instagram app. Caution: Do not select the official Morphe's "Change package name" universal patch. | `android` |
| 🦊 | **[Control video auto scroll](https://gitlab.com/crimera/piko)** | Control video auto scroll in immersive view | `android` |
| 🦊 | **[Copy comment](https://gitlab.com/crimera/piko)** | Adds a button to copy comments on posts and reels. | `android` |
| 🦊 | **[Custom download folder](https://gitlab.com/crimera/piko)** | Change the download directory for video downloads | `android` |
| 🦊 | **[Custom emoji font](https://gitlab.com/crimera/piko)** | Customise emoji font style | `android` |
| 🦊 | **[Custom font](https://gitlab.com/crimera/piko)** | Customise font style | `android` |
| 🦊 | **[Custom sharing domain](https://gitlab.com/crimera/piko)** | Allows for using domains like fxtwitter when sharing tweets/posts. | `android` |
| 🦊 | **[Customise post font size](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customise story ring size](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customise story timestamp](https://gitlab.com/crimera/piko)** | Customise the timestamp that shows when the story was posted | `android` |
| 🦊 | **[Customize Inline action Bar items](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customize Navigation Bar items](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customize default reply sorting](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customize explore tabs](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customize notification tabs](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customize profile tabs](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customize search suggestions](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customize search tab items](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customize side bar items](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Customize timeline top bar](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Delete from database](https://gitlab.com/crimera/piko)** | Delete entries from database(cache) | `android` |
| 🦊 | **[Disable Reels scrolling](https://gitlab.com/crimera/piko)** | Disables the endless scrolling behavior in Instagram Reels, preventing swiping to the next Reel. Note: On a clean install, the 'Tip' animation may appear but will stop on its own after a few seconds. | `android` |
| 🦊 | **[Disable ads](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Disable analytics](https://gitlab.com/crimera/piko)** | Block analytics that are sent to Instagram/Facebook servers. | `android` |
| 🦊 | **[Disable auto timeline scroll on launch](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Disable chirp font](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Disable comments](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Disable discover people](https://gitlab.com/crimera/piko)** | Disables discover people section on user profile | `android` |
| 🦊 | **[Disable double tap like](https://gitlab.com/crimera/piko)** | Disable double tap like on post, reel, comment and message | `android` |
| 🦊 | **[Disable explore](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Disable highlights](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Disable screenshot detection](https://gitlab.com/crimera/piko)** | Disables screenshots detection in DM | `android` |
| 🦊 | **[Disable stories](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Disable story flipping](https://gitlab.com/crimera/piko)** | Disable automatic flipping/moving to next story | `android` |
| 🦊 | **[Disable typing status](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Disable video autoplay](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Disunify xchat system](https://gitlab.com/crimera/piko)** | Bring back legacy features like messages and share sheet. | `android` |
| 🦊 | **[Download media](https://gitlab.com/crimera/piko)** | Adds ability to download posts, reels, stories and highlights | `android` |
| 🦊 | **[Download patch](https://gitlab.com/crimera/piko)** | Unlocks the ability to download videos and gifs from Twitter/X | `android` |
| 🦊 | **[Download voice message](https://gitlab.com/crimera/piko)** | Enables ability to download voice messages | `android` |
| 🦊 | **[Dynamic color](https://gitlab.com/crimera/piko)** | Replaces the default Twitter Blue with the user's Material You palette. | `android` |
| 🦊 | **[Enable PiP mode automatically](https://gitlab.com/crimera/piko)** | Enables PiP mode when you close the app | `android` |
| 🦊 | **[Enable Undo Posts](https://gitlab.com/crimera/piko)** | Enables ability to undo posts before posting | `android` |
| 🦊 | **[Enable debug menu for posts](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Enable force HD videos](https://gitlab.com/crimera/piko)** | Videos will be played in highest quality always | `android` |
| 🦊 | **[Export all activities](https://gitlab.com/crimera/piko)** | Makes all app activities exportable. | `android` |
| 🦊 | **[External downloader](https://gitlab.com/crimera/piko)** | Adds support to share post links directly to external downloader | `android` |
| 🦊 | **[Force enable translate](https://gitlab.com/crimera/piko)** | Get translate option for all posts | `android` |
| 🦊 | **[Friendship status indicator](https://gitlab.com/crimera/piko)** | Adds a follows you back status label on the profile page andshows a detailed friendship status breakdown on click | `android` |
| 🦊 | **[Handle custom twitter links](https://gitlab.com/crimera/piko)** | Adds support for opening custom twitter links such as vxtwitter, fxtwitter, and fixupx within the app. These will have to be manually enabled under the "Open by default" section in the app info! | `android` |
| 🦊 | **[Hide Banner](https://gitlab.com/crimera/piko)** | Hide new post banner | `android` |
| 🦊 | **[Hide Community Notes](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Hide FAB](https://gitlab.com/crimera/piko)** | Adds an option to hide Floating action button | `android` |
| 🦊 | **[Hide FAB Menu Buttons](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Hide Live Threads](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Hide Recommended Users](https://gitlab.com/crimera/piko)** | Hide recommended users that pops up when you follow someone | `android` |
| 🦊 | **[Hide badges from navigation bar icons](https://gitlab.com/crimera/piko)** | Hides notification nudges & counts from navigation bar icons | `android` |
| 🦊 | **[Hide bookmark icon in timeline](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Hide community badges](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Hide followed by context](https://gitlab.com/crimera/piko)** | Hides followed by context under profile | `android` |
| 🦊 | **[Hide group creation button on sharesheet](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Hide hidden replies](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Hide immersive player](https://gitlab.com/crimera/piko)** | Removes swipe up for more videos in video player | `android` |
| 🦊 | **[Hide navigation buttons](https://gitlab.com/crimera/piko)** | Hides navigation bar buttons, such as the Reels and Create button. | `android` |
| 🦊 | **[Hide notes tray](https://gitlab.com/crimera/piko)** | Hides notes tray in DM section | `android` |
| 🦊 | **[Hide nudge button](https://gitlab.com/crimera/piko)** | Hides follow/subscribe/follow back buttons on posts | `android` |
| 🦊 | **[Hide post metrics](https://gitlab.com/crimera/piko)** | Hides like, reposts etc counts. | `android` |
| 🦊 | **[Hide promote button](https://gitlab.com/crimera/piko)** | Hides promote button under self posts | `android` |
| 🦊 | **[Hide recommendation items](https://gitlab.com/crimera/piko)** | Adds options to hide recommendation items such as "Who to follow" and "Today's news" in timeline, search, and replies. | `android` |
| 🦊 | **[Hide reshare button](https://gitlab.com/crimera/piko)** | Hides the reshare button from both posts and reels. | `android` |
| 🦊 | **[Hide stories tray](https://gitlab.com/crimera/piko)** | Hides stories tray from main feed. | `android` |
| 🦊 | **[Hide suggested content](https://gitlab.com/crimera/piko)** | Hides suggested stories, reels, threads (Suggested posts will still be shown). | `android` |
| 🦊 | **[Hook feature flag](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Import/Export login token](https://gitlab.com/crimera/piko)** | Adds an feature to export and import the token of accounts. This is useful when logging in on your second device or when re-installing piko. | `android` |
| 🦊 | **[Improve image viewing](https://gitlab.com/crimera/piko)** | Fetches max resolution images from server. | `android` |
| 🦊 | **[Legacy share links](https://gitlab.com/crimera/piko)** | Brings back username on post share links. Works post 11.4x.xx | `android` |
| 🦊 | **[Limit feed to following profiles](https://gitlab.com/crimera/piko)** | Filters the home feed to display only content from profiles you follow. | `android` |
| 🦊 | **[Log server response](https://gitlab.com/crimera/piko)** | Log json responses received from server | `android` |
| 🦊 | **[Make ephemeral media permanent](https://gitlab.com/crimera/piko)** | Changes unexpired view once, view twice media to permanent view. | `android` |
| 🦊 | **[More options on post](https://gitlab.com/crimera/piko)** | Adds an overflow menu button to get more options on post/reels, like copy description, copy username etc | `android` |
| 🦊 | **[More options on profile](https://gitlab.com/crimera/piko)** | Adds a new button to handle user related data like copy handle, download profile picture etc | `android` |
| 🦊 | **[Native downloader](https://gitlab.com/crimera/piko)** | Requires X 11.0.0-release.0 or higher. | `android` |
| 🦊 | **[Native reader mode](https://gitlab.com/crimera/piko)** | Requires X 11.0.0-release.0 or higher. | `android` |
| 🦊 | **[Native translator](https://gitlab.com/crimera/piko)** | Requires X 11.0.0-release.0 or higher. | `android` |
| 🦊 | **[No shortened URL](https://gitlab.com/crimera/piko)** | Get rid of t.co short urls. | `android` |
| 🦊 | **[Open links externally](https://gitlab.com/crimera/piko)** | Changes links to always open in your external browser, instead of the in-app browser. | `android` |
| 🦊 | **[Pause search suggestions](https://gitlab.com/crimera/piko)** | Search suggestions will not be saved locally | `android` |
| 🦊 | **[Remove Ads](https://gitlab.com/crimera/piko)** | Removed promoted posts, trends and google ads | `android` |
| 🦊 | **[Remove build expired popup](https://gitlab.com/crimera/piko)** | Removes the popup that appears after a while, when the app version ages. | `android` |
| 🦊 | **[Remove empty bottom space](https://gitlab.com/crimera/piko)** | Removes empty space below bottom navigation bar | `android` |
| 🦊 | **[Remove premium upsell](https://gitlab.com/crimera/piko)** | Removes premium upsell in home timeline | `android` |
| 🦊 | **[Remove search suggestions](https://gitlab.com/crimera/piko)** | Hide/Remove search suggestion in explore section | `android` |
| 🦊 | **[Remove view count](https://gitlab.com/crimera/piko)** | Removes the view count from the bottom of tweets | `android` |
| 🦊 | **[Round off numbers](https://gitlab.com/crimera/piko)** | Enable or disable rounding off numbers | `android` |
| 🦊 | **[Sanitize share links](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Save media comment](https://gitlab.com/crimera/piko)** | Adds a button to save media comments on posts and reels. | `android` |
| 🦊 | **[Selectable Text](https://gitlab.com/crimera/piko)** | Makes bio and username selectable | `android` |
| 🦊 | **[Share Tweet as Image](https://gitlab.com/crimera/piko)** | Share tweets as rendered image. Requires X 11.0.0-release.0 or higher. | `android` |
| 🦊 | **[Show changelogs](https://gitlab.com/crimera/piko)** | Shows changelogs when new a patch is installed. | `android` |
| 🦊 | **[Show poll results](https://gitlab.com/crimera/piko)** | Adds an option to show poll results without voting | `android` |
| 🦊 | **[Show post source label](https://gitlab.com/crimera/piko)** | Source label will be shown only on public posts | `android` |
| 🦊 | **[Show sensitive media](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Stories audio autoplay](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[Unlock Plus benefits](https://gitlab.com/crimera/piko)** | Unlocks 'Plus' subscription benefits that are checked locally. USE IT AT YOUR OWN RISK | `android` |
| 🦊 | **[Unlock developer options](https://gitlab.com/crimera/piko)** | Unlocks developer option by long pressing home icon | `android` |
| 🦊 | **[Unlock employee options](https://gitlab.com/crimera/piko)** | Unlocks all options using by employee for debugging | `android` |
| 🦊 | **[Validate links](https://gitlab.com/crimera/piko)** | Fixes app crashing issue while opening links from a different app | `android` |
| 🦊 | **[View DMs anonymously](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[View live anonymously](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[View stories anonymously](https://gitlab.com/crimera/piko)** |  | `android` |
| 🦊 | **[View story mentions](https://gitlab.com/crimera/piko)** | Add option to view visible and hidden story mentions. | `android` |
| ⚙️ | **[Abstract shim layer](https://gitlab.com/inotia00/x-shim)** | Adds an abstracted shim layer for fields, which improves compatibility to allow legacy patches to work. | `android` |
| ⚙️ | **[Abstract shim layer for method](https://gitlab.com/inotia00/x-shim)** | Adds an abstracted shim layer for methods, which improves compatibility to allow legacy patches to work. | `android` |
| ⚙️ | **[Abstract shim layer for native library](https://gitlab.com/inotia00/x-shim)** | Adds an abstracted shim layer for native libraries, which improves compatibility to allow legacy patches to work. | `android` |
| 🛡️ | **[AMOLED dark theme](https://gitlab.com/rushiranpise/morphe-patches)** | Makes Google Photos dark surfaces true black. | `photos` |
| 🛡️ | **[Alert Distances](https://gitlab.com/rushiranpise/morphe-patches)** | Configures radar/camera and hazard alert announcement distances. Credits: Waze CGE Mod.  | `waze` |
| 🛡️ | **[AutoZoom](https://gitlab.com/rushiranpise/morphe-patches)** | Controls how aggressively the map zooms in/out based on driving speed. Credits: Waze Chuppito Mod | `waze` |
| 🛡️ | **[Bypass License Check](https://gitlab.com/rushiranpise/morphe-patches)** | Bypasses PairIP DRM license verification to prevent forced app shutdown on non-Play-licensed installs. | `crimeradar` |
| 🛡️ | **[Bypass Subscription Paywall](https://gitlab.com/rushiranpise/morphe-patches)** | Bypasses the subscription paywall in-app. | `crimeradar` |
| 🛡️ | **[Bypass developer verification](https://gitlab.com/rushiranpise/morphe-patches)** | Forces all APK install verification sessions to be bypassed, preventing the verifier from blocking sideloaded or unsigned apps on Android 16+ devices.Important: Requires pushing the patched APK as a system app replacement (e.g. via Magisk module or ADB with root)since the original holds DEVELOPER_VERIFICATION_AGENT permission. ADB installs are exempt from verification regardless. | `verifier` |
| 🛡️ | **[Change package name](https://gitlab.com/rushiranpise/morphe-patches)** | Installs Google Photos beside the system Photos app by changing package, permissions, providers, and app name. | `photos` |
| 🛡️ | **[Change version code](https://gitlab.com/rushiranpise/morphe-patches)** | Changes android:versionCode. | Any |
| 🛡️ | **[Dark mode](https://gitlab.com/rushiranpise/morphe-patches)** | Force dark mode for Amazon Shopping. | `shopping`, `shopping` |
| 🛡️ | **[Disable Ads](https://gitlab.com/rushiranpise/morphe-patches)** | Prevents the AppOpen ad preloader from initialising. | `control` |
| 🛡️ | **[Disable Ads](https://gitlab.com/rushiranpise/morphe-patches)** | Suppresses all Waze ad systems via bundled preferences file: • AdMob SDK (Ad_.*) • Google Ads (Google_Ads.*) • Ads Inventory Prediction • ExternalPOI pins, coupons, popups (ExternalPO_ + Extern__POI both key variants) • Search autocomplete server ads Credits: Waze CGE Mod (ExternalPOI keys), Waze Chuppito (dual-key coverage). | `waze` |
| 🛡️ | **[Disable Advil Ad Requests](https://gitlab.com/rushiranpise/morphe-patches)** | Stubs AdvilRequest.getPageUrl() → "" so the Advil ad server receives no page URL and returns no ad content.  | `waze` |
| 🛡️ | **[Disable Analytics / Telemetry](https://gitlab.com/rushiranpise/morphe-patches)** | Disables App Analytics / Telemetry. | `onedotonedotonedotone` |
| 🛡️ | **[Disable Tracking](https://gitlab.com/rushiranpise/morphe-patches)** | Disables analytics and telemetry in ES File Explorer | `pop` |
| 🛡️ | **[Disable ad SDK calls](https://gitlab.com/rushiranpise/morphe-patches)** | No-ops common ad SDK load/show/init/fetch methods in bundled ad packages. | Any |
| 🛡️ | **[Disable clipboard access](https://gitlab.com/rushiranpise/morphe-patches)** | Blocks app clipboard reads and writes. | Any |
| 🛡️ | **[Disable search suggestions tracking](https://gitlab.com/rushiranpise/morphe-patches)** | Prevents search keypress and focus events from being sent with suggestion requests. | `shopping`, `shopping` |
| 🛡️ | **[Disable shake ads](https://gitlab.com/rushiranpise/morphe-patches)** | Skips SensorManager.registerListener calls that can power shake-to-ad behavior. | Any |
| 🛡️ | **[Disable telemetry](https://gitlab.com/rushiranpise/morphe-patches)** | Disables CamScanner's custom telemetry/log-agent system. | `camscanner` |
| 🛡️ | **[Disable video autoplay](https://gitlab.com/rushiranpise/morphe-patches)** | Prevents product and ad videos from autoplaying. | `shopping`, `shopping` |
| 🛡️ | **[Enable Android debugging](https://gitlab.com/rushiranpise/morphe-patches)** | Sets android:debuggable=true. | Any |
| 🛡️ | **[Enable DCIM folders backup control](https://gitlab.com/rushiranpise/morphe-patches)** | Allows controlling Camera and other DCIM folder backup individually. | `photos` |
| 🛡️ | **[Enable Debug Menu](https://gitlab.com/rushiranpise/morphe-patches)** | Enables Duolingo's hidden debug menu in settings. | `duolingo` |
| 🛡️ | **[Enable ROM signature spoofing](https://gitlab.com/rushiranpise/morphe-patches)** | Adds fake-signature permission and metadata. | Any |
| 🛡️ | **[Enable debug build target](https://gitlab.com/rushiranpise/morphe-patches)** | Forces compatible BUILD_TARGET debug providers to debug=true. | Any |
| 🛡️ | **[Enlarged Speedometer](https://gitlab.com/rushiranpise/morphe-patches)** | Increases speedometer digit size for better readability. | `waze` |
| 🛡️ | **[Export all activities](https://gitlab.com/rushiranpise/morphe-patches)** | Makes all activities exportable. | Any |
| 🛡️ | **[Export internal data documents provider](https://gitlab.com/rushiranpise/morphe-patches)** | Registers an extension DocumentsProvider for the app internal data directory. | Any |
| 🛡️ | **[Fix Amazon manifest conflicts](https://gitlab.com/rushiranpise/morphe-patches)** | Updates shared Amazon permissions so other Amazon apps can coexist. | `shopping`, `shopping` |
| 🛡️ | **[Fix DCIM folder classification](https://gitlab.com/rushiranpise/morphe-patches)** | Prevents non-Camera DCIM folders from being grouped as Camera. | `photos` |
| 🛡️ | **[Fix Firebase after re-signing](https://gitlab.com/rushiranpise/morphe-patches)** | Fixes Firebase services (push notifications, Remote Config, Firebase Auth) that break after Morphe re-signs the app with a different certificate.  Apply with Original app certificate patch no other config needed. | Any |
| 🛡️ | **[Force dark theme](https://gitlab.com/rushiranpise/morphe-patches)** | Forces common AppCompat, UiModeManager, and Configuration dark-mode checks to night mode. | Any |
| 🛡️ | **[GmsCore support](https://gitlab.com/rushiranpise/morphe-patches)** | Adds MicroG/GmsCore support metadata for Google Photos. | `photos` |
| 🛡️ | **[GmsCore support (MicroG)](https://gitlab.com/rushiranpise/morphe-patches)** | Routes Google Play Services calls through MicroG instead of real GPS.  Works for: Google apps (YouTube, Maps, News, Photos) and third-party apps using classic Google Sign-In (Android 13 and below).  Does not work for: Android 14+ Credential Manager sign-in (most modern third-party apps), Play Integrity / SafetyNet checks, or apps with custom auth.  Requires MicroG RE installed. Apply with Original app certificate patch. | Any |
| 🛡️ | **[Hide ADB status](https://gitlab.com/rushiranpise/morphe-patches)** | Hides adb_enabled and development_settings_enabled. | Any |
| 🛡️ | **[Hide Rufus tab](https://gitlab.com/rushiranpise/morphe-patches)** | Removes the Rufus AI assistant tab from Amazon's bottom navigation bar. | `shopping`, `shopping` |
| 🛡️ | **[Hide VPN and proxy](https://gitlab.com/rushiranpise/morphe-patches)** | Hides common VPN transport/interface and Java proxy property checks. | Any |
| 🛡️ | **[Hide app icon](https://gitlab.com/rushiranpise/morphe-patches)** | Removes launcher category from MAIN launcher filters. | Any |
| 🛡️ | **[Hide mock location](https://gitlab.com/rushiranpise/morphe-patches)** | Hides mock-location signals from app checks. | Any |
| 🛡️ | **[Map Skin (Vitamin C)](https://gitlab.com/rushiranpise/morphe-patches)** | Applies Chuppito's 'Vitamin C' map skin. All visual values configurable. • Night: true black AMOLED background (saves battery, prevents burn-in) • Day: warm beige background • Larger font labels across the board • Wider navigation arrow head for better visibility • Custom car 3D models: Batmobile, Riddler, race car, 3D arrow Credits: ALEX02-GTT (skin design), Waze Chuppito Mod (integration). | `waze` |
| 🛡️ | **[Navigation & Map](https://gitlab.com/rushiranpise/morphe-patches)** | Configures navigation and map behaviour: • Nearing destination distance (Credits: CGE Mod) • Android Auto head-up alert distances • Map turn mode (auto-zoom to upcoming turn) • Traffic bar minimum time threshold • GPS icon visibility • Route notifications (hazard, school zone) both disabled by default Credits: Waze CGE Mod (nearing destination), Waze Chuppito (remaining keys). | `waze` |
| 🛡️ | **[Open links in browser](https://gitlab.com/rushiranpise/morphe-patches)** | Opens non-Amazon URLs in the default browser instead of the in-app WebView. | `shopping`, `shopping` |
| 🛡️ | **[Override certificate pinning](https://gitlab.com/rushiranpise/morphe-patches)** | Forces network security config trust anchors to override pins. | Any |
| 🛡️ | **[Popup Suppression](https://gitlab.com/rushiranpise/morphe-patches)** | Prevents promotional and ad popups from appearing while driving. Raises the minimum trigger speed to a near-impossible value so popups never appear. Credits: Waze Chuppito Mod. | `waze` |
| 🛡️ | **[Predictive back gesture](https://gitlab.com/rushiranpise/morphe-patches)** | Enables Android predictive back gesture. | Any |
| 🛡️ | **[Price history charts](https://gitlab.com/rushiranpise/morphe-patches)** | Injects Keepa and CamelCamelCamel price history charts on Amazon product pages. | `shopping`, `shopping` |
| 🛡️ | **[Provide Original app certificate](https://gitlab.com/rushiranpise/morphe-patches)** | By Default it Reads the signing certificate from the original app installed. Required for GmsCore, Firebase, and Signature spoof patches. Only fill options below if the original is uninstalled. | Any |
| 🛡️ | **[Radar Sound (Any Speed)](https://gitlab.com/rushiranpise/morphe-patches)** | Plays radar/speed camera sound alerts regardless of current speed. Official Waze only alerts when over the speed limit.  | `waze` |
| 🛡️ | **[Remove ADS](https://gitlab.com/rushiranpise/morphe-patches)** | Remove in-app ads | `google` |
| 🛡️ | **[Remove Ads](https://gitlab.com/rushiranpise/morphe-patches)** | Removes all ads in app | `flud` |
| 🛡️ | **[Remove Ads](https://gitlab.com/rushiranpise/morphe-patches)** | Removes interstitial and exit native ads from m-Indicator. | `mindicator` |
| 🛡️ | **[Remove Ads](https://gitlab.com/rushiranpise/morphe-patches)** | Removes ads from TorrDroid. | `torrdroid` |
| 🛡️ | **[Remove Ads](https://gitlab.com/rushiranpise/morphe-patches)** | Remove in-app ads. | `android` |
| 🛡️ | **[Remove Ads / Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Forces SubscriptionStateImpl.getStatus() (LB2/c.h) to always return HAS_UNLIMITED_SUBSCRIPTION and getPurchase() (LB2/c.g) to return a well-formed fake Purchase, removing ads and the upgrade button/banner without crashing on the now-expected non-null Purchase object. | `subscription` |
| 🛡️ | **[Remove Item Limits](https://gitlab.com/rushiranpise/morphe-patches)** | Removes all  item limits in-app. | `crimeradar` |
| 🛡️ | **[Remove Watermark](https://gitlab.com/rushiranpise/morphe-patches)** | Removes watermarks from Canva exports and previews. | `editor` |
| 🛡️ | **[Remove ad manifest entries](https://gitlab.com/rushiranpise/morphe-patches)** | Removes common ad SDK permissions, services, providers, libraries, and metadata. | Any |
| 🛡️ | **[Remove ads](https://gitlab.com/rushiranpise/morphe-patches)** | Stubs all ad loading paths: banner/interstitial loaders, billing callbacks, and ad SDK init. | `aida64` |
| 🛡️ | **[Remove ads](https://gitlab.com/rushiranpise/morphe-patches)** | Hides sponsored and ad content in Amazon Shopping via CSS injection. | `shopping`, `shopping` |
| 🛡️ | **[Remove ads](https://gitlab.com/rushiranpise/morphe-patches)** | Disables Block Puzzle AdMob initialization, banner, and interstitial ads. | `blockpuzzle` |
| 🛡️ | **[Remove ads](https://gitlab.com/rushiranpise/morphe-patches)** | Disables interstitial/banner ad loaders, hides promoted listings and profiles from search feeds. | `Carousell` |
| 🛡️ | **[Remove ads](https://gitlab.com/rushiranpise/morphe-patches)** | Disables LiveScore banner, native, and interstitial ad requests. | `livescore` |
| 🛡️ | **[Remove share targets](https://gitlab.com/rushiranpise/morphe-patches)** | Removes chooser/direct share targets. | Any |
| 🛡️ | **[Report Speed Limit](https://gitlab.com/rushiranpise/morphe-patches)** | Adds a Report option when tapping the speedometer to report wrong or missing speed limits. Not available in the official version.  | `waze` |
| 🛡️ | **[Sanitize share links](https://gitlab.com/rushiranpise/morphe-patches)** | Strips tracking parameters from copied/shared Amazon links, leaving only the clean product URL. | `shopping`, `shopping` |
| 🛡️ | **[Set target SDK 34](https://gitlab.com/rushiranpise/morphe-patches)** | Sets targetSdkVersion to 34. | Any |
| 🛡️ | **[Speed Limit Sign](https://gitlab.com/rushiranpise/morphe-patches)** | Sets the speed limit sign style shown on the map. | `waze` |
| 🛡️ | **[Spoof Android ID](https://gitlab.com/rushiranpise/morphe-patches)** | Spoofs Settings.Secure android_id reads. | Any |
| 🛡️ | **[Spoof Bluetooth identifiers](https://gitlab.com/rushiranpise/morphe-patches)** | Spoofs Bluetooth adapter name and MAC address reads. | Any |
| 🛡️ | **[Spoof Pixel device](https://gitlab.com/rushiranpise/morphe-patches)** | Ports PixelSpoof-style Build, system property, and Pixel feature spoofing. | Any |
| 🛡️ | **[Spoof Play age signals](https://gitlab.com/rushiranpise/morphe-patches)** | Spoofs Play age signal result getters. | Any |
| 🛡️ | **[Spoof SIM provider](https://gitlab.com/rushiranpise/morphe-patches)** | Spoofs TelephonyManager SIM/network provider values. | Any |
| 🛡️ | **[Spoof WARP+ Unlimited UI](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks WARP+ UI locally. | `onedotonedotonedotone` |
| 🛡️ | **[Spoof Wi-Fi connection](https://gitlab.com/rushiranpise/morphe-patches)** | Forces common connectivity checks to connected/unmetered. | Any |
| 🛡️ | **[Spoof Wi-Fi identifiers](https://gitlab.com/rushiranpise/morphe-patches)** | Spoofs Wi-Fi SSID, BSSID, and MAC address reads. | Any |
| 🛡️ | **[Spoof Widevine / DRM level](https://gitlab.com/rushiranpise/morphe-patches)** | Reports Widevine L1 (hardware DRM) to apps that check DRM level locally.  Useful for apps that refuse to play HD/4K content on L3 devices or after re-signing.  Does not bypass server-side DRM - Netflix, Disney+ and similar are not affected. | Any |
| 🛡️ | **[Spoof app signature](https://gitlab.com/rushiranpise/morphe-patches)** | Makes the app think its signing certificate is unchanged after Morphe re-signs it.  Useful when an app crashes or shows a tamper warning because it checks its own certificate.  Does not bypass Play Integrity / SafetyNet hardware attestation.  Apply with Original app certificate patch. | Any |
| 🛡️ | **[Spoof build info](https://gitlab.com/rushiranpise/morphe-patches)** | Spoofs common android.os.Build fields with configurable values. | Any |
| 🛡️ | **[Spoof features](https://gitlab.com/rushiranpise/morphe-patches)** | Spoofs selectable Pixel Photos build and feature flags. | `photos` |
| 🛡️ | **[Spoof install source](https://gitlab.com/rushiranpise/morphe-patches)** | Makes the app think it was installed from a specific store (default: Google Play).  Useful when an app blocks features or shows errors because it detects it was not installed from the Play Store.  Only affects what the app itself sees - does not change the real system install record. | Any |
| 🛡️ | **[Spoof keystore security level](https://gitlab.com/rushiranpise/morphe-patches)** | Forces key/security level getters to software/trusted-environment style values. | Any |
| 🛡️ | **[Spoof root of trust](https://gitlab.com/rushiranpise/morphe-patches)** | Spoofs common RootOfTrust verified boot getters. | Any |
| 🛡️ | **[Spoof telephony IDs](https://gitlab.com/rushiranpise/morphe-patches)** | Spoofs IMEI, MEID, subscriber ID, SIM serial, and line number reads. | Any |
| 🛡️ | **[Suppress Paywall](https://gitlab.com/rushiranpise/morphe-patches)** | Suppresses the in-app paywall. | `control` |
| 🛡️ | **[Suppress Premium Promotions](https://gitlab.com/rushiranpise/morphe-patches)** | Supress all premium promotions in-app. | `crimeradar` |
| 🛡️ | **[Uncensored Radar / Camera Display](https://gitlab.com/rushiranpise/morphe-patches)** | Shows exact fixed and mobile speed camera locations, including those not yet in the official Waze radar zone. Enables enforcement alerts via preferences keys: Credits: Waze CGE Mod. | `waze` |
| 🛡️ | **[Unlock Ad-Free](https://gitlab.com/rushiranpise/morphe-patches)** | Forces FlightAware ad-free subscribed state. | `liveFlightTracker` |
| 🛡️ | **[Unlock Ad-Free](https://gitlab.com/rushiranpise/morphe-patches)** | Removes ads and unlocks ad-free status in Speedtest by Ookla. | `speedtest` |
| 🛡️ | **[Unlock All Access](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks All access in Nzb360. | `nzb360` |
| 🛡️ | **[Unlock All Features](https://gitlab.com/rushiranpise/morphe-patches)** | Bypasses PairIP DRM license check, removes all paywalls, and unlocks all premium features including cloud sync and remote access. | `pialytic` |
| 🛡️ | **[Unlock Business Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Business/Gold premium features in Flightradar24: ad-free map, weather layers, ATC, 3D view, flight history, and unlimited saved locations. | `flightradar24free` |
| 🛡️ | **[Unlock Cloud Service](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks BluramsGuard cloud storage, AI detection, and playback features. | `ipc` |
| 🛡️ | **[Unlock Club](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Citymapper Club Membership Note: Need to manually Purchase inside APP!. | `release` |
| 🛡️ | **[Unlock Donation Features](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium donation features in Greenify. | `greenify` |
| 🛡️ | **[Unlock Drama Episodes](https://gitlab.com/rushiranpise/morphe-patches)** | Bypasses the IAA (ad-watch-to-unlock) episode gate for drama mini-series. | `scoops` |
| 🛡️ | **[Unlock Elite](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks JEFIT Elite features in app. | `fit` |
| 🛡️ | **[Unlock Enterprise](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Enterprise features in app. | `MigraConnect` |
| 🛡️ | **[Unlock Excel](https://gitlab.com/rushiranpise/morphe-patches)** | Removes login requirement, unlocks premium, blocks ads, bypasses signature and code transparency checks. | `excel` |
| 🛡️ | **[Unlock Followed Locations](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks the Followed Locations premium feature. | `crimeradar` |
| 🛡️ | **[Unlock Full Version](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all features in Inure App Manager. | `play` |
| 🛡️ | **[Unlock Gold](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Kahoot! Plus Gold features in app. | `android` |
| 🛡️ | **[Unlock Lifetime](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks lifetime subscription features in BlockerHero. | `blockerhero` |
| 🛡️ | **[Unlock Lifetime](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all Lifetime features in Proxyman. | `proxymanandroid` |
| 🛡️ | **[Unlock Lifetime](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks SHAREit lifetime premium. | `premium` |
| 🛡️ | **[Unlock Lifetime Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all features locked behind the subscription paywall. | `android` |
| 🛡️ | **[Unlock Moovit+](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Moovit+ | `tranzmate` |
| 🛡️ | **[Unlock PRO](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all PRO features in app | `pixelhabittracker` |
| 🛡️ | **[Unlock Patron](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Pocket Casts Patron yearly feature checks. | `pocketcasts` |
| 🛡️ | **[Unlock Platinum](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Life360 Platinum feature in app. | `safetymapd` |
| 🛡️ | **[Unlock Plus](https://gitlab.com/rushiranpise/morphe-patches)** | Forces Clue Plus subscription active, unlocking all premium features. | `android` |
| 🛡️ | **[Unlock Plus](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all SpotAngels Plus features in app | `android` |
| 🛡️ | **[Unlock Plus](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Sticker.ly PLUS subscriptionNote: For Facebook Login, Uninstall Facebook App. | `android` |
| 🛡️ | **[Unlock Plus](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Subway Now Plus. | `theweekendest` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features in app. | `manager` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks AiScore Premium Features in app. | `score` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium. | `pdfviewer` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium wallpapers. | `wallpaper` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock Premium Features in app. | `blurwallpaper` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Premium Features In the App. | `callrecorder` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Carbon premium subscription. | `nutrition` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks ColorNote premium and removes advertising ID permissions. | `note` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium features in Countdown Widget | `countdown` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features in app. | `cpu_z` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Premium Features In the App. | `crimeradar` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features after login. | `eterno` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium wallpapers. | `wallpaper` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all Fitbod premium features. | `fitbod` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features in app. | `tracker` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock Premium features in app. | `dayhistory` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** |  | `play` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium features in Image & Video Date Fixer. | `imagedatefixer` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock Premium features after login. | `kinemasterfree` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features and all map packs. | `android` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features in app. | `larkplayer` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Premium Features in app. | `lawfully_ai_tracker` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Premium features in app after login. | `mapy` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock all premium widgets. | `widgets` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium in Beta by Mirko. | `beta` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks MyRadar's yearly premium features | `myradar` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium features. | `netmonster` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Premium features in app.. | `newsbreak` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Ninja VPN premium. | `android` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features after login. | `portable` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all Photo Editor premium features | `editor` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Picture Mushroom premium features. | `picturemushroom` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks PictureThis premium features. | `xingseus` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Pocket Prep premium subscription gates. | `itcybersecurity` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks local Proton VPN premium  features. | `android` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock premium features in RecipeBro. | `cookingbuddy` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium features in Rename & Organize. | `picturemanager` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Rocket Money Premium Features. | `truebill` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features in app. | `filemanager` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Bypasses PairIP license check, paywall, ads, and pro upsell in SAI. | `sai` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium feature in app. | `scrl` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all Premium features in Snipd: AI Podcast Player by spoofing the RevenueCat CustomerInfo. | `podcastdiscovery` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Premium features. | `snowforecast` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Social Gamebox premium features. | `social_gamebox` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Sticker Maker premium and ad-free checks. | `stickermakerforwhatsapp` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Premium features in app. Also re-enables password login after OTP. | `strava` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium/lifetime featuers in app. | `explorer` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks The Weather Channel's Premium and Premium Pro subscription tiers. Enables the ad-free experience, extended 15-day hourly forecast, real-feel temperature, air quality index, minute-by-minute precipitation, severe weather notifications, and radar overlays gated behind the subscription paywall. | `Weather` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium features. | `weather` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks TomTom GO premium features for the selected vehicle type. | `navapp` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Toxly Premium | `scanner` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock premium features in app. | `tradingviewapp` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Premium Features In the App. | `control` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all Wavve Boating GPS premium features: charts, weather, tide data, and removes subscription paywall. | `gps` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Windscribe premium account. | `vpn` |
| 🛡️ | **[Unlock Premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Windy Pro features. | `android` |
| 🛡️ | **[Unlock Premium ](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium in Clickmate | `autoclicker` |
| 🛡️ | **[Unlock Premium+](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks AccuWeather's Premium+ subscription tier without a Play Store purchase. Enables the full 15-day and hourly forecast detail, MinuteCast extended precision, air quality and health indexes, real-feel temperature, severe weather notifications, and widget customisation. | `android` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Box Box Pro | `android` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all premium features in Case Tracker — Immigration. | `casetracker` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock Pro Features in Cashew App | `tracker_app` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all Citizen Plus/Protect features: Safety Network, Safety Center, Zones, Live Agent, Offender alerts, Clarity crime map, incident video, and more. | `citizen` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all pro features in Hibernator. | `hibernator` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock Pro Features in app. | `inmigreat` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all pro features in KillApps. | `killall` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all Pro features. | `app` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all pro features in ML Manager. | `mlmanager` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all Pro features in app. | `myperm` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all pro features in NetGuard. | `netguard` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Pro features in app. | `mikrotik` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks 1Tap Cleaner PRO: history export, app-group filters, unlimited cache targets, ad removal. | `free` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Pro Features in app. | `pro` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features in app. | `citizen` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Removes ads and unlocks the no-ads subscription in RAR. | `rar` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all Pro features in app. | `permissionmanager` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Splitwise Pro features, removes ad banners, and suppresses all upgrade upsell prompts. | `SplitwiseMobile` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks UbikiTouch Pro features in app. | `ubktouch` |
| 🛡️ | **[Unlock Pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks UDisc Pro subscription. | `udisc` |
| 🛡️ | **[Unlock Pro / No Ads](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Pro/No Ads feature in app | `trackchecker_mobile` |
| 🛡️ | **[Unlock Pro features](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock Pro features in app. | `free` |
| 🛡️ | **[Unlock Professional](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Professional features inapp. | `alphapro` |
| 🛡️ | **[Unlock Royale](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Transit Royale Membership. | `droid` |
| 🛡️ | **[Unlock SPIN Plus](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks SPIN Plus | `spinbrowser` |
| 🛡️ | **[Unlock SVIP](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks SViP features in app. | `faceshow` |
| 🛡️ | **[Unlock Subscription](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks user-selectable Duolingo subscription tiers. | `duolingo` |
| 🛡️ | **[Unlock Subscription](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all subscription features in TWT App. | `twtapp` |
| 🛡️ | **[Unlock Turbo](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Turbo subscription after login. | `uptodown` |
| 🛡️ | **[Unlock Ultimate](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Ultimate Ad-Free + Android TV. | `prod` |
| 🛡️ | **[Unlock Ultra](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Ultra features in app. | `free` |
| 🛡️ | **[Unlock VIP](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock ViP features in app. | `juggle` |
| 🛡️ | **[Unlock VIP](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Dubox Drive VIP/SVIP (Premium+) | `drive` |
| 🛡️ | **[Unlock VIP](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks VIP features in app. | `oneroom`, `in` |
| 🛡️ | **[Unlock VIP](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks VIP Features in app. | `tv` |
| 🛡️ | **[Unlock VIP](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock VIP subscription in app. | `videoplayer` |
| 🛡️ | **[Unlock VIP](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks Yatri VIP by forcing active plan status and spoofing active plan DB query. | `yatri` |
| 🛡️ | **[Unlock VIP (Lifetime)](https://gitlab.com/rushiranpise/morphe-patches)** | Forces permanent professional VIP tier, removes ads and upgrade popups, bypasses PairIP. | `mock` |
| 🛡️ | **[Unlock VIP Lifetime](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock Vip Features in APP. | `pop` |
| 🛡️ | **[Unlock Word](https://gitlab.com/rushiranpise/morphe-patches)** | Removes login requirement, unlocks premium, blocks ads, bypasses signature and code transparency checks. | `word` |
| 🛡️ | **[Unlock donation](https://gitlab.com/rushiranpise/morphe-patches)** | Forces h0() to return "yes" so donate dialog never shows and providers unlock. | `weawow` |
| 🛡️ | **[Unlock premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks AmoledPix premium features and disables ads. | `amoledpix` |
| 🛡️ | **[Unlock premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks NAVITIME Japan Travel Premium features in app | `walk` |
| 🛡️ | **[Unlock premium](https://gitlab.com/rushiranpise/morphe-patches)** | Unlock Premium features in app | `RPGSoundSystem` |
| 🛡️ | **[Unlock pro](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks all pro features. | `kinestop` |
| 🛡️ | **[Unlock subscription](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks subscription in app | `crossword` |
| 🛡️ | **[Yearly Unlock](https://gitlab.com/rushiranpise/morphe-patches)** | Unlocks premium features without login. Note: Login Won't Work | `camscanner` |
| 🔥 | **[Anti-delete messages](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Prevents deleted messages from being removed locally. | `plus` |
| 🔥 | **[Anti-delete messages](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Prevents deleted messages from being removed locally. | `web` |
| 🔥 | **[Anti-disappearing media](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Keeps view-once and self-destructing media viewable forever. | `plus` |
| 🔥 | **[Anti-disappearing media](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Keeps view-once and self-destructing media viewable forever. | `web` |
| 🔥 | **[Anti-screenshot notification](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Blocks screenshot notifications from being sent to the other user. | `plus` |
| 🔥 | **[Bypass channel restrictions](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Allows copying text, saving media, and opening blocked channels. Forwarding is server-side blocked and won't work. | `plus` |
| 🔥 | **[Bypass channel restrictions](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Allows opening copyrighted, sensitive, and temporarily disabled channels. | `web` |
| 🔥 | **[Bypass content restrictions](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Allows saving from restricted channels. | `web` |
| 🔥 | **[Bypass integrity](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Bypasses integrity check to allow login on patched app. | `plus` |
| 🔥 | **[Bypass integrity](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Bypasses integrity check to allow login on patched app. | `web` |
| 🔥 | **[Bypass signature check](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Bypasses app signature verification to allow API access. | `hotstar` |
| 🔥 | **[CREX Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features and removes ads. | `cricketexchange` |
| 🔥 | **[Cricbuzz Disable Ads](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Removes all ads including banner, interstitial, video, and app open ads. | `android` |
| 🔥 | **[Cricbuzz Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features like live streaming and premium articles. | `android` |
| 🔥 | **[Disable analytics](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Blocks all analytics and tracking. | `plus` |
| 🔥 | **[Disable auto update](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Disables automatic app update checks. | `plus` |
| 🔥 | **[Disable auto update](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Disables automatic app update checks. | `web` |
| 🔥 | **[Disable telemetry](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Blocks all telemetry, analytics, and observability data collection. | `android` |
| 🔥 | **[Disable telemetry](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Disables AppStartTracker and other telemetry points. | `truecaller` |
| 🔥 | **[Disable update check](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Disables the in-app update check. | `truecaller` |
| 🔥 | **[Doc Scanner Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks all premium features, removes ads, and enables pro themes. | `docscanner` |
| 🔥 | **[Download speed boost](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Increases download chunk size and max concurrent requests. | `web` |
| 🔥 | **[Enable all codecs](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Enables all video codecs (H265, VP9, AV1) and 4K resolution by bypassing blacklist and capability checks. | `hotstar` |
| 🔥 | **[Enable screen mirroring](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Allows playback while screen mirroring or HDMI is connected. | `hotstar` |
| 🔥 | **[Enable screenshots](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Removes screenshot and screen recording restrictions. | `hotstar` |
| 🔥 | **[Eyecon Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features. | `global` |
| 🔥 | **[Fing Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium network tools and features. | `fing` |
| 🔥 | **[Force HDR10](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Forces HDR10 and HDR10+ playback on compatible devices by bypassing blacklist and capability checks. | `hotstar` |
| 🔥 | **[GMS sign-in bypass](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Forces SMS-based OTP verification instead of GMS SmsRetriever, fixing sign-in on re-signed APKs. | `truecaller` |
| 🔥 | **[Hide Assistant tab](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Hides the Assistant tab from the bottom navigation bar. | `truecaller` |
| 🔥 | **[Hide Family Protection button](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Hides the Family Protection button from the bottom navigation bar. | `truecaller` |
| 🔥 | **[Hide Premium from settings](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Hides the Premium options from the settings and user details pages. | `truecaller` |
| 🔥 | **[Hide Premium tab](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Hides the Premium tab from the bottom navigation bar. | `truecaller` |
| 🔥 | **[Hide Scams tab](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Hides the Scams tab from the bottom navigation bar. | `truecaller` |
| 🔥 | **[Hide typing indicator](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Prevents typing status from being sent to other users. | `plus` |
| 🔥 | **[Hide typing indicator](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Hides your typing indicator from other users. | `web` |
| 🔥 | **[Lumina Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks all premium wallpapers and categories. | `wallpapers` |
| 🔥 | **[MX Player Pro License](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Bypasses license verification and signature checks in MX Player Pro. | `pro` |
| 🔥 | **[MacroDroid Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features and removes macro limits. | `macrodroid` |
| 🔥 | **[Mark Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features and removes ads. | `ss_app` |
| 🔥 | **[Neutralize third-party SDKs](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Disables telemetry, ad, and tracking SDK initializations. Fixes #84. | `truecaller` |
| 🔥 | **[Plus Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium feature UI and shows premium badge on self only. | `plus` |
| 🔥 | **[Premium unlock](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium UI features, removes subscription nudges, and enables downloads. | `hotstar` |
| 🔥 | **[Proton VPN Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium UI features: removes upsells, enables NetShield ad-blocker, hides upgrade prompts, shows free servers with premium interface (Plus badge, no speed limits display, all feature flags enabled). | `android` |
| 🔥 | **[Remove ads](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Removes pre-roll, mid-roll, and live match video ads. | `hotstar` |
| 🔥 | **[Remove ads](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Removes all ads including Plus banner ads and Telegram sponsored messages. | `plus` |
| 🔥 | **[Remove ads](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Removes sponsored messages and video ads. | `web` |
| 🔥 | **[StarSense Unlock](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Bypasses the unlock code check to enable all features. | `skybox` |
| 🔥 | **[Telegram Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features. | `web` |
| 🔥 | **[Teleprompter Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features in Teleprompter Vlog & Scripts app. | `teleprompter` |
| 🔥 | **[TickTick Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features, removes limits, and enables AI tools. | `task` |
| 🔥 | **[TrackIt Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features. | `trackit` |
| 🔥 | **[Truecaller Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features. | `truecaller` |
| 🔥 | **[Unlock Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks all premium missions — Lights On, Step & Walk Off, Push-Up, Squats, Jumping Jack, and Wake Up check. | `missionalarm` |
| 🔥 | **[Unlock Pro](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks SD Maid SE Pro features — full history, scheduled operations, extra options, custom rules. | `sdmse` |
| 🔥 | **[Unlock Pro](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks Pro features — auto refresh, advanced process management, and all settings. | `taskmanager` |
| 🔥 | **[VN Premium](https://gitlab.com/Paresh-Maheshwari/paresh-patches)** | Unlocks premium features, removes watermark, and hides Pro tab. | `vlog` |
| 💎 | **[AMOLED dark theme](https://gitlab.com/hoo-dles/morphe-patches)** | Changes the default dark theme to use true blacks for AMOLED screens. | `android` |
| 💎 | **[AMOLED dark theme](https://gitlab.com/hoo-dles/morphe-patches)** | Changes the default dark theme to use true blacks for AMOLED screens. | `android` |
| 💎 | **[Block Permissions Request](https://gitlab.com/hoo-dles/morphe-patches)** | Blocks the request of notification permissions on load of app. | `lingory` |
| 💎 | **[Change package name](https://gitlab.com/hoo-dles/morphe-patches)** | Appends ".morphe" to the package name by default. Changing the package name of the app can lead to unexpected issues. | Any |
| 💎 | **[Disable Pairip license check](https://gitlab.com/hoo-dles/morphe-patches)** | Disables Play Integrity API (pairip) client-side license check. This patch does not bypass Play Integrity attestation or pairipcore virtualization. | Any |
| 💎 | **[Disable ads](https://gitlab.com/hoo-dles/morphe-patches)** | Disables all ads contained within the UI. | `goodreads` |
| 💎 | **[Disable ads](https://gitlab.com/hoo-dles/morphe-patches)** | Disables ads during audio streaming. | `android` |
| 💎 | **[Disable ads](https://gitlab.com/hoo-dles/morphe-patches)** | Disables all ads contained within the UI. | `results` |
| 💎 | **[Disable anti-tamper](https://gitlab.com/hoo-dles/morphe-patches)** | Disables various anti-tamper checks that causes the app to force-close. | `moffice_eng` |
| 💎 | **[Disable dynamic app icon](https://gitlab.com/hoo-dles/morphe-patches)** | Prevents Duolingo from changing the app icon. Only the default icon will be available. | `duolingo` |
| 💎 | **[Disable signature check](https://gitlab.com/hoo-dles/morphe-patches)** | Removes the anti-tamper protection, which verifies apk signature, causing the app to force close. | `flowerfree` |
| 💎 | **[Disable telemetry](https://gitlab.com/hoo-dles/morphe-patches)** | Disables CamScanner's custom telemetry system. | `camscanner` |
| 💎 | **[Disable telemetry](https://gitlab.com/hoo-dles/morphe-patches)** | Disables event logging sent to the app's custom endpoint. | `vrd` |
| 💎 | **[Disable telemetry](https://gitlab.com/hoo-dles/morphe-patches)** | Disables SoundCloud's telemetry system. | `android` |
| 💎 | **[Disable telemetry](https://gitlab.com/hoo-dles/morphe-patches)** | Blocks SuperChinese's custom telemetry reporting. | `superchinese` |
| 💎 | **[Enable FotMob+](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `wc2010` |
| 💎 | **[Enable Niagara Pro](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `launcher` |
| 💎 | **[Enable Peak membership](https://gitlab.com/hoo-dles/morphe-patches)** | Enables some app features locked behind the subscription paywall. Not all premium functionality is available. | `alltrails` |
| 💎 | **[Enable Plus](https://gitlab.com/hoo-dles/morphe-patches)** | Enable Plus membership (not all features are available). There is a strict version requirement for this patch. | `mycake` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `android` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `avocards` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `enc` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables some app features locked behind the subscription paywall. Certain server-side functionality may be unavailable. | `camscanner` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `dailypay` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `duolingo` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `eggconvo` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `guessthecountry` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `hellochinese` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `hypertrophy` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. There is a strict version requirement for this patch and only arm64-v8a devices are supported. | `lingory` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `lyfta` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | REQUIRES ROOT MOUNT INSTALL! Enables app features locked behind the subscription paywall. | `diet`, `train` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `podcastaddict` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `pydroid3` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `showly2` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `sleep` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `app` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `teuida` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. There is a strict version requirement for this patch. | `android` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `ventusky` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `wallpaper` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `merriamwebster` |
| 💎 | **[Enable Premium](https://gitlab.com/hoo-dles/morphe-patches)** | Enables some app features locked behind the subscription paywall. Not all premium functionality is available. | `android` |
| 💎 | **[Enable Premium+](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `android` |
| 💎 | **[Enable Prime](https://gitlab.com/hoo-dles/morphe-patches)** | Enable Nova Launcher Prime and app locked behind the subscription paywall. | `launcher` |
| 💎 | **[Enable Prime membership](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `app` |
| 💎 | **[Enable Pro](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `MemeGenerator` |
| 💎 | **[Enable Pro](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `getmimo` |
| 💎 | **[Enable Pro](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `mirinae` |
| 💎 | **[Enable Pro](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `myexpenses` |
| 💎 | **[Enable Pro](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `flowerfree` |
| 💎 | **[Enable Pro](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `solidexplorer2` |
| 💎 | **[Enable Pro](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. Login is required and AI functionality is unavailable. | `moffice_eng` |
| 💎 | **[Enable Pro](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `reader` |
| 💎 | **[Enable Pro](https://gitlab.com/hoo-dles/morphe-patches)** |  | `screenrecorder` |
| 💎 | **[Enable SoundCloud Go](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. | `android` |
| 💎 | **[Enable custom tabs](https://gitlab.com/hoo-dles/morphe-patches)** | Open articles using your default browser. | `magazines` |
| 💎 | **[Enable debug](https://gitlab.com/hoo-dles/morphe-patches)** | Enables debugging on the app by setting android:debuggable="true". | Any |
| 💎 | **[Enable debug mode](https://gitlab.com/hoo-dles/morphe-patches)** | Enables hidden debug menu in settings. | `duolingo` |
| 💎 | **[Enable speed control](https://gitlab.com/hoo-dles/morphe-patches)** | Enables experimental speed control to the video player. | `thirdpartyclient` |
| 💎 | **[Force Native Keyboard](https://gitlab.com/hoo-dles/morphe-patches)** | When typing in normal lessons, Eggbun forces you to use their own on-screen keyboard. This patches forces the use of the default OS keyboard. | `eggconvo` |
| 💎 | **[Hide app icon](https://gitlab.com/hoo-dles/morphe-patches)** | Hides the app icon from the Android launcher. | Any |
| 💎 | **[MicroG integration](https://gitlab.com/hoo-dles/morphe-patches)** | Allows the app to work without root by using MicroG instead of Google Play Services. | `dailypay` |
| 💎 | **[MicroG integration](https://gitlab.com/hoo-dles/morphe-patches)** | Allows the app to work without root by using MicroG instead of Google Play Services. | `magazines` |
| 💎 | **[MicroG integration](https://gitlab.com/hoo-dles/morphe-patches)** | Allows the app to work without root by using MicroG instead of Google Play Services. | `podcastaddict` |
| 💎 | **[MicroG integration](https://gitlab.com/hoo-dles/morphe-patches)** | Allows the app to work without root by using MicroG instead of Google Play Services. | `solidexplorer2` |
| 💎 | **[MicroG integration](https://gitlab.com/hoo-dles/morphe-patches)** | Allows the app to work without root by using MicroG instead of Google Play Services. | `teuida` |
| 💎 | **[Remove delay](https://gitlab.com/hoo-dles/morphe-patches)** | Removes the imposed delay when changing VPN servers. | `android` |
| 💎 | **[Remove trial limit](https://gitlab.com/hoo-dles/morphe-patches)** | Removes the imposed 6-hour trial usage limit. | `vrd` |
| 💎 | **[Rename shared permissions](https://gitlab.com/hoo-dles/morphe-patches)** | Rename certain permissions shared across Amazon apps. Applying this patch can fix installation errors, but can also break features in certain apps. | `thirdpartyclient` |
| 💎 | **[Skip ads](https://gitlab.com/hoo-dles/morphe-patches)** | Automatically skips ads baked into the video stream. | `thirdpartyclient` |
| 💎 | **[Unlimited skips](https://gitlab.com/hoo-dles/morphe-patches)** | Disables the limit for skipping songs during playback. | `android` |
| 💎 | **[Unlock LAN connections](https://gitlab.com/hoo-dles/morphe-patches)** | Enables the LAN connections feature usually locked behind the Proton Plus paywall. | `android` |
| 💎 | **[Unlock all lessons](https://gitlab.com/hoo-dles/morphe-patches)** | Only unlocks lessons on the client UI! This is useful for pre-downloading content during free trial periods. | `superchinese` |
| 💎 | **[Unlock custom DNS](https://gitlab.com/hoo-dles/morphe-patches)** | Enables the custom DNS feature usually locked behind the Proton Plus paywall. | `android` |
| 💎 | **[Unlock premium features](https://gitlab.com/hoo-dles/morphe-patches)** | Enables app features locked behind the subscription paywall. Some UI elements may not show an active membership, but this does not effect functionality. | `iconpacker` |
| 💎 | **[Unlock split tunneling](https://gitlab.com/hoo-dles/morphe-patches)** | Enables the split tunneling feature usually locked behind the Proton Plus paywall. | `android` |

<!-- SUPPORTED_PATCHES_END -->

---

## 🤝 Contribution Guidelines

1. Always branch off the `Testing` branch for any optimizations or feature additions.
2. Keep codebase changes backward compatible.
3. Ensure to verify local builds using `python main.py <App>` before committing changes.
4. Submit your pull requests targeting the `Testing` branch.

---

## ⚠️ Troubleshooting

- **Access Violation / Segfault (0xC0000005) in Java:** Ensure you are using a stable JDK 21+ installation in your PATH.
- **Gradle Build Fails on Submodule:** The automated sync script will automatically fall back to downloading the upstream compiled release, ensuring compilation failures do not block the pipeline.
- **Submodule Conflict:** If submodules get out of sync locally, run `git submodule update --init --recursive --force`.
