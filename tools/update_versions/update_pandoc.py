"""A script for fetching Pandoc releases and computing integrity hashes."""

import argparse
import base64
import binascii
import hashlib
import json
import logging
import os
import re
import time
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

PANDOC_GITHUB_RELEASES_API_TEMPLATE = (
    "https://api.github.com/repos/jgm/pandoc/releases?page={page}"
)

# Matches versions like 3.0, 3.0.1, 3.2.0.2 (2-4 components)
PANDOC_RELEASE_NAME_REGEX = r"^(\d+(?:\.\d+){1,3})$"

# Map platform names to artifact suffixes
# The suffixes to look for in release assets
PANDOC_ARTIFACT_SUFFIXES = {
    "macos-aarch64": "-arm64-macOS.zip",
    "macos-x86_64": "-x86_64-macOS.zip",
    "linux-x86_64": "-linux-amd64.tar.gz",
    "linux-aarch64": "-linux-arm64.tar.gz",
    "windows-x86_64": "-windows-x86_64.zip",
}

PANDOC_STRIP_PREFIX = {
    "-arm64-macOS.zip": "{prefix}-arm64",
    "-x86_64-macOS.zip": "{prefix}-x86_64",
    "-linux-amd64.tar.gz": "{prefix}",
    "-linux-arm64.tar.gz": "{prefix}",
    "-windows-x86_64.zip": "{prefix}",
}

REQUEST_HEADERS = {"User-Agent": "curl/8.7.1"}

BUILD_TEMPLATE = """\
\"\"\"Pandoc Versions

A mapping of platform to integrity of the archive for said platform for each version of Pandoc available.
\"\"\"

# AUTO-GENERATED: DO NOT MODIFY
#
# Update using the following command:
#
# ```
# bazel run //tools/update_versions:update_pandoc
# ```

PANDOC_VERSIONS = {versions}
"""


