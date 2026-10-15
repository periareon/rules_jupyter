"""The `jupyter_notebook_binary` runner.

Executes a notebook from runfiles and writes the executed notebook and any
requested reports to an output directory next to the user.
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


def _working_directory() -> Path:
    """Return the directory `bazel run` was invoked from.

    Falls back to the process working directory when not running under Bazel.
    """
    return Path(os.environ.get("BUILD_WORKING_DIRECTORY", os.getcwd()))


def _resolve_out_dir(value: str) -> Path:
    """Resolve an `--out-dir` value, anchoring relative paths to `BUILD_WORKING_DIRECTORY`.

    Under `bazel run` the process cwd is the runfiles tree, so a bare
    `Path(value)` would silently write outputs there instead of next to the user.
    """
    path = Path(value)
    if path.is_absolute():
        return path
    return _working_directory() / path


def main() -> None:
    """The main entrypoint."""
    init_logging()
    runfiles = create_runfiles()

    basename = os.environ.get("RULES_JUPYTER_BINARY_NAME", Path(__file__).stem)

    parser = argparse.ArgumentParser(description=__doc__)
    add_notebook_arguments(parser, path_type(runfiles))
    parser.add_argument(
        "--out-dir",
        "--out_dir",
        "--output_dir",
        dest="out_dir",
        type=_resolve_out_dir,
        default=_working_directory() / basename,
        help="Directory to write output files to. Relative paths are resolved against BUILD_WORKING_DIRECTORY.",
    )
    args = parser.parse_args(collect_argv(runfiles, "RULES_JUPYTER_ARGS_FILE"))

    with notebook_session(args, runfiles=runfiles) as session:
        notebook = session.execute(suppress_log=False)

        args.out_dir.mkdir(parents=True, exist_ok=True)
        stem = args.notebook.stem
        executed_notebook_path = args.out_dir / f"{stem}_executed.ipynb"
        save_notebook(notebook, executed_notebook_path)
        logging.info("Saved executed notebook: %s", executed_notebook_path)

        for request, output in zip(
            session.reports, session.write_reports(notebook, args.out_dir, stem)
        ):
            print(f"{request.format.name.capitalize()} report written to: {output}")


if __name__ == "__main__":
    main()
