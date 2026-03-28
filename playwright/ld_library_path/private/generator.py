"""Collect shared library files from debian archive extractions into a flat directory."""

import argparse
import re
import shutil
from pathlib import Path

_SO_PATTERN = re.compile(r"\.so(\.\d+)*$")


def _is_shared_lib(path: Path) -> bool:
    return bool(_SO_PATTERN.search(path.name)) and path.is_file()


def main() -> None:
    """Collect .so files from debian archive inputs into a flat output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to copy shared libraries into.",
    )
    parser.add_argument(
        "--dep-file",
        type=Path,
        action="append",
        default=[],
        help="Input file from a debian archive dependency. Repeatable.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    for dep_file in args.dep_file:
        if not _is_shared_lib(dep_file):
            continue
        if dep_file.name in seen:
            continue
        seen.add(dep_file.name)
        shutil.copy2(dep_file, args.output_dir / dep_file.name)


if __name__ == "__main__":
    main()
