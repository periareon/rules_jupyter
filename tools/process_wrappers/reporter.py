"""The `JupyterReport` action runner."""

import argparse
import asyncio
import json
import logging
import os
import platform
import sys
import tempfile
import warnings
from collections.abc import Generator
from contextlib import ExitStack, contextmanager
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
        "--ld_library_dir",
        type=Path,
        help="Directory of shared libraries to prepend to LD_LIBRARY_PATH.",
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
        "--exporter_arg",
        dest="exporter_args",
        action="append",
        default=[],
        help="Traitlets-style flag forwarded to nbconvert exporters.",
    )
    parser.add_argument(
        "params",
        nargs="*",
        help="Additional args to be passed to the jupyter script.",
    )

    return parser.parse_args()


def configure_jupyter_environment(tmp_dir: Path) -> None:
    """Configure Jupyter/IPython environment for Bazel's sandboxed execution.

    This function:
    1. Sets JUPYTER_PATH to find data files in Bazel's non-standard wheel layout
       where packages have their data in `*.data/data/share/jupyter` directories.
    2. Sets IPYTHONDIR to a writable temp location to avoid warnings about
       non-writable IPython directories in sandboxed environments.

    Args:
        tmp_dir: A caller-managed temporary directory used for IPYTHONDIR.
            The caller is responsible for cleanup.
    """
    if "IPYTHONDIR" not in os.environ:
        ipython_dir = tmp_dir / "ipython"
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


@contextmanager
def _notebook_execution_environment(
    suppress_log: bool,
) -> Generator[StringIO | None, None, None]:
    """Temporarily configure the process environment for notebook execution.

    Handles five concerns that would otherwise clutter ``execute_notebook``:

    1. **stdout/stderr redirect** -- when *suppress_log* is true, Python-level
       streams are captured to a :class:`~io.StringIO` that is yielded to the
       caller (and flushed to the real stderr on error).
    2. **Windows event-loop policy** -- switches to ``SelectorEventLoop`` so
       ZMQ's ``add_reader``/``add_writer`` work, then restores the original
       policy so Playwright (WebPDF) can use ``ProactorEventLoop`` afterwards.
    3. **Tornado logger** -- mutes ``tornado.general`` at ``CRITICAL`` to hide
       the harmless "not a socket" ``ZMQError`` logged during kernel shutdown
       on Windows.
    4. **fd-level stderr** -- on Windows with *suppress_log*, redirects file
       descriptor 2 to ``os.devnull`` so libzmq's C-level assertion doesn't
       leak into build output.
    5. **MissingIDFieldWarning** -- suppresses the nbformat warning for
       notebooks using format 4.0-4.4 that lack cell IDs.
    """
    # -- stdout / stderr --
    old_stdout, old_stderr = sys.stdout, sys.stderr
    stream: StringIO | None = None
    if suppress_log:
        stream = StringIO()
        sys.stdout = stream
        sys.stderr = stream

    # -- Windows event-loop policy --
    original_policy = None
    if sys.platform == "win32":
        original_policy = asyncio.get_event_loop_policy()
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # -- tornado logger --
    tornado_logger = logging.getLogger("tornado.general")
    tornado_orig_level = tornado_logger.level
    tornado_logger.setLevel(logging.CRITICAL)

    # -- fd-level stderr on Windows --
    saved_stderr_fd: int | None = None
    if suppress_log and sys.platform == "win32":
        saved_stderr_fd = os.dup(2)
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, 2)
        os.close(devnull_fd)

    # -- MissingIDFieldWarning --
    missing_id_warning = getattr(nbformat, "MissingIDFieldWarning", None)
    if missing_id_warning is not None:
        warnings.filterwarnings("ignore", category=missing_id_warning)
    else:
        warnings.filterwarnings("ignore", message="Cell is missing an id field")

    try:
        yield stream
    except Exception:
        if suppress_log and stream is not None:
            print(stream.getvalue(), file=old_stderr)
        raise
    finally:
        tornado_logger.setLevel(tornado_orig_level)
        if saved_stderr_fd is not None:
            os.dup2(saved_stderr_fd, 2)
            os.close(saved_stderr_fd)
        if original_policy is not None:
            asyncio.set_event_loop_policy(original_policy)
        if suppress_log:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


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

    # Configure the execute preprocessor.
    # Use IPC transport on Unix to avoid ZMQ port collisions when Bazel
    # runs multiple notebook actions in parallel on the same host.
    ep_kwargs: dict[str, Any] = {"timeout": timeout}
    if sys.platform != "win32":
        from traitlets.config import Config  # pylint: disable=import-outside-toplevel

        config = Config()
        config.KernelManager.transport = "ipc"
        ep_kwargs["config"] = config

    if kernel_name:
        ep_kwargs["kernel_name"] = kernel_name

    # If params are provided, inject a cell at the beginning to set sys.argv
    # Note: ExecutePreprocessor.extra_arguments is for kernel config, not sys.argv
    # So we inject a cell that sets sys.argv directly
    if params is not None:
        argv_code = _ARGV_CELL_TEMPLATE.format(argv_list=json.dumps(params, indent=4))
        argv_cell = nbformat.v4.new_code_cell(argv_code)  # type: ignore[no-untyped-call]
        # Strip the 'id' field so notebooks using nbformat 4.0-4.4 don't fail
        # schema validation ("id" is only valid in 4.5+).
        argv_cell.pop("id", None)
        argv_cell.metadata["tags"] = ["injected-argv"]
        notebook.cells.insert(0, argv_cell)

    with _notebook_execution_environment(suppress_log):
        # Import ExecutePreprocessor here so environment variables can take effect
        # pylint: disable=import-outside-toplevel
        import nbconvert.preprocessors  # isort: skip

        ExecutePreprocessor = nbconvert.preprocessors.ExecutePreprocessor
        ep = ExecutePreprocessor(**ep_kwargs)  # type: ignore[no-untyped-call]
        ep.preprocess(notebook, {"metadata": {"path": str(cwd)}})

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


