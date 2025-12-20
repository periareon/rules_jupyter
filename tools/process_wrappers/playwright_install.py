"""Playwright browser installer for Bazel.

This script copies browser files from Bazel filegroups to a directory structure
compatible with PLAYWRIGHT_BROWSERS_PATH environment variable.
"""

import argparse
import logging
import os
import shutil
from pathlib import Path

# Browser type to Playwright directory name mapping
BROWSER_DIR_MAP = {
    "chromium": "chromium",
    "chromium-headless-shell": "chromium_headless_shell",
    "firefox": "firefox",
    "webkit": "webkit",
    "ffmpeg": "ffmpeg",
}


def infer_platform_from_path(file_path: str) -> str | None:
    """Infer platform identifier from a file path in browser archives.

    Browser archives contain platform-specific directory names:
    - chrome-linux/ -> linux-x86_64
    - chrome-headless-shell-linux64/ -> linux-x86_64
    - chrome-headless-shell-linux-arm64/ -> linux-aarch64
    - chrome-mac/ -> macos (need to check for arm64 vs x64)
    - chrome-headless-shell-mac-arm64/ -> macos-aarch64
    - chrome-headless-shell-mac-x64/ -> macos-x86_64
    - chrome-win/ -> windows-x86_64
    - chrome-headless-shell-win64/ -> windows-x86_64
    - firefox/Firefox.app/ -> macos
    - firefox/firefox.exe -> windows-x86_64
    - firefox/firefox -> linux
    - webkit/ (check executable names)
    """
    path_lower = file_path.lower()

    # Platform detection rules: (platform, indicators)
    platform_rules = [
        ("linux-x86_64", ["/chrome-linux/", "/chrome-headless-shell-linux64/"]),
        ("linux-aarch64", ["/chrome-headless-shell-linux-arm64/", "linux-arm64"]),
        (
            "macos-aarch64",
            ["/chrome-headless-shell-mac-arm64/", "mac-arm64", "/chrome-mac/"],
        ),
        (
            "macos-x86_64",
            ["/chrome-headless-shell-mac-x64/", "/chrome-headless-shell-mac/"],
        ),
        ("windows-x86_64", ["/chrome-win/", "/chrome-headless-shell-win64/", ".exe"]),
    ]

    # Check platform rules
    for platform, indicators in platform_rules:
        if any(indicator in path_lower for indicator in indicators):
            return platform

    # Browser-specific detection (Firefox and WebKit)
    result = None
    if "firefox" in path_lower:
        if ".exe" in path_lower:
            result = "windows-x86_64"
        elif ".app/" in path_lower:
            result = "macos-aarch64"  # Default to aarch64
        elif "/firefox/" in path_lower and ".app" not in path_lower:
            result = "linux-x86_64"  # Default to x86_64
    elif "webkit" in path_lower:
        if ".exe" in path_lower or ".bat" in path_lower:
            result = "windows-x86_64"
        elif ".app/" in path_lower:
            result = "macos-aarch64"
        else:
            result = "linux-x86_64"

    return result


