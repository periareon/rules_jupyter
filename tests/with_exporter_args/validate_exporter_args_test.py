"""Integration test: exporter_args are forwarded to nbconvert exporters.

The BUILD target generates an HTML report with
``--HTMLExporter.exclude_input=true``, so the rendered HTML must not contain
the code cell source.  A comment ``EXPORTER_ARGS_SOURCE_MARKER`` exists only
in the code input (not in any cell output) and serves as the canary.
"""

import platform
from pathlib import Path

from python.runfiles import Runfiles


def _rlocation(runfiles: Runfiles, rlocationpath: str) -> Path:
    """Resolve a runfiles path to an absolute ``Path``.

    Args:
        runfiles: The runfiles object.
        rlocationpath: The runfile key.

    Returns:
        The resolved path.
    """
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


def test_html_excludes_input_cells() -> None:
    """With ``exclude_input=true`` the code source comment is stripped."""
    runfiles = Runfiles.Create()
    assert runfiles is not None

    html = _rlocation(
        runfiles, "rules_jupyter/tests/with_exporter_args/report.html"
    ).read_text(encoding="utf-8")

    assert "EXPORTER_ARGS_SOURCE_MARKER" not in html, (
        "HTML report still contains code input -- "
        "exporter_args exclude_input=true was not applied"
    )


def test_html_without_exporter_args_includes_input() -> None:
    """The baseline report (no exporter_args) retains the code source."""
    runfiles = Runfiles.Create()
    assert runfiles is not None

    html = _rlocation(
        runfiles, "rules_jupyter/tests/with_exporter_args/baseline_report.html"
    ).read_text(encoding="utf-8")

    assert (
        "EXPORTER_ARGS_SOURCE_MARKER" in html
    ), "Baseline HTML report is missing code input -- test precondition failed"