def parse_exporter_config(flags: list[str]) -> Any:
    """Parse traitlets-style config flags into a :class:`~traitlets.config.Config`.

    Each flag should follow the ``--ClassName.trait_name=value`` convention used
    by ``jupyter nbconvert`` on the command line.  A bare flag without ``=``
    (e.g. ``--WebPDFExporter.exclude_input``) is treated as boolean ``True``.
    Values are decoded as JSON when possible, otherwise kept as strings.

    Args:
        flags: A list of traitlets config strings
            (e.g. ``["--WebPDFExporter.exclude_input=true"]``).

    Returns:
        A :class:`~traitlets.config.Config` object.
    """
    from traitlets.config import Config  # pylint: disable=import-outside-toplevel

    c = Config()
    for flag in flags:
        key, has_value, raw_value = flag.lstrip("-").partition("=")
        class_name, _, trait_name = key.partition(".")
        if not class_name or not trait_name:
            raise ValueError(
                f"Invalid config flag {flag!r}: expected --ClassName.trait_name=value"
            )
        if not has_value:
            value: Any = True
        else:
            try:
                value = json.loads(raw_value)
            except (json.JSONDecodeError, ValueError):
                value = raw_value
        setattr(c[class_name], trait_name, value)
    return c


def export_notebook(
    notebook: nbformat.NotebookNode,
    output_path: Path,
    exporter_class: type,
    template_name: Optional[str] = None,
    exporter_config: Optional[Any] = None,
) -> None:
    """Export a notebook to a specific format.

    Args:
        notebook: The executed notebook.
        output_path: Path to write the output.
        exporter_class: The nbconvert exporter class to use.
        template_name: Optional template name for the exporter.
        exporter_config: Optional :class:`~traitlets.config.Config` object
            forwarded to the exporter constructor.
    """
    exporter_kwargs: dict[str, Any] = {}
    if template_name:
        exporter_kwargs["template_name"] = template_name
    if exporter_config:
        exporter_kwargs["config"] = exporter_config

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


