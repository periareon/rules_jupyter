"""The `JupyterReport` action runner."""

import argparse
import asyncio
import json
import logging
import os
import platform
import shutil
import sys
import tempfile
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import Any, Optional

import nbformat
from nbclient.exceptions import CellExecutionError


class CwdMode(StrEnum):
    """Notebook current working directory modes."""

    EXECUTION_ROOT = "execution_root"
    """The location where a bazel execution would normally spawn (e.g. within the runfiles dir for tests)."""

    NOTEBOOK_ROOT = "notebook_root"
    """The location of the notebook itself (within runfiles)"""


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--notebook", type=Path, required=True, help="The notebook file to execute."
    )
    parser.add_argument(
        "--out_notebook",
        type=Path,
        required=True,
        help="The output path for the executed notebook.",
    )
    parser.add_argument(
        "--pandoc",
        type=Path,
        required=True,
        help="The path to a pandoc binary.",
    )
    parser.add_argument(
        "--playwright_browsers_dir",
        type=Path,
        help="The path to a playwright browsers cache.",
    )
    parser.add_argument(
        "--cwd_mode",
        type=CwdMode,
        required=True,
        help="The current working directory mode for the notebook execution.",
    )
    parser.add_argument(
        "--kernel", type=str, help="An optional kernel to explicitly use."
    )
    parser.add_argument(
        "--out_html", type=Path, help="The output path to an html report."
    )
    parser.add_argument(
        "--out_html_template_type",
        type=str,
        help="The template type for the output html.",
    )
    parser.add_argument(
        "--out_latex", type=Path, help="The output path to an latex report."
    )
    parser.add_argument(
        "--out_latex_template_type",
        type=str,
        help="The template type for the output latex.",
    )
    parser.add_argument(
        "--out_markdown", type=Path, help="The output path to an markdown report."
    )
    parser.add_argument(
        "--out_pdf", type=Path, help="The output path to an pdf (latex) report."
    )
    parser.add_argument(
        "--out_rst", type=Path, help="The output path to an rst report."
    )
    parser.add_argument(
        "--out_webpdf", type=Path, help="The output path to an pdf (web) report."
    )
    parser.add_argument(
        "params",
        nargs="*",
        help="Additional args to be passed to the jupyter script.",
    )

    return parser.parse_args()


def configure_jupyter_environment() -> None:
    """Configure Jupyter/IPython environment for Bazel's sandboxed execution.

    This function:
    1. Sets JUPYTER_PATH to find data files in Bazel's non-standard wheel layout
       where packages have their data in `*.data/data/share/jupyter` directories.
    2. Sets IPYTHONDIR to a writable temp location to avoid warnings about
       non-writable IPython directories in sandboxed environments.
    """
    # Set IPYTHONDIR to a writable temp location
    if "IPYTHONDIR" not in os.environ:
        temp_dir = Path(os.getenv("TEST_TMPDIR", tempfile.gettempdir()))
        ipython_dir = temp_dir / "rules_jupyter_ipython"
        ipython_dir.mkdir(exist_ok=True, parents=True)
        os.environ["IPYTHONDIR"] = str(ipython_dir)
        logging.debug("Set IPYTHONDIR to %s", ipython_dir)

    # Find and configure JUPYTER_PATH
    jupyter_data_dirs: list[str] = []

    # Search through sys.path for site-packages directories
    for path_str in sys.path:
        path = Path(path_str)
        if not path.exists():
            continue

        # Look for *.data/data/share/jupyter pattern in site-packages
        if "site-packages" in path_str:
            site_packages = path
            # Handle case where path is inside site-packages
            while (
                site_packages.name != "site-packages"
                and site_packages.parent != site_packages
            ):
                site_packages = site_packages.parent
            if site_packages.name == "site-packages":
                # Search for all .data directories with share/jupyter
                for data_dir in site_packages.glob("*.data"):
                    jupyter_share = data_dir / "data" / "share" / "jupyter"
                    if jupyter_share.is_dir():
                        jupyter_data_dirs.append(str(jupyter_share))

        # Also check if the path itself contains share/jupyter
        jupyter_share = path / "share" / "jupyter"
        if jupyter_share.is_dir():
            jupyter_data_dirs.append(str(jupyter_share))

    if jupyter_data_dirs:
        # Combine with existing JUPYTER_PATH if set
        existing = os.environ.get("JUPYTER_PATH", "")
        all_paths = jupyter_data_dirs + ([existing] if existing else [])
        os.environ["JUPYTER_PATH"] = os.pathsep.join(all_paths)
        logging.debug(
            "Configured JUPYTER_PATH with %d directories", len(jupyter_data_dirs)
        )


