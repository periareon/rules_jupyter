"""A suite of tests ensuring version strings are all in sync."""

import os
import platform
import re
from pathlib import Path

from python.runfiles import Runfiles


def rlocation(runfiles: Runfiles, rlocationpath: str) -> Path:
    """Look up a runfile and ensure the file exists

    Args:
        runfiles: The runfiles object
        rlocationpath: The runfile key

    Returns:
        The requested runifle.
    """
    # TODO: https://github.com/periareon/rules_venv/issues/37
    source_repo = None
    if platform.system() == "Windows":
        source_repo = ""
    runfile = runfiles.Rlocation(rlocationpath, source_repo)
    if not runfile:
        raise FileNotFoundError(f"Failed to find runfile: {rlocationpath}")
    path = Path(runfile)
    if not path.exists():
        raise FileNotFoundError(f"Runfile does not exist: ({rlocationpath}) {path}")
    return path


def test_versions() -> None:
    """Test that the version.bzl and MODULE.bazel versions are synced."""
    runfiles = Runfiles.Create()
    if not runfiles:
        raise EnvironmentError("Failed to locate runfiles.")

    bzl_version = os.environ["VERSION"]

    module_bazel = rlocation(runfiles, "rules_jupyter/MODULE.bazel")
    module_version = re.findall(
        r'module\(\n\s+name = "rules_jupyter",\n\s+version = "([\d\w\.]+)",\n\)',
        module_bazel.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert module_version, f"Failed to parse version from {module_bazel}"

    assert bzl_version == module_version[0], f"{bzl_version} == {module_version[0]}"
