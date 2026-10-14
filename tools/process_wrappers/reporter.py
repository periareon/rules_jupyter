"""The `JupyterReport` action runner.

Executes a notebook inside a build action and writes the executed notebook
and every requested report to the paths Bazel declared.
"""

import argparse
from pathlib import Path

from tools.process_wrappers.exporters import save_notebook
from tools.process_wrappers.notebook_env import (
    add_notebook_arguments,
    init_logging,
    notebook_session,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_notebook_arguments(parser)
    parser.add_argument(
        "--out_notebook",
        type=Path,
        required=True,
        help="The output path for the executed notebook.",
    )
    return parser.parse_args()


def main() -> None:
    """The main entrypoint."""
    init_logging()
    args = parse_args()

    # Build actions name every file explicitly rather than through runfiles.
    with notebook_session(args, runfiles=None) as session:
        notebook = session.execute(suppress_log=True)
        save_notebook(notebook, args.out_notebook)
        session.write_reports(
            notebook, args.out_notebook.parent, args.out_notebook.stem
        )


if __name__ == "__main__":
    main()