_ARGV_CELL_TEMPLATE = """\
import sys
sys.argv = [sys.argv[0]] + {argv_list}
"""


def execute_notebook(  # pylint: disable=too-many-arguments,too-many-locals
    notebook_path: Path,
    cwd: Path,
    *,
    kernel_name: Optional[str] = None,
    timeout: int = 600,
    suppress_log: bool = False,
    params: Optional[list[str]] = None,
) -> nbformat.NotebookNode:
    """Execute a Jupyter notebook and return the executed notebook.

    Args:
        notebook_path: Path to the notebook file (.ipynb).
        cwd: The path to use as `cwd`.
        kernel_name: Optional kernel name to use for execution.
        timeout: Timeout in seconds for cell execution.
        suppress_log: Whether or not to suppress output while the notebook is running.
        params: Optional list of command-line arguments to pass to the notebook via sys.argv.

    Returns:
        The executed notebook.

    Raises:
        Exception: If notebook execution fails (e.g., a cell raises an error).
    """
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)  # type: ignore[no-untyped-call]

    # Configure the execute preprocessor
    ep_kwargs: dict[str, int | str] = {"timeout": timeout}
    if kernel_name:
        ep_kwargs["kernel_name"] = kernel_name

    # If params are provided, inject a cell at the beginning to set sys.argv
    # Note: ExecutePreprocessor.extra_arguments is for kernel config, not sys.argv
    # So we inject a cell that sets sys.argv directly
    if params:
        argv_code = _ARGV_CELL_TEMPLATE.format(argv_list=json.dumps(params, indent=4))
        argv_cell = nbformat.v4.new_code_cell(argv_code)  # type: ignore[no-untyped-call]
        # Strip the 'id' field so notebooks using nbformat 4.0-4.4 don't fail
        # schema validation ("id" is only valid in 4.5+).
        argv_cell.pop("id", None)
        argv_cell.metadata["tags"] = ["injected-argv"]
        notebook.cells.insert(0, argv_cell)

    # Suppress stdout/stderr during execution
    old_stdout, old_stderr = sys.stdout, sys.stderr
    if suppress_log:
        stream = StringIO()
        sys.stdout = stream
        sys.stderr = stream
    # Windows defaults to ProactorEventLoop which lacks add_reader/add_writer
    # support required by ZMQ. Temporarily switch to SelectorEventLoop for
    # notebook execution, then restore so Playwright (WebPDF) can use
    # subprocess_exec which requires ProactorEventLoop.
    _original_policy = None
    if sys.platform == "win32":
        _original_policy = asyncio.get_event_loop_policy()
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        # Import ExecutePreprocessor here so environment variables can take effect
        # pylint: disable=import-outside-toplevel
        import nbconvert.preprocessors  # isort: skip

        ExecutePreprocessor = nbconvert.preprocessors.ExecutePreprocessor
        ep = ExecutePreprocessor(**ep_kwargs)  # type: ignore[no-untyped-call]

        # Suppress MissingIDFieldWarning from nbformat validation. Notebooks
        # using nbformat 4.0-4.4 (and cells injected without an 'id') will
        # trigger this warning, but adding IDs would break their schema..
        _missing_id_warning = getattr(nbformat, "MissingIDFieldWarning", None)
        if _missing_id_warning is not None:
            warnings.filterwarnings("ignore", category=_missing_id_warning)
        else:
            warnings.filterwarnings("ignore", message="Cell is missing an id field")

        # Execute the notebook
        ep.preprocess(notebook, {"metadata": {"path": str(cwd)}})
    except Exception:
        if suppress_log:
            print(stream.getvalue(), file=old_stderr)
        raise
    finally:
        if _original_policy is not None:
            asyncio.set_event_loop_policy(_original_policy)
        if suppress_log:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    return notebook  # type: ignore[no-any-return]


