"""The `jupyter_notebook_binary` runner."""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from python.runfiles import Runfiles

from tools.process_wrappers.reporter import (
    CwdMode,
    configure_jupyter_environment,
    configure_pandoc,
    configure_playwright,
    execute_notebook,
    postprocess_notebook_outputs,
    save_notebook,
)
from tools.process_wrappers.tester import (
    create_arg_parser,
    generate_reports,
    rlocation,
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

    args_file_path = os.environ.get("RULES_JUPYTER_ARGS_FILE")
    if not args_file_path:
        logging.error("RULES_JUPYTER_ARGS_FILE environment variable not set")
        sys.exit(1)

    args_file = rlocation(runfiles, args_file_path)
    argv = args_file.read_text(encoding="utf-8").splitlines()
    args = parse_args(argv + sys.argv[1:], runfiles)

    configure_jupyter_environment()

    configure_pandoc(args.pandoc)

    if args.playwright_browsers_dir:
        configure_playwright(args.playwright_browsers_dir)

    if not args.notebook.exists():
        raise FileNotFoundError(f"Notebook does not exist: {args.notebook}")

    if args.cwd_mode == CwdMode.NOTEBOOK_ROOT:
        cwd = args.notebook.parent
    elif args.cwd_mode == CwdMode.EXECUTION_ROOT:
        cwd = Path.cwd()
    else:
        raise ValueError(f"Unexpected cwd mode: {args.cwd_mode}")

    logging.debug("Executing notebook: %s", args.notebook)
    notebook = execute_notebook(
        args.notebook,
        cwd,
        kernel_name=args.kernel,
        suppress_log=False,
        params=args.params,
    )
    logging.debug("Notebook execution completed successfully")

    postprocess_notebook_outputs(notebook)

    output_dir = args.out_dir

    output_dir.mkdir(parents=True, exist_ok=True)
    notebook_name = args.notebook.stem

    executed_notebook_path = output_dir / f"{notebook_name}_executed.ipynb"
    save_notebook(notebook, executed_notebook_path)
    logging.info("Saved executed notebook: %s", executed_notebook_path)

    for report_type in args.reports:
        output = generate_reports(notebook, notebook_name, report_type, output_dir)
        print(f"{report_type.capitalize()} report written to: {output}")

    sys.exit(0)


if __name__ == "__main__":
    main()
