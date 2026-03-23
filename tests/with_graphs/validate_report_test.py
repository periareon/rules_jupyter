"""Regression test: plotly and matplotlib graphs appear in HTML/WebPDF reports."""

import platform
import re
from pathlib import Path

import pytest
from python.runfiles import Runfiles


def _rlocation(runfiles: Runfiles, rlocationpath: str) -> Path:
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


@pytest.fixture(scope="session")
def runfiles() -> Runfiles:
    r = Runfiles.Create()
    assert r is not None, "Failed to create Runfiles instance"
    return r


def test_html_contains_matplotlib_png(runfiles: Runfiles) -> None:
    html = _rlocation(
        runfiles, "rules_jupyter/tests/with_graphs/report.html"
    ).read_text(encoding="utf-8")
    png_matches = re.findall(r"data:image/png;base64,", html)
    assert (
        len(png_matches) >= 1
    ), f"Expected at least 1 base64 PNG (matplotlib), found {len(png_matches)}"


def test_html_contains_plotly_content(runfiles: Runfiles) -> None:
    html = _rlocation(
        runfiles, "rules_jupyter/tests/with_graphs/report.html"
    ).read_text(encoding="utf-8")
    assert "plotly" in html.lower(), "Expected plotly content in HTML report"


def test_html_contains_plotly_png_fallback(runfiles: Runfiles) -> None:
    html = _rlocation(
        runfiles, "rules_jupyter/tests/with_graphs/report.html"
    ).read_text(encoding="utf-8")
    png_matches = re.findall(r"data:image/png;base64,", html)
    assert (
        len(png_matches) >= 2
    ), f"Expected at least 2 base64 PNGs (matplotlib + plotly), found {len(png_matches)}"


def test_webpdf_is_non_trivial(runfiles: Runfiles) -> None:
    pdf_path = _rlocation(runfiles, "rules_jupyter/tests/with_graphs/report.pdf")
    size = pdf_path.stat().st_size
    assert size > 10_000, f"WebPDF is only {size} bytes -- graphs are likely missing"