@contextmanager
def _plotly_pdf_workaround(
    notebook: nbformat.NotebookNode, exporter_class: type
) -> Generator[None, None, None]:
    """Strip interactive plotly HTML for PDF export so nbconvert uses image/png.

    WebPDFExporter captures the page before plotly.js finishes rendering,
    producing empty chart containers. The static PNG screenshot is reliable.
    """
    if exporter_class.__name__ not in ("WebPDFExporter", "PDFExporter"):
        yield
        return

    saved: list[tuple[dict[str, Any], str]] = []
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            if _PLOTLY_MIME in data and "text/html" in data:
                saved.append((data, data.pop("text/html")))
    try:
        yield
    finally:
        for data, html in saved:
            data["text/html"] = html


def export_notebook(
    notebook: nbformat.NotebookNode,
    output_path: Path,
    exporter_class: type,
    template_name: Optional[str] = None,
) -> None:
    """Export a notebook to a specific format.

    Args:
        notebook: The executed notebook.
        output_path: Path to write the output.
        exporter_class: The nbconvert exporter class to use.
        template_name: Optional template name for the exporter.
    """
    exporter_kwargs = {}
    if template_name:
        exporter_kwargs["template_name"] = template_name

    exporter = exporter_class(**exporter_kwargs)

    with _plotly_pdf_workaround(notebook, exporter_class):
        output, _ = exporter.from_notebook_node(notebook)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output - handle both text and binary formats
    if isinstance(output, bytes):
        with open(output_path, "wb") as f:
            f.write(output)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)


