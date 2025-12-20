"""The `jupyter_notebook_test` test runner."""

import argparse
import logging
import os
import platform
import shutil
import sys
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Optional, Sequence

import nbformat
from python.runfiles import Runfiles

from tools.process_wrappers.reporter import (
    CwdMode,
    configure_jupyter_environment,
    configure_pandoc,
    configure_playwright,
    execute_notebook,
    export_notebook,
    save_notebook,
)


class ReportType(StrEnum):
    """Supported report output types."""

    HTML = "html"
    MARKDOWN = "markdown"
    LATEX = "latex"
    PDF = "pdf"
    WEB_PDF = "webpdf"


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


def parse_args(
    argv: Optional[Sequence[str]] = None, runfiles: Optional[Runfiles] = None
) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)

    if runfiles:

        def _path(value: str) -> Path:
            return _rlocation(runfiles, value)

    else:

        def _path(value: str) -> Path:
            return Path(value)

    parser.add_argument(
        "--notebook", type=_path, required=True, help="The notebook file to execute."
    )
    parser.add_argument(
        "--pandoc",
        type=_path,
        required=True,
        help="The path to a pandoc binary.",
    )
    parser.add_argument(
        "--playwright_browsers_dir",
        type=_path,
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
        "--report",
        type=ReportType,
        action="append",
        default=[],
        help="Report types to generate after the test.",
    )
    parser.add_argument(
        "params",
        nargs="*",
        help="Additional args to be passed to the jupyter script.",
    )

    if argv is not None:
        return parser.parse_args(argv)

    return parser.parse_args()


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


def _get_exporter_map() -> dict[ReportType, tuple[type, str]]:
    """Get the mapping of report types to exporter classes and extensions."""
    # `nbconvert` must be imported here so the environment has a chance to be configured.
    # pylint: disable=import-outside-toplevel
    # isort: off
    from nbconvert import (
        HTMLExporter,
        LatexExporter,
        MarkdownExporter,
        PDFExporter,
        WebPDFExporter,
    )

    # isort: on

    return {
        ReportType.HTML: (HTMLExporter, ".html"),
        ReportType.MARKDOWN: (MarkdownExporter, ".md"),
        ReportType.LATEX: (LatexExporter, ".tex"),
        ReportType.PDF: (PDFExporter, ".tex.pdf"),
        ReportType.WEB_PDF: (WebPDFExporter, ".html.pdf"),
    }


def generate_reports(
    notebook: nbformat.NotebookNode,
    notebook_name: str,
    reports: list[ReportType],
    output_dir: Path,
) -> None:
    """Generate requested reports for the executed notebook.

    Args:
        notebook: The executed notebook.
        notebook_name: Base name for output files.
        reports: List of report types to generate.
        output_dir: Directory to write reports to.
    """
    exporter_map = _get_exporter_map()

    for report_type in reports:
        if report_type not in exporter_map:
            raise ValueError(f"Unknown report type: {report_type}")

        exporter_class, extension = exporter_map[report_type]
        output_path = output_dir / f"{notebook_name}{extension}"

        export_notebook(notebook, output_path, exporter_class)
        logging.debug("Generated %s report: %s", report_type, output_path)


def main() -> None:
    """The main entrypoint."""
    if "RULES_JUPYTER_DEBUG" in os.environ:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            level=logging.DEBUG,
        )

    # Set up environment FIRST before any nbconvert imports
    original_home, original_userprofile, temp_home = _set_temp_home_env()
    try:
        runfiles = Runfiles.Create()
        if not runfiles:
            logging.error("Failed to create runfiles")
            sys.exit(1)

        args_file_path = os.environ.get("RULES_JUPYTER_TEST_ARGS_FILE")
        if not args_file_path:
            logging.error("RULES_JUPYTER_TEST_ARGS_FILE environment variable not set")
            sys.exit(1)

        args_file = _rlocation(runfiles, args_file_path)
        argv = args_file.read_text(encoding="utf-8").splitlines()
        args = parse_args(argv + sys.argv[1:], runfiles)

        configure_jupyter_environment()

        configure_pandoc(args.pandoc)

        if args.playwright_browsers_dir:
            configure_playwright(args.playwright_browsers_dir)

        # Validate notebook exists
        if not args.notebook.exists():
            raise FileNotFoundError(f"Notebook does not exist: {args.notebook}")

        if args.cwd_mode == CwdMode.NOTEBOOK_ROOT:
            cwd = args.notebook.parent
        elif args.cwd_mode == CwdMode.WORKSPACE_ROOT:
            cwd = Path.cwd()
        else:
            raise ValueError(f"Unexpected cwd mode: {args.cwd_mode}")

        # Execute the notebook - any cell error will cause test failure
        logging.debug("Executing notebook: %s", args.notebook)
        notebook = execute_notebook(args.notebook, cwd, kernel_name=args.kernel)
        logging.debug("Notebook execution completed successfully")

        # Generate reports into the TEST_UNDECLARED_OUTPUTS_DIR if available
        if args.report:
            output_dir_str = os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR")
            if output_dir_str:
                output_dir = Path(output_dir_str)
                notebook_name = args.notebook.stem

                # Also save the executed notebook
                executed_notebook_path = output_dir / f"{notebook_name}_executed.ipynb"
                save_notebook(notebook, executed_notebook_path)
                logging.debug("Saved executed notebook: %s", executed_notebook_path)

                generate_reports(notebook, notebook_name, args.report, output_dir)
            else:
                logging.warning(
                    "TEST_UNDECLARED_OUTPUTS_DIR not set, skipping report generation"
                )
    finally:
        _restore_home_env(original_home, original_userprofile, temp_home)

    sys.exit(0)


if __name__ == "__main__":
    main()
