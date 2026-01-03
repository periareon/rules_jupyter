"""Playwright browser installer for Bazel.

This script copies browser files from Bazel filegroups to a directory structure
compatible with PLAYWRIGHT_BROWSERS_PATH environment variable.
"""

import argparse
import json
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


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--manifest",
        type=Path,
        action="append",
        required=True,
        help="JSON manifest file(s) containing browser information (one per browser)",
    )

    parser.add_argument(
        "--playwright-version",
        type=str,
        required=True,
        help="Playwright version (e.g., '1.57.0')",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory for installed browsers (PLAYWRIGHT_BROWSERS_PATH)",
    )

    return parser.parse_args()


def _find_common_root(file_paths: list[str]) -> Path:
    """Find the common root of all file paths.

    Args:
        file_paths: List of file paths

    Returns:
        Path to the common root directory

    Raises:
        RuntimeError: If no common root can be found
    """
    # Find common root by comparing path components
    path_components = []
    for file_path_str in file_paths:
        file_path = Path(file_path_str)
        if file_path.exists():
            path_components.append(file_path.resolve().parts)
        else:
            path_components.append(file_path.parts)

    if not path_components:
        raise ValueError("No valid file paths provided")

    # Find common prefix
    min_len = min(len(parts) for parts in path_components)
    common_components = []

    for i in range(min_len):
        if all(parts[i] == path_components[0][i] for parts in path_components):
            common_components.append(path_components[0][i])
        else:
            break

    if not common_components:
        raise RuntimeError(f"No common root found for file paths: {file_paths[:3]}...")

    return Path(*common_components)


def _find_app_directory_parent(root: Path) -> Path | None:
    """Find a .app directory above the given root and return its parent.

    Args:
        root: Root directory to start searching from

    Returns:
        Parent directory of .app directory if found, None otherwise
    """
    current = root
    for _ in range(10):  # Walk up max 10 levels
        # Check if current directory contains a .app directory
        if current.exists() and current.is_dir():
            for item in current.iterdir():
                if item.is_dir() and item.name.endswith(".app"):
                    logging.info(
                        "Found .app directory above common root: %s (using parent: %s)",
                        item,
                        current,
                    )
                    return current
        # Also check if current itself is a .app directory
        if current.name.endswith(".app"):
            browser_root = current.parent
            logging.info(
                "Common root is inside .app directory, using parent: %s",
                browser_root,
            )
            return browser_root

        # Walk up one level
        if current.parent == current:
            break
        current = current.parent

    return None


def find_browser_root(file_paths: list[str]) -> Path:
    """Find the browser root directory from file paths.

    Finds the common root of all files, then checks if there's a .app directory
    above that common root. If found, uses the .app directory's parent as the root.

    Args:
        file_paths: List of file paths

    Returns:
        Path to the browser root directory

    Raises:
        RuntimeError: If no common root can be found
    """
    if not file_paths:
        raise ValueError("No file paths provided")

    common_root = _find_common_root(file_paths)
    app_parent = _find_app_directory_parent(common_root)

    if app_parent:
        return app_parent

    # No .app directory found above common root, use common root
    logging.info("Using common root: %s", common_root)
    return common_root


def _calculate_relative_path(source_file: Path, browser_root: Path) -> Path:
    """Calculate relative path from browser_root to source_file.

    Args:
        source_file: Source file path
        browser_root: Browser root directory path

    Returns:
        Relative path from browser_root to source_file
    """
    try:
        return source_file.relative_to(browser_root)
    except ValueError:
        # If relative_to fails, construct relative path from parts
        browser_root_parts = list(browser_root.parts)
        source_parts = list(source_file.parts)

        # Find where browser_root_parts matches the start of source_parts
        if len(source_parts) > len(browser_root_parts):
            # Check if browser_root is a prefix of source_file
            if source_parts[: len(browser_root_parts)] == browser_root_parts:
                return Path(*source_parts[len(browser_root_parts) :])
            # Find common prefix and construct relative path
            common_len = 0
            for i in range(min(len(browser_root_parts), len(source_parts))):
                if browser_root_parts[i] == source_parts[i]:
                    common_len += 1
                else:
                    break
            # Calculate relative path
            up_levels = len(browser_root_parts) - common_len
            down_path = source_parts[common_len:]
            return Path(*([".."] * up_levels + list(down_path)))
        # Source is at or above browser_root, use filename
        return Path(source_file.name)