def copy_browser(
    browser_type: str, revision: str, browser_path: Path, output_dir: Path
) -> None:
    """Copy browser files to the Playwright directory structure.

    Args:
        browser_type: Browser type (e.g., "chromium", "chromium-headless-shell")
        revision: Browser revision (e.g., "1200")
        browser_path: Path to the browser filegroup directory (may be a subdirectory)
        output_dir: Base output directory (will create browser-specific subdirectories)
    """
    # Create browser directory: PLAYWRIGHT_BROWSERS_PATH/{browser_dir}-{revision}/
    browser_dir_name = BROWSER_DIR_MAP.get(browser_type)
    if not browser_dir_name:
        raise ValueError(f"Unknown browser type: {browser_type}")

    browser_revision_dir = output_dir / f"{browser_dir_name}-{revision}"
    browser_revision_dir.mkdir(parents=True, exist_ok=True)

    if not browser_path.exists():
        raise RuntimeError(f"Browser path does not exist: {browser_path}")

    # Find the archive root directory
    # browser_path might be a subdirectory (e.g., firefox/Nightly.app/Contents/MacOS)
    # We need to find the root (e.g., firefox/)
    archive_root = browser_path
    if browser_path.is_dir():
        # Walk up to find the archive root
        # Archive roots are typically: firefox/, chrome-headless-shell-mac-arm64/, etc.
        # They contain platform-specific directories or are the platform directory itself
        current = browser_path
        while current.parent != current:  # Not at filesystem root
            parent = current.parent
            # Check if parent contains platform-specific indicators
            # For Firefox: parent should be "firefox"
            # For Chromium headless shell: current might be "chrome-headless-shell-mac-arm64"
            # For FFmpeg: current might be the root
            if browser_type == "firefox" and current.name == "firefox":
                archive_root = current
                break
            if browser_type == "ffmpeg" and current.name in ["ffmpeg", "ffmpeg-mac"]:
                archive_root = current
                break
            # For other browsers, the current directory might be the platform-specific one
            # (e.g., chrome-headless-shell-mac-arm64)
            if any(
                indicator in current.name
                for indicator in ["chrome", "webkit", "headless"]
            ):
                archive_root = current
                break
            current = parent
        else:
            # If we didn't find a specific root, use browser_path as-is
            archive_root = browser_path

    # Copy all files from archive_root to browser_revision_dir
    logging.info(
        "Copying %s revision %s from %s to %s",
        browser_type,
        revision,
        archive_root,
        browser_revision_dir,
    )

    # Copy the entire directory tree
    # archive_root is the directory containing the browser files (e.g., chrome-headless-shell-mac-arm64 or firefox)
    # We need to copy the entire archive_root directory into browser_revision_dir
    # so that browser_revision_dir contains the platform-specific directory
    if archive_root.is_dir():
        # copytree(src, dst) copies src INTO dst, creating dst/src/...
        # We want: browser_revision_dir/archive_root.name/...
        # So we copy archive_root into browser_revision_dir
        dest_path = browser_revision_dir / archive_root.name
        if dest_path.exists():
            # Remove existing directory if it exists (for dirs_exist_ok behavior)
            shutil.rmtree(dest_path)
        shutil.copytree(archive_root, dest_path)
    else:
        # If it's a file, copy it to the directory
        shutil.copy2(archive_root, browser_revision_dir)

    logging.info("Successfully installed %s revision %s", browser_type, revision)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory for installed browsers (PLAYWRIGHT_BROWSERS_PATH)",
    )

    parser.add_argument(
        "--playwright-version",
        type=str,
        required=True,
        help="Playwright version (e.g., '1.57.0')",
    )

    # Browser arguments - each browser has its own path and version
    parser.add_argument(
        "--chromium",
        type=Path,
        help="Path to Chromium browser files",
    )
    parser.add_argument(
        "--chromium-version",
        type=str,
        help="Chromium browser revision (e.g., '1200')",
    )

    parser.add_argument(
        "--chromium-headless-shell",
        type=Path,
        help="Path to Chromium headless-shell browser files",
    )
    parser.add_argument(
        "--chromium-headless-shell-version",
        type=str,
        help="Chromium headless-shell browser revision (e.g., '1200')",
    )

    parser.add_argument(
        "--firefox",
        type=Path,
        help="Path to Firefox browser files",
    )
    parser.add_argument(
        "--firefox-version",
        type=str,
        help="Firefox browser revision (e.g., '1497')",
    )

    parser.add_argument(
        "--webkit",
        type=Path,
        help="Path to WebKit browser files",
    )
    parser.add_argument(
        "--webkit-version",
        type=str,
        help="WebKit browser revision (e.g., '2227')",
    )

    parser.add_argument(
        "--ffmpeg",
        type=Path,
        help="Path to FFmpeg files",
    )
    parser.add_argument(
        "--ffmpeg-version",
        type=str,
        help="FFmpeg revision (e.g., '1011')",
    )

    return parser.parse_args()


def main() -> None:
    """Main entrypoint."""
    if "RULES_JUPYTER_DEBUG" in os.environ:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            level=logging.DEBUG,
        )

    args = parse_args()

    # Build browser -> (path, version) mapping
    browsers = []

    if args.chromium and args.chromium_version:
        browsers.append(("chromium", args.chromium_version, args.chromium))
    if args.chromium_headless_shell and args.chromium_headless_shell_version:
        browsers.append(
            (
                "chromium-headless-shell",
                args.chromium_headless_shell_version,
                args.chromium_headless_shell,
            )
        )
    if args.firefox and args.firefox_version:
        browsers.append(("firefox", args.firefox_version, args.firefox))
    if args.webkit and args.webkit_version:
        browsers.append(("webkit", args.webkit_version, args.webkit))
    if args.ffmpeg and args.ffmpeg_version:
        browsers.append(("ffmpeg", args.ffmpeg_version, args.ffmpeg))

    if not browsers:
        raise ValueError(
            "No browsers specified. Provide at least one browser with its version."
        )

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Copy each browser to the output directory
    for browser_type, revision, browser_path in browsers:
        copy_browser(browser_type, revision, browser_path, args.output_dir)


if __name__ == "__main__":
    main()