def configure_ld_library_path(ld_library_dir: Path) -> None:
    """Prepend a directory of shared libraries to LD_LIBRARY_PATH.

    Args:
        ld_library_dir: Path to a directory containing .so files.
    """
    current = os.environ.get("LD_LIBRARY_PATH", "")
    if current:
        os.environ["LD_LIBRARY_PATH"] = str(ld_library_dir) + os.pathsep + current
    else:
        os.environ["LD_LIBRARY_PATH"] = str(ld_library_dir)
    logging.debug("Set LD_LIBRARY_PATH to: %s", os.environ["LD_LIBRARY_PATH"])


@contextmanager
def temporary_home(
    tmp_dir: Optional[Path] = None,
) -> Generator[Path, None, None]:
    """Redirect HOME (and USERPROFILE on Windows) into a temp directory.

    Creates ``<dir>/home`` and points HOME at it.  On exit the original
    environment variables are restored.

    When *tmp_dir* is ``None`` a fresh ``TemporaryDirectory`` is created and
    cleaned up automatically on exit (using robust Windows-safe cleanup via
    ``ignore_cleanup_errors``).  When *tmp_dir* is provided the caller owns
    the directory lifecycle (e.g. Bazel's ``TEST_TMPDIR``).

    Args:
        tmp_dir: Optional base directory.  If ``None``, a temporary directory
            is created and cleaned up on exit.

    Yields:
        The base directory (caller-supplied or auto-created).
    """
    with ExitStack() as stack:
        if tmp_dir is None:
            tmp_dir = Path(
                stack.enter_context(
                    tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
                )
            )

        original_home = os.environ.get("HOME")
        original_userprofile = os.environ.get("USERPROFILE")
        temp_home = tmp_dir / "home"
        temp_home.mkdir(exist_ok=True, parents=True)
        os.environ["HOME"] = str(temp_home)
        if platform.system() == "Windows":
            os.environ["USERPROFILE"] = str(temp_home)
        try:
            yield tmp_dir
        finally:
            if original_home is not None:
                os.environ["HOME"] = original_home
            elif "HOME" in os.environ:
                del os.environ["HOME"]

            if original_userprofile is not None:
                os.environ["USERPROFILE"] = original_userprofile
            elif "USERPROFILE" in os.environ:
                del os.environ["USERPROFILE"]


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

    config = parse_exporter_config(args.exporter_args) if args.exporter_args else None

    if args.out_html:
        export_notebook(
            notebook,
            args.out_html,
            nbconvert.HTMLExporter,
            template_name=args.out_html_template_type,
            exporter_config=config,
        )
    if args.out_latex:
        export_notebook(
            notebook,
            args.out_latex,
            nbconvert.LatexExporter,
            template_name=args.out_latex_template_type,
            exporter_config=config,
        )
    if args.out_markdown:
        export_notebook(
            notebook,
            args.out_markdown,
            nbconvert.MarkdownExporter,
            exporter_config=config,
        )
    if args.out_pdf:
        export_notebook(
            notebook,
            args.out_pdf,
            nbconvert.PDFExporter,
            exporter_config=config,
        )
    if args.out_rst:
        export_notebook(
            notebook,
            args.out_rst,
            nbconvert.RSTExporter,
            exporter_config=config,
        )
    if args.out_webpdf:
        export_notebook(
            notebook,
            args.out_webpdf,
            nbconvert.WebPDFExporter,
            exporter_config=config,
        )


def main() -> None:
    """The main entrypoint."""
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if "RULES_JUPYTER_DEBUG" in os.environ else logging.ERROR,
    )

    args = parse_args()

    # Set up environment FIRST before any nbconvert imports
    with temporary_home() as temp_dir:
        configure_jupyter_environment(temp_dir)

        configure_pandoc(args.pandoc)

        if args.playwright_browsers_dir:
            configure_playwright(args.playwright_browsers_dir)
        if args.ld_library_dir:
            configure_ld_library_path(args.ld_library_dir)

        if args.cwd_mode == CwdMode.NOTEBOOK_ROOT:
            cwd = args.notebook.parent
        elif args.cwd_mode == CwdMode.EXECUTION_ROOT:
            cwd = Path.cwd()
        else:
            raise ValueError(f"Unexpected cwd mode: {args.cwd_mode}")

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

        postprocess_notebook_outputs(notebook)

        save_notebook(notebook, args.out_notebook)

        _generate_outputs(notebook, args)


if __name__ == "__main__":
    main()
