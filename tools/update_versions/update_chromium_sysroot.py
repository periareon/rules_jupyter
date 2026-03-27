"""Generate sysroot_packages.bzl with Debian package URLs and integrity hashes.

Resolves the system library packages required by Chromium headless-shell
from Ubuntu mirrors (Noble 24.04) for both amd64 and arm64 architectures.
"""

import argparse
import base64
import hashlib
import json
import logging
import lzma
import os
import time
import urllib.request
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

# Packages required by Chromium headless-shell on Linux.
# Derived from `playwright install-deps --dry-run` on Ubuntu 24.04.
# Only library packages (.so providers) are included; font/X11 packages are omitted.
REQUIRED_PACKAGES: list[str] = [
    "libasound2t64",
    "libatk-bridge2.0-0t64",
    "libatk1.0-0t64",
    "libatspi2.0-0t64",
    "libcairo2",
    "libcups2t64",
    "libdbus-1-3",
    "libdrm2",
    "libgbm1",
    "libglib2.0-0t64",
    "libnspr4",
    "libnss3",
    "libnssutil3",
    "libpango-1.0-0",
    "libx11-6",
    "libxcb1",
    "libxcomposite1",
    "libxdamage1",
    "libxext6",
    "libxfixes3",
    "libxkbcommon0",
    "libxrandr2",
    "libfontconfig1",
    "libfreetype6",
    "libexpat1",
    "libxrender1",
    "libpangocairo-1.0-0",
    "libpixman-1-0",
    "libxau6",
    "libxdmcp6",
    "libwayland-server0",
    "libwayland-client0",
]

UBUNTU_MIRROR_AMD64 = "http://archive.ubuntu.com/ubuntu"
UBUNTU_MIRROR_ARM64 = "http://ports.ubuntu.com/ubuntu-ports"
UBUNTU_RELEASE = "noble"
UBUNTU_COMPONENTS: list[str] = ["main", "universe"]

ARCH_MAP: dict[str, str] = {
    "linux-x86_64": "amd64",
    "linux-aarch64": "arm64",
}

MIRROR_MAP: dict[str, str] = {
    "amd64": UBUNTU_MIRROR_AMD64,
    "arm64": UBUNTU_MIRROR_ARM64,
}

REQUEST_HEADERS: dict[str, str] = {"User-Agent": "curl/8.7.1"}

BUILD_TEMPLATE = '''\
"""Chromium Sysroot Packages

Debian packages providing system shared libraries required by Chromium
headless-shell on Linux. Used by playwright_chromium_with_sysroot.
"""

# AUTO-GENERATED: DO NOT MODIFY
#
# Update using the following command:
#
# ```
# bazel run //tools/update_versions:update_chromium_sysroot
# ```

CHROMIUM_SYSROOT_PACKAGES = {packages}
'''


def _workspace_root() -> Path:
    if "BUILD_WORKSPACE_DIRECTORY" in os.environ:
        return Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])
    return Path(__file__).parent.parent.parent


def _download_with_retry(url: str, max_retries: int = 3, delay: int = 2) -> bytes:
    """Download a URL with retries."""
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=REQUEST_HEADERS)
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()  # type: ignore[no-any-return]
        except (HTTPError, URLError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries - 1:
                logging.warning("Attempt %d failed for %s: %s", attempt + 1, url, e)
                time.sleep(delay * (attempt + 1))
    raise last_error  # type: ignore[misc]


def _compute_integrity(data: bytes) -> str:
    """Compute SRI integrity hash (sha256)."""
    digest = hashlib.sha256(data).digest()
    b64 = base64.b64encode(digest).decode("ascii")
    return f"sha256-{b64}"


def _parse_packages_index(content: str) -> dict[str, dict[str, str]]:
    """Parse a Debian Packages file into a dict of package_name -> fields."""
    packages: dict[str, dict[str, str]] = {}
    current: dict[str, str] = {}

    for line in content.split("\n"):
        if not line.strip():
            if "Package" in current:
                packages[current["Package"]] = current
            current = {}
            continue
        if line.startswith(" ") or line.startswith("\t"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            current[key.strip()] = value.strip()

    if "Package" in current:
        packages[current["Package"]] = current

    return packages


def _load_packages_index(arch: str) -> dict[str, dict[str, str]]:
    """Download and parse the Ubuntu Packages index for an architecture."""
    mirror = MIRROR_MAP[arch]
    all_packages: dict[str, dict[str, str]] = {}

    for component in UBUNTU_COMPONENTS:
        url = f"{mirror}/dists/{UBUNTU_RELEASE}/{component}/binary-{arch}/Packages.xz"
        logging.info("Downloading packages index: %s", url)

        data = _download_with_retry(url)
        content = lzma.decompress(data).decode("utf-8")
        packages = _parse_packages_index(content)
        all_packages.update(packages)
        logging.info(
            "Loaded %d packages from %s/%s",
            len(packages),
            UBUNTU_RELEASE,
            component,
        )

    return all_packages


def _resolve_packages(
    required: list[str],
    packages_index: dict[str, dict[str, str]],
    arch: str,
) -> list[dict[str, Any]]:
    """Resolve required package names to .deb URLs and download for hashing."""
    mirror = MIRROR_MAP[arch]
    resolved: list[dict[str, Any]] = []

    for pkg_name in required:
        if pkg_name not in packages_index:
            logging.warning("Package %s not found for %s, skipping", pkg_name, arch)
            continue

        pkg_info = packages_index[pkg_name]
        filename = pkg_info.get("Filename")
        if not filename:
            logging.warning("Package %s has no Filename field, skipping", pkg_name)
            continue

        url = f"{mirror}/{filename}"
        logging.info("Downloading %s (%s)", pkg_name, url)

        data = _download_with_retry(url)
        integrity = _compute_integrity(data)

        resolved.append(
            {
                "name": pkg_name,
                "urls": [url],
                "integrity": integrity,
            }
        )

        logging.info("  %s -> %s", pkg_name, integrity)

    return resolved


def _format_packages_dict(
    packages_by_platform: dict[str, list[dict[str, Any]]],
) -> str:
    """Format the packages dict as a Starlark literal."""
    lines: list[str] = ["{\n"]

    for platform, packages in sorted(packages_by_platform.items()):
        lines.append(f'    "{platform}": [\n')
        for pkg in packages:
            lines.append("        {\n")
            lines.append(f'            "name": "{pkg["name"]}",\n')
            lines.append(f'            "urls": {json.dumps(pkg["urls"])},\n')
            lines.append(f'            "integrity": "{pkg["integrity"]}",\n')
            lines.append("        },\n")
        lines.append("    ],\n")

    lines.append("}")
    return "".join(lines)


def main() -> None:
    """Main entrypoint."""
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=_workspace_root() / "playwright" / "private" / "sysroot_packages.bzl",
        help="Output path for sysroot_packages.bzl",
    )
    args = parser.parse_args()

    packages_by_platform: dict[str, list[dict[str, Any]]] = {}

    for platform, arch in sorted(ARCH_MAP.items()):
        logging.info("=== Resolving packages for %s (%s) ===", platform, arch)
        packages_index = _load_packages_index(arch)
        resolved = _resolve_packages(REQUIRED_PACKAGES, packages_index, arch)
        packages_by_platform[platform] = resolved
        logging.info(
            "Resolved %d/%d packages for %s",
            len(resolved),
            len(REQUIRED_PACKAGES),
            platform,
        )

    content = BUILD_TEMPLATE.format(
        packages=_format_packages_dict(packages_by_platform),
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    logging.info("Wrote %s", args.output)


if __name__ == "__main__":
    main()
