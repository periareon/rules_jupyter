"""The `jupyter_notebook_test` test runner.

Executes a notebook from runfiles and, when reports are requested, writes the
executed notebook and the reports to Bazel's undeclared test outputs.
"""

import argparse
import logging
import os
from pathlib import Path

from tools.process_wrappers.exporters import save_notebook
from tools.process_wrappers.notebook_env import (
    add_notebook_arguments,
    collect_argv,
    create_runfiles,
    init_logging,
    notebook_session,
    path_type,
)


def main() -> None:
    """The main entrypoint."""
    init_logging()
    runfiles = create_runfiles()

    parser = argparse.ArgumentParser(description=__doc__)
    add_notebook_arguments(parser, path_type(runfiles))
    args = parser.parse_args(collect_argv(runfiles, "RULES_JUPYTER_TEST_ARGS_FILE"))

    # Bazel manages the lifecycle of `TEST_TMPDIR`.
    test_tmpdir = Path(os.environ["TEST_TMPDIR"])
    with notebook_session(args, runfiles=runfiles, tmp_dir=test_tmpdir) as session:
        notebook = session.execute(suppress_log=False)

        if not session.reports:
            return
        output_dir_str = os.environ.get("TEST_UNDECLARED_OUTPUTS_DIR")
        if not output_dir_str:
            logging.warning(
                "TEST_UNDECLARED_OUTPUTS_DIR not set, skipping report generation"
            )
            return

        output_dir = Path(output_dir_str)
        stem = args.notebook.stem
        save_notebook(notebook, output_dir / f"{stem}_executed.ipynb")
        session.write_reports(notebook, output_dir, stem)


if __name__ == "__main__":
    main()