def _copy_file(source_file: Path, dest_file: Path) -> None:
    """Copy a single file from source to destination.

    Args:
        source_file: Source file path
        dest_file: Destination file path
    """
    # Skip if source and destination are the same file
    try:
        if source_file.samefile(dest_file):
            logging.debug("Skipping %s (same as destination)", source_file)
            return
    except (OSError, ValueError):
        # samefile can fail if files don't exist or are on different filesystems
        pass

    # Create parent directories
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    # Copy file and preserve metadata (copy2 handles executable permissions)
    try:
        shutil.copy2(source_file, dest_file)
        logging.debug("Copied %s -> %s", source_file, dest_file)
    except (OSError, PermissionError) as exc:
        logging.warning("Failed to copy %s - %s", source_file, exc)


def copy_browser(
    browser_type: str,
    revision: str,
    file_paths: list[str],
    output_dir: Path,
) -> None:
    """Copy browser files to the Playwright directory structure.

    Args:
        browser_type: Browser type (e.g., "chromium", "chromium-headless-shell")
        revision: Browser revision (e.g., "1200")
        file_paths: List of file paths from the manifest
        output_dir: Base output directory (will create browser-specific subdirectories)
    """
    # Create browser directory: PLAYWRIGHT_BROWSERS_PATH/{browser_dir}-{revision}/
    browser_dir_name = BROWSER_DIR_MAP.get(browser_type)
    if not browser_dir_name:
        raise ValueError(f"Unknown browser type: {browser_type}")

    browser_revision_dir = output_dir / f"{browser_dir_name}-{revision}"
    browser_revision_dir.mkdir(parents=True, exist_ok=True)

    if not file_paths:
        raise RuntimeError(f"No file paths provided for browser type: {browser_type}")

    logging.info(
        "Finding common root for %s from %d file paths",
        browser_type,
        len(file_paths),
    )
    if file_paths:
        logging.info("Sample file paths: %s", file_paths[:3])

    # Find the browser root (common root, checking for .app directories above it)
    browser_root = find_browser_root(file_paths)

    # Use the browser root directory name as the normalized name
    normalized_name = browser_root.name

    logging.info(
        "Copying %s revision %s from common root %s (normalized: %s) to %s",
        browser_type,
        revision,
        browser_root,
        normalized_name,
        browser_revision_dir,
    )

    # Copy contents of browser_root into {browser}-{revision}/{normalized_name}/
    # The structure should be: {browser}-{revision}/{normalized_name}/contents
    dest_path = browser_revision_dir / normalized_name

    if dest_path.exists():
        # Remove existing directory if it exists
        shutil.rmtree(dest_path)

    dest_path.mkdir(parents=True, exist_ok=True)

    # Copy individual files, preserving directory structure relative to browser_root
    for file_path_str in file_paths:
        source_file = Path(file_path_str).resolve()
        relative_path = _calculate_relative_path(source_file, browser_root)
        dest_file = dest_path / relative_path
        _copy_file(source_file, dest_file)

    logging.info("Successfully installed %s revision %s", browser_type, revision)


def main() -> None:
    """Main entrypoint."""
    if "RULES_JUPYTER_DEBUG" in os.environ:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            level=logging.DEBUG,
        )

    args = parse_args()

    if not args.manifest:
        raise ValueError("No manifest files provided")

    # Load all manifest files
    browsers_to_install = []

    for manifest_path in args.manifest:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        browser_type = manifest["browser_type"]
        version = manifest["version"]
        files = manifest["files"]

        browsers_to_install.append((browser_type, version, files))

    if not browsers_to_install:
        raise ValueError(
            "No browsers specified in manifests. Provide at least one browser with its version."
        )

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Copy each browser to the output directory
    for browser_type, revision, file_paths in browsers_to_install:
        copy_browser(
            browser_type=browser_type,
            revision=revision,
            file_paths=file_paths,
            output_dir=args.output_dir,
        )


if __name__ == "__main__":
    main()