def _workspace_root() -> Path:
    if "BUILD_WORKSPACE_DIRECTORY" in os.environ:
        return Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])

    return Path(__file__).parent.parent.parent


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a tuple of integers for comparison.

    Handles versions with 2-4 components (e.g., "3.0", "3.0.1", "3.2.0.2").

    Args:
        version_str: Version string like "3.2.0.2".

    Returns:
        Tuple of integers, padded to 4 components for consistent comparison.
    """
    parts = [int(p) for p in version_str.split(".")]
    # Pad to 4 components for consistent comparison
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts)


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
        "--output",
        type=Path,
        default=_workspace_root() / "jupyter/private/pandoc_versions.bzl",
        help="The path in which to save results.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--min-version",
        type=str,
        default="3.1.1",
        help="Minimum version to fetch.",
    )

    return parser.parse_args()


def compute_sha256(url: str) -> str:
    """Download a file and compute its SHA256 hash.

    Args:
        url: The URL of the file to download.

    Returns:
        The SHA256 hash as a hex string.
    """
    logging.debug("Downloading and hashing: %s", url)
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


def integrity(hex_str: str) -> str:
    """Convert a sha256 hex value to a Bazel integrity value."""
    try:
        raw_bytes = binascii.unhexlify(hex_str.strip())
    except binascii.Error as e:
        raise ValueError(f"Invalid hex input: {e}") from e

    encoded = base64.b64encode(raw_bytes).decode("utf-8")
    return f"sha256-{encoded}"


def _process_artifact(
    platform: str, suffix: str, asset_map: dict[str, str], version: str
) -> dict[str, str] | None:
    """Process a single artifact for a platform.

    Returns:
        Artifact data dict with url, integrity, strip_prefix, or None if not found.
    """
    # Find the asset that ends with this suffix
    matching_asset = None
    matching_url = None
    for name, download_url in asset_map.items():
        if name.endswith(suffix):
            matching_asset = name
            matching_url = download_url
            break

    if not matching_url or not matching_asset:
        logging.warning(
            "No artifact found for platform %s (suffix: %s) in version %s",
            platform,
            suffix,
            version,
        )
        return None

    logging.debug("Found artifact for %s: %s", platform, matching_asset)

    # Extract the prefix from the asset name (part before the suffix)
    # e.g., "pandoc-3.8.3-arm64-macOS.zip" -> "pandoc-3.8.3"
    asset_prefix = matching_asset[: -len(suffix)]

    # Generate strip_prefix using the template
    strip_prefix_template = PANDOC_STRIP_PREFIX.get(suffix, "")
    strip_prefix = strip_prefix_template.format(prefix=asset_prefix)

    logging.debug("Strip prefix for %s: %s", platform, strip_prefix)

    # Download and compute hash
    try:
        sha256_hex = compute_sha256(matching_url)
        artifact_data = {
            "url": matching_url,
            "integrity": integrity(sha256_hex),
            "strip_prefix": strip_prefix,
        }
        logging.debug(
            "Computed integrity for %s: %s", platform, artifact_data["integrity"]
        )
        return artifact_data
    except (HTTPError, URLError, OSError, ValueError) as e:
        logging.error("Failed to download/hash %s: %s", matching_url, e)
        return None


def _process_release(
    release: dict[str, object], version_regex: re.Pattern[str], min_version: str
) -> tuple[str | None, dict[str, dict[str, str]] | None]:
    """Process a single release and return version and artifacts.

    Returns:
        Tuple of (version, artifacts) or (None, None) if version doesn't match.
        Returns ("", None) to signal stop fetching if version is too old.
    """
    tag_name = release.get("tag_name")
    if not isinstance(tag_name, str):
        logging.debug("Skipping release with invalid tag_name type")
        return (None, None)

    regex = version_regex.match(tag_name)
    if not regex:
        logging.debug("Skipping non-matching tag: %s", tag_name)
        return (None, None)

    version = regex.group(1)

    # Check if version meets minimum requirement
    if not version_gte(version, min_version):
        logging.info("Version %s is below minimum %s, stopping", version, min_version)
        return ("", None)  # Signal to stop fetching

    logging.info("Processing version %s", version)

    # Build a map of asset names to download URLs
    assets = release.get("assets")
    if not isinstance(assets, list):
        logging.warning("Release has invalid assets type, skipping")
        return (version, None)
    asset_map: dict[str, str] = {}
    for asset in assets:
        if isinstance(asset, dict):
            name = asset.get("name")
            url = asset.get("browser_download_url")
            if isinstance(name, str) and isinstance(url, str):
                asset_map[name] = url

    artifacts: dict[str, dict[str, str]] = {}
    for platform, suffix in PANDOC_ARTIFACT_SUFFIXES.items():
        artifact_data = _process_artifact(platform, suffix, asset_map, version)
        if artifact_data:
            artifacts[platform] = artifact_data

    if artifacts:
        logging.info("Collected %d artifacts for version %s", len(artifacts), version)
        return (version, artifacts)

    logging.warning("No artifacts collected for version %s", version)
    return (version, None)


def query_releases(min_version: str) -> dict[str, dict[str, dict[str, str]]]:
    """Query Pandoc GitHub releases and compute integrity hashes.

    Args:
        min_version: Minimum version to include (e.g., "3.0.0").

    Returns:
        A dict mapping version -> platform -> {url, integrity}.
    """
    page = 1
    releases_data: dict[str, dict[str, dict[str, str]]] = {}
    version_regex = re.compile(PANDOC_RELEASE_NAME_REGEX)
    stop_fetching = False

    logging.info("Fetching versions >= %s", min_version)

    while not stop_fetching:
        url = urlparse(PANDOC_GITHUB_RELEASES_API_TEMPLATE.format(page=page))
        req = urllib.request.Request(url.geturl(), headers=REQUEST_HEADERS)
        logging.debug("Releases url: %s", url.geturl())

        try:
            with urlopen(req) as data:
                json_data = json.loads(data.read())
                if not json_data:
                    break

                for release in json_data:
                    version, artifacts = _process_release(
                        release, version_regex, min_version
                    )
                    if version is None:
                        continue
                    if not version:  # Signal to stop fetching
                        stop_fetching = True
                        break
                    if artifacts:
                        releases_data[version] = artifacts

            page += 1
            time.sleep(0.5)  # Be nice to GitHub API

        except HTTPError as exc:
            if exc.code == 404:
                # No more pages
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

    return releases_data


def main() -> None:
    """The main entrypoint."""
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    logging.info("Fetching Pandoc releases from GitHub...")
    releases = query_releases(min_version=args.min_version)

    if not releases:
        logging.error("No releases found!")
        return

    logging.info("Collected %d versions", len(releases))

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Writing to %s", args.output)
    versions_str = json.dumps(releases, indent=4, sort_keys=True)
    args.output.write_text(BUILD_TEMPLATE.format(versions=versions_str))
    logging.info("Done")


if __name__ == "__main__":
    main()