def save_notebook(notebook: nbformat.NotebookNode, output_path: Path) -> None:
    """Save a notebook to disk.

    Args:
        notebook: The notebook to save.
        output_path: Path to write the notebook.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(notebook, f)  # type: ignore[no-untyped-call]


def configure_pandoc(pandoc_path: Path) -> None:
    """Configure PATH to include the pandoc binary.

    nbconvert looks for pandoc in PATH using shutil.which('pandoc').
    This function adds the pandoc binary's directory to PATH so it can be found.

    Args:
        pandoc_path: Path to the pandoc binary.
    """
    if not pandoc_path.exists():
        raise FileNotFoundError(f"Pandoc binary not found: {pandoc_path}")

    # Add the pandoc binary's directory to PATH
    pandoc_dir = str(pandoc_path.parent.absolute())
    current_path = os.environ.get("PATH", "")
    os.environ["PATH"] = pandoc_dir + os.pathsep + current_path
    logging.debug("Added pandoc directory to PATH: %s", pandoc_dir)


def configure_playwright(browsers_dir: Path) -> None:
    """Configure Playwright to use the provided Chromium browser.

    Playwright's WebPDFExporter uses Playwright to generate PDFs, which needs
    to find the Chromium browser. This function sets environment variables that
    Playwright respects to locate the browser.

    Args:
        browsers_dir: Path to the playwright install cache.
    """
    if not browsers_dir.exists():
        raise FileNotFoundError(f"Chromium binary not found: {browsers_dir}")

    # Set environment variables that Playwright respects
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_dir)
    logging.debug("Set PLAYWRIGHT_BROWSERS_PATH to: %s", browsers_dir)


def _set_temp_home_env() -> tuple[str | None, str | None, Path]:
    """Set HOME and USERPROFILE to a temporary directory.

    Returns:
        Tuple of (original HOME, original USERPROFILE, temp_home) values.
    """
    original_home = os.environ.get("HOME")
    original_userprofile = os.environ.get("USERPROFILE")
    temp_dir = Path(os.getenv("TEST_TMPDIR", tempfile.mkdtemp()))
    temp_home = temp_dir / "home"
    temp_home.mkdir(exist_ok=True, parents=True)
    os.environ["HOME"] = str(temp_home)
    if platform.system() == "Windows":
        os.environ["USERPROFILE"] = str(temp_home)
    return (original_home, original_userprofile, temp_home)


def _restore_home_env(
    original_home: str | None,
    original_userprofile: str | None,
    temp_home: Path,
) -> None:
    """Restore original HOME and USERPROFILE environment variables and cleanup temp directory."""
    if original_home is not None:
        os.environ["HOME"] = original_home
    elif "HOME" in os.environ:
        del os.environ["HOME"]

    if original_userprofile is not None:
        os.environ["USERPROFILE"] = original_userprofile
    elif "USERPROFILE" in os.environ:
        del os.environ["USERPROFILE"]

    # Clean up temporary directory
    if "TEST_TMPDIR" not in os.environ:
        try:
            shutil.rmtree(temp_home)
        except OSError:
            # Ignore errors during cleanup
            pass


_PLOTLY_MIME = "application/vnd.plotly.v1+json"


def _render_plotly_png_playwright(html: str) -> bytes:
    """Render a plotly HTML page to PNG using the toolchain's Playwright Chromium.

    PLAYWRIGHT_BROWSERS_PATH must already be set via configure_playwright().

    Args:
        html: A full HTML page string containing a plotly chart.

    Returns:
        PNG image bytes of the rendered chart.
    """
    # pylint: disable=import-outside-toplevel
    from playwright.sync_api import sync_playwright

    with tempfile.NamedTemporaryFile(
        suffix=".html", mode="w", encoding="utf-8", delete=False
    ) as f:
        f.write(html)
        html_path = f.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 800})
            page.goto(f"file://{html_path}", wait_until="networkidle")
            png_bytes = page.locator(".plotly-graph-div").screenshot()
            browser.close()
        return png_bytes
    finally:
        os.unlink(html_path)


def _postprocess_plotly_outputs(notebook: nbformat.NotebookNode) -> None:
    """Convert plotly MIME outputs to renderable formats.

    Plotly's default IPython renderer produces ``application/vnd.plotly.v1+json``
    which nbconvert cannot render. This function adds ``text/html`` (interactive,
    with embedded plotly.js) and ``image/png`` (static, via Playwright screenshot)
    representations so that HTML and WebPDF exports display the charts.

    Plotly is imported conditionally -- it is only needed when the notebook
    actually produced plotly outputs. The notebook's own deps are available
    at runtime because the reporter venv merges notebook and tool deps.
    """
    plotly_outputs: list[dict[str, Any]] = []
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") in ("display_data", "execute_result"):
                if _PLOTLY_MIME in output.get("data", {}):
                    plotly_outputs.append(output)

    if not plotly_outputs:
        return

    # pylint: disable=import-outside-toplevel
    try:
        import plotly.graph_objects as go  # type: ignore[import-not-found]
    except ImportError:
        logging.warning(
            "Notebook cell outputs contain plotly data but plotly is not "
            "importable. Plotly graphs may not appear in reports."
        )
        return

    browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not browsers_path:
        raise RuntimeError(
            "Notebook produces plotly graphs but the Playwright toolchain is "
            "not configured. Set `playwright_browsers_dir` on your "
            "`jupyter_toolchain` to enable plotly graph rendering in reports."
        )

    import base64

    logging.debug(
        "Post-processing %d plotly output(s) via Playwright", len(plotly_outputs)
    )

    for output in plotly_outputs:
        plotly_json = output["data"][_PLOTLY_MIME]
        fig = go.Figure(data=plotly_json.get("data"), layout=plotly_json.get("layout"))

        output["data"]["text/html"] = fig.to_html(
            full_html=False, include_plotlyjs=True
        )

        full_html = fig.to_html(full_html=True, include_plotlyjs=True)
        png_bytes = _render_plotly_png_playwright(full_html)
        output["data"]["image/png"] = base64.b64encode(png_bytes).decode("ascii")


def postprocess_notebook_outputs(notebook: nbformat.NotebookNode) -> None:
    """Post-process cell outputs so non-standard MIME types render in reports.

    Scans executed notebook cells for library-specific MIME types that
    nbconvert cannot render (e.g. plotly's ``application/vnd.plotly.v1+json``)
    and converts them to standard formats (``text/html``, ``image/png``).

    Libraries are imported conditionally -- notebook deps are available at
    runtime because the reporter venv merges notebook and tool deps.
    """
    _postprocess_plotly_outputs(notebook)


def _generate_outputs(
    notebook: nbformat.NotebookNode, args: argparse.Namespace
) -> None:
    """Generate all requested output formats."""
    # Now import nbconvert after environment is set up
    # pylint: disable=import-outside-toplevel
    # isort: skip
    import nbconvert

    if args.out_html:
        export_notebook(
            notebook,
            args.out_html,
            nbconvert.HTMLExporter,
            template_name=args.out_html_template_type,
        )
    if args.out_latex:
        export_notebook(
            notebook,
            args.out_latex,
            nbconvert.LatexExporter,
            template_name=args.out_latex_template_type,
        )
    if args.out_markdown:
        export_notebook(notebook, args.out_markdown, nbconvert.MarkdownExporter)
    if args.out_pdf:
        export_notebook(notebook, args.out_pdf, nbconvert.PDFExporter)
    if args.out_rst:
        export_notebook(notebook, args.out_rst, nbconvert.RSTExporter)
    if args.out_webpdf:
        export_notebook(notebook, args.out_webpdf, nbconvert.WebPDFExporter)


def main() -> None:
    """The main entrypoint."""
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if "RULES_JUPYTER_DEBUG" in os.environ else logging.ERROR,
    )

    args = parse_args()

    # Set up environment FIRST before any nbconvert imports
    original_home, original_userprofile, temp_home = _set_temp_home_env()
    try:
        # Configure Jupyter paths for Bazel's non-standard layout
        configure_jupyter_environment()

        # Configure pandoc path for nbconvert (injects to PATH)
        configure_pandoc(args.pandoc)

        # Configure playwright browsers (sets PLAYWRIGHT_BROWSERS_PATH)
        if args.playwright_browsers_dir:
            configure_playwright(args.playwright_browsers_dir)

        if args.cwd_mode == CwdMode.NOTEBOOK_ROOT:
            cwd = args.notebook.parent
        elif args.cwd_mode == CwdMode.EXECUTION_ROOT:
            cwd = Path.cwd()
        else:
            raise ValueError(f"Unexpected cwd mode: {args.cwd_mode}")

        # Execute notebook
        try:
            notebook = execute_notebook(
                args.notebook,
                cwd,
                kernel_name=args.kernel,
                suppress_log=True,
                params=args.params,
            )
        except CellExecutionError as e:
            print(f"\nCellExecutionError: {e}", file=sys.stderr)
            sys.exit(1)

        # Convert non-standard MIME types (e.g. plotly) to renderable formats
        postprocess_notebook_outputs(notebook)

        # Save the executed notebook
        save_notebook(notebook, args.out_notebook)

        # Generate all requested outputs
        _generate_outputs(notebook, args)
    finally:
        _restore_home_env(original_home, original_userprofile, temp_home)


if __name__ == "__main__":
    main()
