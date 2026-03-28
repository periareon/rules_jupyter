"""The `jupyter_notebook_binary` runner."""

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Sequence

from nbclient.exceptions import CellExecutionError
from python.runfiles import Runfiles

from tools.process_wrappers.reporter import (
    CwdMode,
    configure_jupyter_environment,
    configure_ld_library_path,
    configure_pandoc,
    configure_playwright,
    execute_notebook,
    postprocess_notebook_outputs,
    save_notebook,
)
from tools.process_wrappers.tester import (
    collect_argv,
    create_arg_parser,
    generate_reports,
)


def parse_args(
    argv: Optional[Sequence[str]] = None, runfiles: Optional[Runfiles] = None
) -> argparse.Namespace:
    """Parse command line arguments, extending the base parser with --output-dir."""

    basename, _, _ = Path(__file__).name.rpartition(".")
    basename = os.environ.get("RULES_JUPYTER_BINARY_NAME", basename)
    output_dir = Path(os.environ.get("BUILD_WORKING_DIRECTORY", os.getcwd())) / basename

    parser = create_arg_parser(runfiles=runfiles, description=__doc__)
    parser.add_argument(
        "--out-dir",
        "--output_dir",
        dest="out_dir",
        type=Path,
        default=output_dir,
        help="Directory to write output files to. Relative paths are resolved against BUILD_WORKING_DIRECTORY.",
    )

    if argv is not None:
        return parser.parse_args(argv)

    return parser.parse_args()


def main() -> None:
    """The main entrypoint."""
    if "RULES_JUPYTER_DEBUG" in os.environ:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            level=logging.DEBUG,
        )

    runfiles = Runfiles.Create()
    if not runfiles:
        logging.error("Failed to create runfiles")
        sys.exit(1)

    args = parse_args(collect_argv(runfiles, "RULES_JUPYTER_ARGS_FILE"), runfiles)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        configure_jupyter_environment(Path(tmp_dir))

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

        args.out_dir.mkdir(parents=True, exist_ok=True)
        notebook_name = args.notebook.stem

        executed_notebook_path = args.out_dir / f"{notebook_name}_executed.ipynb"
        save_notebook(notebook, executed_notebook_path)
        logging.info("Saved executed notebook: %s", executed_notebook_path)

        for report_type in args.reports:
            output = generate_reports(
                notebook, notebook_name, report_type, args.out_dir
            )
            print(f"{report_type.capitalize()} report written to: {output}")

    sys.exit(0)


if __name__ == "__main__":
    main()
