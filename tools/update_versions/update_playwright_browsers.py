"""A script for fetching Playwright browser releases and computing integrity hashes.

Generates a *_versions.bzl file for each browser type.
"""

import argparse
import base64
import binascii
import hashlib
import io
import json
import logging
import os
import re
import tarfile
import time
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

PLAYWRIGHT_GITHUB_RELEASES_API_TEMPLATE = (
    "https://api.github.com/repos/microsoft/playwright/releases?page={page}"
)

# Matches versions like 1.40.0, 1.57.0 (semantic versioning)
PLAYWRIGHT_RELEASE_NAME_REGEX = r"^v?(\d+\.\d+\.\d+(?:-\w+)?)$"

# Playwright browser download base URLs (primary and fallbacks)
PLAYWRIGHT_BROWSER_BASE_URLS = [
    "https://cdn.playwright.dev/dbazure/download/playwright/builds",
    "https://playwright.download.prss.microsoft.com/dbazure/download/playwright/builds",
    "https://cdn.playwright.dev/builds",
]

# Browser types to process
BROWSER_TYPES = [
    "chromium",
    "chromium-headless-shell",
    "firefox",
    "webkit",
    "ffmpeg",
]

# Browser type to archive name pattern
BROWSER_ARCHIVE_PATTERNS = {
    "chromium": {
        "macos-aarch64": "chromium-mac-arm64.zip",
        "macos-x86_64": "chromium-mac.zip",
        "linux-aarch64": "chromium-linux-arm64.zip",
        "linux-x86_64": "chromium-linux.zip",
        "windows-x86_64": "chromium-win64.zip",
    },
    "chromium-headless-shell": {
        "macos-aarch64": "chromium-headless-shell-mac-arm64.zip",
        "macos-x86_64": "chromium-headless-shell-mac.zip",
        "linux-aarch64": "chromium-headless-shell-linux-arm64.zip",
        "linux-x86_64": "chromium-headless-shell-linux.zip",
        "windows-x86_64": "chromium-headless-shell-win64.zip",
    },
    "firefox": {
        "macos-aarch64": "firefox-mac-arm64.zip",
        "macos-x86_64": "firefox-mac.zip",
        # Note: Firefox doesn't support linux-aarch64
        # Firefox uses ubuntu-20.04 instead of linux for x86_64
        "linux-x86_64": "firefox-ubuntu-20.04.zip",
        "windows-x86_64": "firefox-win64.zip",
    },
    "webkit": {
        "macos-aarch64": "webkit-mac-15-arm64.zip",
        "macos-x86_64": "webkit-mac-15.zip",
        # WebKit uses ubuntu-22.04 for Linux ARM64
        "linux-aarch64": "webkit-ubuntu-22.04-arm64.zip",
        # WebKit uses ubuntu-22.04 for Linux x86_64
        "linux-x86_64": "webkit-ubuntu-22.04.zip",
        "windows-x86_64": "webkit-win64.zip",
    },
    "ffmpeg": {
        "macos-aarch64": "ffmpeg-mac-arm64.zip",
        "macos-x86_64": "ffmpeg-mac.zip",
        "linux-aarch64": "ffmpeg-linux-arm64.zip",
        "linux-x86_64": "ffmpeg-linux.zip",
        "windows-x86_64": "ffmpeg-win64.zip",
    },
}

# Strip prefix for each browser/platform (empty means no strip)
STRIP_PREFIX = {
    browser: {platform: "" for platform in patterns}
    for browser, patterns in BROWSER_ARCHIVE_PATTERNS.items()
}

REQUEST_HEADERS = {"User-Agent": "curl/8.7.1"}

VERSIONS_TEMPLATE = """\
\"\"\"{browser_title} Versions for Playwright

A mapping of browser revision to platform to integrity of the archive for said platform.
Each revision key maps to platform-specific download information.
\"\"\"

# AUTO-GENERATED: DO NOT MODIFY
#
# Update using the following command:
#
# ```
# bazel run //tools/update_versions:update_playwright_browsers
# ```

{browser_upper}_VERSIONS = {versions_placeholder}
"""


