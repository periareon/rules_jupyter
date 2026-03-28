"""The `jupyter_notebook_test` test runner."""

import argparse
import logging
import os
import platform
import sys
from enum import StrEnum
from pathlib import Path
from typing import Optional, Sequence

import nbformat
from nbclient.exceptions import CellExecutionError
from python.runfiles import Runfiles

from tools.process_wrappers.reporter import (
    CwdMode,
    configure_jupyter_environment,
    configure_ld_library_path,
    configure_pandoc,
    configure_playwright,
    execute_notebook,
    export_notebook,
    postprocess_notebook_outputs,
    save_notebook,
    temporary_home,
)


class ReportType(StrEnum):
    """Supported report output types."""

    HTML = "html"
    MARKDOWN = "markdown"
    LATEX = "latex"
    PDF = "pdf"
    WEB_PDF = "webpdf"


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


def create_arg_parser(
    runfiles: Optional[Runfiles] = None,
    description: Optional[str] = None,
) -> argparse.ArgumentParser:
    """Create an argument parser with the common notebook execution arguments.

    Args:
        runfiles: If provided, path arguments are resolved via runfiles lookup.
        description: Parser description. Defaults to this module's docstring.

    Returns:
        An ArgumentParser pre-populated with the shared flags.
    """
    parser = argparse.ArgumentParser(description=description or __doc__)

    if runfiles:

        def _path(value: str) -> Path:
            return rlocation(runfiles, value)

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
        "--ld_library_dir",
        type=_path,
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
        "--report",
        dest="reports",
        type=ReportType,
        action="append",
        default=[],
        help="Report types to generate.",
    )
    parser.add_argument(
        "params",
        nargs="*",
        help="Additional args to be passed to the jupyter script.",
    )

    return parser


def parse_args(
    argv: Optional[Sequence[str]] = None, runfiles: Optional[Runfiles] = None
) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_arg_parser(runfiles=runfiles)

    if argv is not None:
        return parser.parse_args(argv)

    return parser.parse_args()


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
    report_type: ReportType,
    output_dir: Path,
) -> Path:
    """Generate requested reports for the executed notebook.

    Args:
        notebook: The executed notebook.
        notebook_name: Base name for output files.
        reports: List of report types to generate.
        output_dir: Directory to write reports to.
    Returns:
        The path to the generated file.
    """
    exporter_map = _get_exporter_map()

    if report_type not in exporter_map:
        raise ValueError(f"Unknown report type: {report_type}")

    exporter_class, extension = exporter_map[report_type]
    output_path = output_dir / f"{notebook_name}{extension}"

    export_notebook(notebook, output_path, exporter_class)
    logging.debug("Generated %s report: %s", report_type, output_path)

    return output_path


def _init_logging() -> None:
    if "RULES_JUPYTER_DEBUG" in os.environ:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            level=logging.DEBUG,
        )


def collect_argv(runfiles: Runfiles, args_file_var: str) -> list[str]:
    """Parse the appropriate `sys.argv` while accounting for an args file.

    Args:
        runfiles: The runfiles object for lookups
        args_file_var: The environment variable pointing to the args file.
    """
    argv = []
    args_file_path = os.environ.get(args_file_var)
    if args_file_path:
        args_file = rlocation(runfiles, args_file_path)
        argv = args_file.read_text(encoding="utf-8").splitlines()

    return argv + sys.argv[1:]


def main() -> None:  # pylint: disable=too-many-locals,too-many-branches
    """The main entrypoint."""
    _init_logging()

    # Set up environment FIRST before any nbconvert imports.
    # Use TEST_TMPDIR so Bazel manages the lifecycle of the temp directory.
    test_tmpdir = Path(os.environ["TEST_TMPDIR"])
    with temporary_home(test_tmpdir):
        runfiles = Runfiles.Create()
        if not runfiles:
            logging.error("Failed to create runfiles")
            sys.exit(1)

        args = parse_args(
            collect_argv(runfiles, "RULES_JUPYTER_TEST_ARGS_FILE"), runfiles
        )

        configure_jupyter_environment(test_tmpdir)

        configure_pandoc(args.pandoc)

        if args.playwright_browsers_dir:
            configure_playwright(args.playwright_browsers_dir)
        if args.ld_library_dir:
            configure_ld_library_path(args.ld_library_dir)

        if not args.notebook.exists():
            raise FileNotFoundError(f"Notebook does not exist: {args.notebook}")

        if args.cwd_mode == CwdMode.NOTEBOOK_ROOT:
            cwd = args.notebook.parent
        elif args.cwd_mode == CwdMode.EXECUTION_ROOT:
            cwd = Path.cwd()
        else:
            raise ValueError(f"Unexpected cwd mode: {args.cwd_mode}")

        logging.debug("Executing notebook: %s", args.notebook)
        try:
            notebook = execute_notebook(
                args.notebook,
                cwd,
                kernel_name=args.kernel,
                suppress_log=False,
                params=args.params,
            )
        except CellExecutionError as e:
            print(f"\nCellExecutionError: {e}", file=sys.stderr)
            sys.exit(1)
        logging.debug("Notebook execution completed successfully")

        postprocess_notebook_outputs(notebook)

        if args.reports:
            output_dir_str = os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR")
            if output_dir_str:
                output_dir = Path(output_dir_str)
                notebook_name = args.notebook.stem

                executed_notebook_path = output_dir / f"{notebook_name}_executed.ipynb"
                save_notebook(notebook, executed_notebook_path)
                logging.debug("Saved executed notebook: %s", executed_notebook_path)

                for report_type in args.reports:
                    generate_reports(notebook, notebook_name, report_type, output_dir)
            else:
                logging.warning(
                    "TEST_UNDECLARED_OUTPUTS_DIR not set, skipping report generation"
                )

    sys.exit(0)


if __name__ == "__main__":
    main()
