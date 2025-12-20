"""Ffmpeg Versions for Playwright

A mapping of browser revision to platform to integrity of the archive for said platform.
Each revision key maps to platform-specific download information.
"""

# AUTO-GENERATED: DO NOT MODIFY
#
# Update using the following command:
#
# ```
# bazel run //tools/update_versions:update_playwright_browsers
# ```

FFMPEG_VERSIONS = {
    "1011": {
        "linux-aarch64": {
            "integrity": "sha256-JijAPwUxj/gSyMm6ryB96i3fU+gYwNyTZxSw++OvsAk=",
            "strip_prefix": "",
            "urls": [
                "https://cdn.playwright.dev/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-linux-arm64.zip",
                "https://playwright.download.prss.microsoft.com/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-linux-arm64.zip",
                "https://cdn.playwright.dev/builds/ffmpeg/1011/ffmpeg-linux-arm64.zip",
            ],
        },
        "linux-x86_64": {
            "integrity": "sha256-68dPxblIMBdqPCkUrpa9i8f2qR9PM4kCMPhKFy7mHMw=",
            "strip_prefix": "",
            "urls": [
                "https://cdn.playwright.dev/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-linux.zip",
                "https://playwright.download.prss.microsoft.com/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-linux.zip",
                "https://cdn.playwright.dev/builds/ffmpeg/1011/ffmpeg-linux.zip",
            ],
        },
        "macos-aarch64": {
            "integrity": "sha256-fXfrDUS1msxAZfqiR2wN8aJCzJBMNG+CBiaBjJU8Unc=",
            "strip_prefix": "",
            "urls": [
                "https://cdn.playwright.dev/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-mac-arm64.zip",
                "https://playwright.download.prss.microsoft.com/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-mac-arm64.zip",
                "https://cdn.playwright.dev/builds/ffmpeg/1011/ffmpeg-mac-arm64.zip",
            ],
        },
        "macos-x86_64": {
            "integrity": "sha256-F+0Vovpg08dBgb78sr33ybsojRmyo7mJO5S2PyziYOQ=",
            "strip_prefix": "",
            "urls": [
                "https://cdn.playwright.dev/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-mac.zip",
                "https://playwright.download.prss.microsoft.com/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-mac.zip",
                "https://cdn.playwright.dev/builds/ffmpeg/1011/ffmpeg-mac.zip",
            ],
        },
        "windows-x86_64": {
            "integrity": "sha256-jQiCfAGa0257nUnTZIRH2IRTTLKs8gDnHHFfbdg0zFA=",
            "strip_prefix": "",
            "urls": [
                "https://cdn.playwright.dev/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-win64.zip",
                "https://playwright.download.prss.microsoft.com/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-win64.zip",
                "https://cdn.playwright.dev/builds/ffmpeg/1011/ffmpeg-win64.zip",
            ],
        },
    },
}