def _workspace_root() -> Path:
    if "BUILD_WORKSPACE_DIRECTORY" in os.environ:
        return Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])

    return Path(__file__).parent.parent.parent


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a tuple of integers for comparison.

    Handles semantic versions like "1.40.0" or "1.57.0".

    Args:
        version_str: Version string like "1.57.0".

    Returns:
        Tuple of integers, padded to 3 components for consistent comparison.
    """
    # Remove 'v' prefix if present and split on '.'
    version_str = version_str.lstrip("v")
    parts_str = version_str.split(".")
    # Handle pre-release versions (e.g., "1.40.0-beta")
    if len(parts_str) > 0 and "-" in parts_str[-1]:
        parts_str[-1] = parts_str[-1].split("-")[0]
    parts_int = [int(p) for p in parts_str]
    # Pad to 3 components for consistent comparison
    while len(parts_int) < 3:
        parts_int.append(0)
    return tuple(parts_int)


def version_gte(version: str, min_version: str) -> bool:
    """Check if version is greater than or equal to min_version.

    Args:
        version: Version string to check.
        min_version: Minimum version to compare against.

    Returns:
        True if version >= min_version.
    """
    return parse_version(version) >= parse_version(min_version)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_workspace_root() / "jupyter/playwright/private",
        help="The directory in which to save version files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--min-version",
        type=str,
        default="1.50.0",
        help="Minimum Playwright version to fetch.",
    )
    parser.add_argument(
        "--max-versions",
        type=int,
        default=20,
        help="Maximum number of versions to fetch (most recent first).",
    )

    return parser.parse_args()


def compute_sha256(url: str) -> str:
    """Download a file and compute its SHA256 hash.

    Note: Unfortunately, Playwright/Chrome for Testing don't provide checksum files,
    so we must download the entire archive to compute the hash. This is slower but
    necessary for integrity verification.

    Args:
        url: The URL of the file to download.

    Returns:
        The SHA256 hash as a hex string.
    """
    logging.debug("Downloading and hashing (SHA256): %s", url)
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)

    sha256_hash = hashlib.sha256()

    with urlopen(req) as response:
        # Read in chunks to handle large files
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def integrity(hex_str: str, algorithm: str = "sha256") -> str:
    """Convert a SHA256 or SHA512 hex value to a Bazel integrity value.

    Args:
        hex_str: Hex string of the hash.
        algorithm: Hash algorithm, either "sha256" or "sha512".

    Returns:
        Bazel integrity string (e.g., "sha256-..." or "sha512-...").
    """
    try:
        raw_bytes = binascii.unhexlify(hex_str.strip())
    except binascii.Error as e:
        raise ValueError(f"Invalid hex input: {e}") from e

    encoded = base64.b64encode(raw_bytes).decode("utf-8")
    return f"{algorithm}-{encoded}"


def compute_sha512(url: str) -> str:
    """Download a file and compute its SHA512 hash.

    Args:
        url: The URL of the file to download.

    Returns:
        The SHA512 hash as a hex string.
    """
    logging.debug("Downloading and hashing (SHA512): %s", url)
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)

    sha512_hash = hashlib.sha512()

    with urlopen(req) as response:
        # Read in chunks to handle large files
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            sha512_hash.update(chunk)

    return sha512_hash.hexdigest()


def _extract_browser_revisions_from_tarball(
    tar: tarfile.TarFile,
) -> dict[str, str] | None:
    """Extract browser revisions from browsers.json in tarball."""
    browsers_json_path = None
    for member in tar.getmembers():
        if member.name.endswith("browsers.json"):
            browsers_json_path = member.name
            break

    if not browsers_json_path:
        return None

    browsers_file = tar.extractfile(browsers_json_path)
    if not browsers_file:
        return None

    browsers_data = json.loads(browsers_file.read())
    browser_revisions = {}
    if "browsers" in browsers_data:
        for browser in browsers_data["browsers"]:
            browser_name = browser.get("name")
            revision = browser.get("revision")
            if browser_name and revision:
                browser_revisions[browser_name] = str(revision)
    return browser_revisions


def get_all_browser_revisions(playwright_version: str) -> dict[str, str] | None:
    """Get all browser revisions for a given Playwright version.

    This fetches browsers.json from the npm package tarball to determine all browser revisions.

    Args:
        playwright_version: Playwright version string (e.g., "1.57.0").

    Returns:
        A dict mapping browser_type -> revision (e.g., {"chromium": "1200", "firefox": "1497"}),
        or None if not found.
    """
    npm_registry_url = (
        f"https://registry.npmjs.org/playwright-core/{playwright_version}"
    )

    try:
        req = urllib.request.Request(npm_registry_url, headers=REQUEST_HEADERS)
        with urlopen(req) as response:
            package_data = json.loads(response.read())
            dist = package_data.get("dist", {})
            tarball_url = dist.get("tarball")

            if not tarball_url:
                logging.warning(
                    "No tarball URL found for Playwright %s", playwright_version
                )
                return None

            logging.debug(
                "Downloading tarball for Playwright %s: %s",
                playwright_version,
                tarball_url,
            )
            tarball_req = urllib.request.Request(tarball_url, headers=REQUEST_HEADERS)
            with urlopen(tarball_req) as tarball_response:
                tarball_data = io.BytesIO(tarball_response.read())

                with tarfile.open(fileobj=tarball_data, mode="r:gz") as tar:
                    browser_revisions = _extract_browser_revisions_from_tarball(tar)
                    if browser_revisions is None:
                        logging.warning(
                            "browsers.json not found in tarball for Playwright %s",
                            playwright_version,
                        )
                        return None
                    return browser_revisions
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError) as e:
        logging.warning(
            "Failed to fetch browser revisions for Playwright %s: %s",
            playwright_version,
            e,
        )

    return None


def _process_release_for_version(
    release: dict[str, object],
    version_regex: re.Pattern[str],
    min_version: str,
) -> str | None:
    """Process a release and extract version if it matches."""
    tag_name_obj = release.get("tag_name")
    if not isinstance(tag_name_obj, str):
        return None
    tag_name = tag_name_obj

    regex = version_regex.match(tag_name)
    if not regex:
        logging.debug("Skipping non-matching tag: %s", tag_name)
        return None

    version = regex.group(1)
    if not version_gte(version, min_version):
        logging.info(
            "Version %s is below minimum %s, stopping",
            version,
            min_version,
        )
        return ""  # Signal to stop

    return version


def get_playwright_versions(min_version: str, max_versions: int) -> list[str]:
    """Get list of Playwright versions from GitHub releases.

    Args:
        min_version: Minimum Playwright version to include (e.g., "1.30.0").
        max_versions: Maximum number of versions to fetch.

    Returns:
        List of Playwright version strings, sorted from newest to oldest.
    """
    page = 1
    versions: list[str] = []
    version_regex = re.compile(PLAYWRIGHT_RELEASE_NAME_REGEX)

    logging.info(
        "Fetching Playwright versions >= %s (max %d versions)",
        min_version,
        max_versions,
    )

    while len(versions) < max_versions:
        url = urlparse(PLAYWRIGHT_GITHUB_RELEASES_API_TEMPLATE.format(page=page))
        req = urllib.request.Request(url.geturl(), headers=REQUEST_HEADERS)
        logging.debug("Releases url: %s", url.geturl())

        try:
            with urlopen(req) as data:
                json_data = json.loads(data.read())
                if not json_data:
                    break

                for release in json_data:
                    if len(versions) >= max_versions:
                        break

                    version = _process_release_for_version(
                        release, version_regex, min_version
                    )
                    if version == "":
                        return versions
                    if version:
                        versions.append(version)

            page += 1
            time.sleep(0.5)  # Be nice to GitHub API

        except HTTPError as exc:
            if exc.code == 404:
                break
            if exc.code != 403:
                raise

            reset_time = exc.headers.get("x-ratelimit-reset")
            if not reset_time:
                raise

            sleep_duration = float(reset_time) - time.time()
            if sleep_duration < 0.0:
                continue

            logging.warning("Rate limited: %s", exc.msg)
            logging.info("Waiting %.0fs for rate limit reset", sleep_duration)
            time.sleep(sleep_duration)

    return versions


def _check_url_availability(test_url: str) -> bool:
    """Check if a URL is available using Range request."""
    try:
        headers = REQUEST_HEADERS.copy()
        headers["Range"] = "bytes=0-0"
        req = urllib.request.Request(test_url, headers=headers)
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        response = opener.open(req, timeout=30)
        is_available = response.status in (200, 206)
        response.close()
        return is_available
    except HTTPError as e:
        if e.code == 404:
            return False
        logging.debug("HTTP error %d for URL %s: %s", e.code, test_url, e)
        return False
    except (URLError, OSError) as e:
        logging.debug("Failed to check URL %s: %s", test_url, e)
        return False


def _find_working_urls(download_path: str) -> list[str]:
    """Find all working URLs for a download path."""
    working_urls = []
    for base_url in PLAYWRIGHT_BROWSER_BASE_URLS:
        test_url = f"{base_url}/{download_path}"
        if _check_url_availability(test_url):
            working_urls.append(test_url)
    return working_urls


def _process_platform_artifact(
    browser_type: str,
    platform: str,
    download_path: str,
    browser_revision: str,
) -> dict[str, str | list[str]] | None:
    """Process a single platform artifact."""
    working_urls = _find_working_urls(download_path)
    if not working_urls:
        tried_urls = ", ".join(
            [f"{base_url}/{download_path}" for base_url in PLAYWRIGHT_BROWSER_BASE_URLS]
        )
        raise ValueError(
            f"Artifact not found for {browser_type} {platform} "
            f"(tried all URLs for path {download_path}). "
            f"Tried URLs: {tried_urls}"
        )

    download_url = working_urls[0]
    strip_prefix = STRIP_PREFIX.get(browser_type, {}).get(platform, "")

    logging.debug("Strip prefix for %s %s: %s", browser_type, platform, strip_prefix)

    try:
        sha256_hex = compute_sha256(download_url)
        return {
            "urls": working_urls,
            "integrity": integrity(sha256_hex),
            "strip_prefix": strip_prefix,
            "revision": browser_revision,
        }
    except (HTTPError, URLError, OSError, ValueError) as e:
        logging.error("Failed to download/hash %s: %s", download_url, e)
        return None


def query_browser_for_version(
    playwright_version: str,
    browser_type: str,
    browser_revision: str,
) -> dict[str, dict[str, str | list[str]]] | None:
    """Query and compute integrity hashes for a browser at a specific Playwright version.

    Args:
        playwright_version: Playwright version (e.g., "1.57.0").
        browser_type: Browser type (e.g., "chromium", "firefox").
        browser_revision: Browser revision (e.g., "1200").

    Returns:
        A dict mapping platform -> {urls, integrity, strip_prefix, revision}, or None if failed.
    """
    archive_patterns = BROWSER_ARCHIVE_PATTERNS.get(browser_type)
    if not archive_patterns:
        raise ValueError(f"Unknown browser type: {browser_type}")

    artifacts: dict[str, dict[str, str | list[str]]] = {}
    url_path = "chromium" if browser_type == "chromium-headless-shell" else browser_type

    for platform, archive_name in archive_patterns.items():
        download_path = f"{url_path}/{browser_revision}/{archive_name}"

        logging.debug(
            "Checking artifact for %s %s: %s", browser_type, platform, download_path
        )

        try:
            platform_data = _process_platform_artifact(
                browser_type, platform, download_path, browser_revision
            )
            if platform_data:
                artifacts[platform] = platform_data
                logging.debug(
                    "Computed integrity for %s %s: %s",
                    browser_type,
                    platform,
                    platform_data["integrity"],
                )
        except ValueError:
            # Artifact not found - skip this platform
            continue

    if artifacts:
        logging.info(
            "Collected %d artifacts for %s revision %s (Playwright %s)",
            len(artifacts),
            browser_type,
            browser_revision,
            playwright_version,
        )
        return artifacts
    logging.warning(
        "No artifacts collected for %s revision %s (Playwright %s)",
        browser_type,
        browser_revision,
        playwright_version,
    )
    return None


BROWSER_VERSIONS_TEMPLATE = """\
\"\"\"Browser Versions for Playwright

