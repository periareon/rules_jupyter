"""The `JupyterReport` action runner."""

import argparse
import logging
import os
import platform
import shutil
import sys
import tempfile
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import Optional

import nbformat


class CwdMode(StrEnum):
    """Notebook current working directory modes."""

    WORKSPACE_ROOT = "workspace_root"
    NOTEBOOK_ROOT = "notebook_root"


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
        ipython_dir = os.path.join(tempfile.gettempdir(), "rules_jupyter_ipython")
        os.makedirs(ipython_dir, exist_ok=True)
        os.environ["IPYTHONDIR"] = ipython_dir
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


def execute_notebook(
    notebook_path: Path,
    cwd: Path,
    kernel_name: Optional[str] = None,
    timeout: int = 600,
    suppress_log: bool = False,
) -> nbformat.NotebookNode:
    """Execute a Jupyter notebook and return the executed notebook.

    Args:
        notebook_path: Path to the notebook file (.ipynb).
        cwd: The path to use as `cwd`.
        kernel_name: Optional kernel name to use for execution.
        timeout: Timeout in seconds for cell execution.
        suppress_log: Whether or not to suppress output while the notebook is running.

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

    # Suppress stdout/stderr during execution
    old_stdout, old_stderr = sys.stdout, sys.stderr
    if suppress_log:
        stream = StringIO()
        sys.stdout = stream
        sys.stderr = stream
    try:
        # Import ExecutePreprocessor here so environment variables can take effect
        # pylint: disable=import-outside-toplevel
        import nbconvert.preprocessors  # isort: skip

        ExecutePreprocessor = nbconvert.preprocessors.ExecutePreprocessor
        ep = ExecutePreprocessor(**ep_kwargs)  # type: ignore[no-untyped-call]

        # Execute the notebook
        ep.preprocess(notebook, {"metadata": {"path": str(cwd)}})
    except Exception:
        value = stream.getvalue()
        print(value, file=old_stderr)
        raise
    finally:
        if suppress_log:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    return notebook  # type: ignore[no-any-return]


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


def _set_temp_home_env() -> tuple[str | None, str | None, str]:
    """Set HOME and USERPROFILE to a temporary directory.

    Returns:
        Tuple of (original HOME, original USERPROFILE, temp_home) values.
    """
    original_home = os.environ.get("HOME")
    original_userprofile = os.environ.get("USERPROFILE")
    temp_home = tempfile.mkdtemp()
    os.environ["HOME"] = temp_home
    if platform.system() == "Windows":
        os.environ["USERPROFILE"] = temp_home
    return (original_home, original_userprofile, temp_home)


def _restore_home_env(
    original_home: str | None,
    original_userprofile: str | None,
    temp_home: str,
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
    try:
        shutil.rmtree(temp_home)
    except OSError:
        # Ignore errors during cleanup
        pass


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
    if "RULES_JUPYTER_DEBUG" in os.environ:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            level=logging.DEBUG,
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
        elif args.cwd_mode == CwdMode.WORKSPACE_ROOT:
            cwd = Path.cwd()
        else:
            raise ValueError(f"Unexpected cwd mode: {args.cwd_mode}")

        # Execute notebook
        notebook = execute_notebook(
            args.notebook, cwd, kernel_name=args.kernel, suppress_log=True
        )

        # Save the executed notebook
        save_notebook(notebook, args.out_notebook)

        # Generate all requested outputs
        _generate_outputs(notebook, args)
    finally:
        _restore_home_env(original_home, original_userprofile, temp_home)


if __name__ == "__main__":
    main()
