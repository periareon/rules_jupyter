"""Overlay sysroot shared libraries into a Chromium browser directory.

Copies all browser files preserving directory structure, then copies .so files
from sysroot Debian packages into the browser binary's directory so that
RPATH=$ORIGIN resolves them at runtime.
"""

import json
import logging
import os
import re
import shutil
import sys
from pathlib import Path

SO_FILE_PATTERN = re.compile(r"\.so(\.\d+)*$")


def _find_browser_binary_dir(output_dir: Path) -> Path:
    """Find the directory containing the browser binary inside the output."""
    for dirpath, _dirnames, filenames in os.walk(output_dir):
        for filename in filenames:
            if "headless-shell" in filename or "headless_shell" in filename:
                return Path(dirpath)
    raise RuntimeError(f"No browser binary found under {output_dir}")


def _find_common_root(file_paths: list[str]) -> Path:
    """Find the common root directory of all file paths."""
    resolved = []
    for p in file_paths:
        fp = Path(p)
        resolved.append(fp.resolve().parts if fp.exists() else fp.parts)

    if not resolved:
        raise ValueError("No file paths provided")

    min_len = min(len(parts) for parts in resolved)
    common: list[str] = []
    for i in range(min_len):
        if all(parts[i] == resolved[0][i] for parts in resolved):
            common.append(resolved[0][i])
        else:
            break

    if not common:
        raise RuntimeError(f"No common root found for: {file_paths[:3]}...")

    return Path(*common)


def main() -> None:
    """Main entrypoint."""
    if "RULES_JUPYTER_DEBUG" in os.environ:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            level=logging.DEBUG,
        )

    manifest_path = Path(sys.argv[1])
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    browser_files: list[str] = manifest["browser_files"]
    sysroot_files: list[str] = manifest["sysroot_files"]
    output_dir = Path(manifest["output_dir"])

    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy browser files preserving directory structure relative to common root
    browser_root = _find_common_root(browser_files)

    for file_path_str in browser_files:
        source = Path(file_path_str)
        resolved = source.resolve() if source.exists() else source
        try:
            rel = resolved.relative_to(browser_root)
        except ValueError:
            rel = Path(source.name)
        dest = output_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)

    # Find the browser binary directory in the output
    binary_dir = _find_browser_binary_dir(output_dir)

    # Copy .so files from sysroot into the browser binary directory
    for file_path_str in sysroot_files:
        source = Path(file_path_str)
        if not SO_FILE_PATTERN.search(source.name):
            continue
        dest = binary_dir / source.name
        if not dest.exists():
            shutil.copy2(source, dest)


if __name__ == "__main__":
    main()