A mapping of Playwright version to browser name to browser revision.
This is used to automatically select browser versions based on Playwright version.
\"\"\"

# AUTO-GENERATED: DO NOT MODIFY
#
# Update using the following command:
#
# ```
# bazel run //tools/update_versions:update_playwright_browsers
# ```

BROWSER_VERSIONS = {versions_placeholder}
"""


def _write_browser_version_files(
    output_dir: Path,
    browser_releases: dict[str, dict[str, dict[str, dict[str, str | list[str]]]]],
) -> None:
    """Write individual browser version files."""
    for browser_type, releases in browser_releases.items():
        if not releases:
            logging.warning("No releases found for %s!", browser_type)
            continue

        logging.info("Collected %d revisions for %s", len(releases), browser_type)

        browser_name = browser_type.replace("-", "_")
        output_file = output_dir / f"{browser_name}_versions.bzl"
        browser_title = browser_type.replace("-", " ").title()
        browser_upper = browser_name.upper()

        logging.info("Writing to %s", output_file)
        versions_str = json.dumps(releases, indent=4, sort_keys=True)
        output_file.write_text(
            VERSIONS_TEMPLATE.format(
                browser_title=browser_title,
                browser_upper=browser_upper,
                versions_placeholder=versions_str,
            )
        )
        logging.info("Done writing %s", output_file)


def _write_browser_versions_file(
    output_dir: Path, browser_versions_map: dict[str, dict[str, str]]
) -> None:
    """Write browser_versions.bzl file."""
    browser_versions_file = output_dir / "browser_versions.bzl"
    logging.info("Writing browser versions mapping to %s", browser_versions_file)
    versions_str = json.dumps(browser_versions_map, indent=4, sort_keys=True)
    browser_versions_file.write_text(
        BROWSER_VERSIONS_TEMPLATE.format(versions_placeholder=versions_str)
    )
    logging.info("Done writing %s", browser_versions_file)


def main() -> None:
    """The main entrypoint."""
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # First, get all Playwright versions
    logging.info("Fetching Playwright versions from GitHub...")
    playwright_versions = get_playwright_versions(
        min_version=args.min_version,
        max_versions=args.max_versions,
    )

    if not playwright_versions:
        logging.error("No Playwright versions found!")
        return

    logging.info("Found %d Playwright versions", len(playwright_versions))

    # Initialize data structures: browser_type -> revision -> platform -> data
    # Revisions are the root keys, not Playwright versions
    browser_releases: dict[str, dict[str, dict[str, dict[str, str | list[str]]]]] = {
        browser_type: {} for browser_type in BROWSER_TYPES
    }
    browser_versions_map: dict[str, dict[str, str]] = {}

    # Iterate over Playwright versions and query all browsers at once
    for playwright_version in playwright_versions:
        logging.info("Processing Playwright version %s", playwright_version)

        # Get all browser revisions for this Playwright version (single npm tarball download)
        browser_revisions = get_all_browser_revisions(playwright_version)
        if not browser_revisions:
            logging.warning(
                "Could not determine browser revisions for Playwright %s, skipping",
                playwright_version,
            )
            continue

        logging.info(
            "Found browser revisions for Playwright %s: %s",
            playwright_version,
            browser_revisions,
        )

        # Store browser versions for browser_versions.bzl
        browser_versions_map[playwright_version] = browser_revisions

        # Query each browser for this version
        for browser_type in BROWSER_TYPES:
            browser_revision = browser_revisions.get(browser_type)
            if not browser_revision:
                logging.warning(
                    "No revision found for %s in Playwright %s, skipping",
                    browser_type,
                    playwright_version,
                )
                continue

            # Skip if we already have this revision
            # (multiple Playwright versions may use the same revision)
            if browser_revision in browser_releases[browser_type]:
                logging.debug(
                    "Revision %s for %s already processed, skipping",
                    browser_revision,
                    browser_type,
                )
                continue

            # Query and download artifacts for this browser/version
            artifacts = query_browser_for_version(
                playwright_version,
                browser_type,
                browser_revision,
            )
            if artifacts:
                # Key by revision instead of Playwright version
                # Remove revision field from platform data since it's now the key
                artifacts_by_revision = {}
                for platform, platform_data in artifacts.items():
                    # Create a copy without the revision field
                    artifacts_by_revision[platform] = {
                        k: v for k, v in platform_data.items() if k != "revision"
                    }
                browser_releases[browser_type][browser_revision] = artifacts_by_revision

    # Write individual browser version files
    _write_browser_version_files(args.output_dir, browser_releases)

    # Write browser_versions.bzl
    if browser_versions_map:
        _write_browser_versions_file(args.output_dir, browser_versions_map)


if __name__ == "__main__":
    main()
