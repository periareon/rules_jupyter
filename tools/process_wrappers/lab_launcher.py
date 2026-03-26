"""The `jupyter_lab` runner.

Launches a Jupyter Lab server for interactive notebook development,
optionally auto-executing all cells when the user opens the notebook
in their browser by injecting a "Run All Cells" trigger into Lab's
frontend via a tornado OutputTransform.
"""

import argparse
import json
import logging
import os
import platform
import secrets
import shutil
import socket
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple, Optional, Sequence

from python.runfiles import Runfiles

from tools.process_wrappers.reporter import (
    CwdMode,
    configure_jupyter_environment,
    configure_pandoc,
    configure_playwright,
)


def _rlocation(runfiles: Runfiles, rlocationpath: str) -> Path:
    """Look up a runfile and ensure the file exists."""
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
        "--execute",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Auto-execute all notebook cells when the user opens the notebook.",
    )
    parser.add_argument(
        "--overrides",
        type=_path,
        required=True,
        help="A JupyterLab overrides.json file with default settings.",
    )
    parser.add_argument(
        "--run_mode",
        choices=["runfiles", "source"],
        default="runfiles",
        help="Controls where the notebook is served from.",
    )
    parser.add_argument(
        "--notebook_rlocationpath",
        type=str,
        help="Runfiles-relative path to the notebook (e.g. _main/pkg/nb.ipynb).",
    )
    parser.add_argument(
        "--notebook_src_short_path",
        type=str,
        help="Workspace-relative path to the notebook source file.",
    )
    parser.add_argument(
        "--data_file",
        action="append",
        default=[],
        dest="data_files",
        help="Data file as rlocationpath=short_path (repeatable).",
    )
    parser.add_argument(
        "--source_notebook",
        type=str,
        help="Workspace-relative path to the source notebook (source mode only).",
    )
    parser.add_argument(
        "params",
        nargs="*",
        help="Additional args to be passed to the jupyter script.",
    )

    if argv is not None:
        return parser.parse_args(argv)

    return parser.parse_args()


# -- Jupyter server config: session reuse --------------------------------------

_JUPYTER_SERVER_CONFIG_BASE = '''\
"""Jupyter server config for rules_jupyter.

Monkey-patches SessionManager to reuse existing sessions so Lab connects
to the same kernel when navigating back to an already-opened notebook.
"""

from jupyter_server.services.sessions.sessionmanager import SessionManager as _SM

_original_create_session = _SM.create_session

async def _reusing_create_session(self, path=None, **kwargs):
    try:
        for session in await self.list_sessions():
            if session.get("path") == path:
                self.log.info(
                    "Reusing existing session for %s (kernel %s)",
                    path,
                    session["kernel"]["id"],
                )
                return session
    except Exception:
        pass
    return await _original_create_session(self, path=path, **kwargs)

_SM.create_session = _reusing_create_session
'''

_TEMPLATES_DIR = Path(__file__).parent


def _write_jupyter_config(
    directory: Path, *, execute: bool, ibazel: bool = False
) -> Path:
    """Write a Jupyter server config file.

    When *execute* is True the config includes a tornado ``OutputTransform``
    that injects auto-run JavaScript into Lab's HTML page.  When *ibazel*
    is also True, the ibazel reload watcher script is appended so that
    rebuilds trigger an automatic revert-and-rerun cycle in the browser.

    Returns the path to the config file for ``--JupyterApp.config_file``.
    """
    config = _JUPYTER_SERVER_CONFIG_BASE
    if execute:
        # Read autorun.js and inline it into autorun_transform.py's
        # _AUTORUN_SCRIPT placeholder, then append the result to the
        # config.  At runtime the transform monkey-patches the Jupyter
        # server to inject the script into every /lab/* HTML response.
        autorun_js = (_TEMPLATES_DIR / "autorun.js").read_text(encoding="utf-8")
        if ibazel:
            ibazel_js = (_TEMPLATES_DIR / "ibazel_reload.js").read_text(
                encoding="utf-8"
            )
            autorun_js += "\n" + ibazel_js
        transform_template = (_TEMPLATES_DIR / "autorun_transform.py").read_text(
            encoding="utf-8"
        )
        config += "\n" + transform_template.replace("{autorun_script}", autorun_js)
    config_path = directory / "jupyter_server_config.py"
    config_path.write_text(config, encoding="utf-8")
    return config_path


def _write_overrides(directory: Path, overrides_file: Path, *, execute: bool) -> Path:
    """Copy the ``overrides.json`` into *directory* and write ``page_config.json``.

    When *execute* is True, ``page_config.json`` sets ``exposeAppInBrowser``
    so the injected auto-run script can call ``commands.execute()`` directly.

    Returns *directory* for ``--LabServerApp.app_settings_dir``.
    """
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copy2(overrides_file, directory / "overrides.json")
    if execute:
        # exposeAppInBrowser makes JupyterLab assign its Application
        # instance to window.jupyterapp in the browser.  The injected
        # autorun.js script uses this to call
        # commands.execute("notebook:run-all-cells") once the kernel is
        # connected.  jupyterlab_server reads page_config.json from
        # app_settings_dir and injects the values into a
        # <script id="jupyter-config-data"> tag in the HTML.
        page_config = {"exposeAppInBrowser": True}
        (directory / "page_config.json").write_text(
            json.dumps(page_config), encoding="utf-8"
        )
    return directory


def _find_lab_app_dir() -> Optional[Path]:
    """Find JupyterLab's static assets in Bazel's non-standard wheel layout.

    ``configure_jupyter_environment()`` populates ``JUPYTER_PATH`` with
    ``*.data/data/share/jupyter`` directories from site-packages.  The Lab
    app dir lives at ``<jupyter_path>/lab`` and must contain a ``static/``
    subdirectory with the built frontend assets.
    """
    jupyter_path = os.environ.get("JUPYTER_PATH", "")
    for path_str in jupyter_path.split(os.pathsep):
        if not path_str:
            continue
        lab_dir = Path(path_str) / "lab"
        if (lab_dir / "static").is_dir():
            return lab_dir
    return None


def _symlink_data_files(
    runfiles: Runfiles,
    data_files: list[str],
    work_dir: Path,
) -> None:
    """Symlink declared data dependencies into the synthetic runfiles tree.

    Each *data_files* entry is ``rlocationpath=short_path``.  The symlink
    is placed at ``work_dir/<rlocationpath>`` so the tree mirrors Bazel's
    runfiles layout.
    """
    for entry in data_files:
        rloc, _ = entry.split("=", 1)
        actual_path = _rlocation(runfiles, rloc)
        link = work_dir / rloc
        link.parent.mkdir(parents=True, exist_ok=True)
        if not link.exists():
            link.symlink_to(actual_path)


def _find_free_port() -> int:
    """Find a free TCP port by binding to port 0."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return int(s.getsockname()[1])


class _WorkspaceLayout(NamedTuple):
    """Resolved paths for a ``jupyter_lab`` invocation."""

    notebook_dir: Path
    notebook_name: str
    config_dir: Path


def _prepare_source_mode(args: argparse.Namespace) -> _WorkspaceLayout:
    """Resolve paths for ``run_mode='source'``."""
    workspace_dir_str = os.environ.get("BUILD_WORKSPACE_DIRECTORY", "")
    if not workspace_dir_str:
        raise RuntimeError(
            "run_mode='source' requires `bazel run` "
            "(BUILD_WORKSPACE_DIRECTORY is not set)"
        )
    workspace_dir = Path(workspace_dir_str)
    source_notebook = workspace_dir / args.source_notebook
    if not source_notebook.exists():
        raise FileNotFoundError(f"Source notebook not found: {source_notebook}")

    return _WorkspaceLayout(
        notebook_dir=source_notebook.parent,
        notebook_name=source_notebook.name,
        config_dir=Path(tempfile.mkdtemp(prefix="rules_jupyter_config_")),
    )


def _prepare_runfiles_mode(
    args: argparse.Namespace, runfiles: Runfiles
) -> _WorkspaceLayout:
    """Create a synthetic runfiles tree for ``run_mode='runfiles'``."""
    if not args.notebook.exists():
        raise FileNotFoundError(f"Notebook does not exist: {args.notebook}")

    work_dir = Path(tempfile.mkdtemp(prefix="rules_jupyter_server_"))

    dest_notebook = work_dir / args.notebook_rlocationpath
    dest_notebook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.notebook, dest_notebook)
    # Bazel runfiles are read-only; make the copy writable so the
    # notebook can be saved and exported from the Lab UI.
    dest_notebook.chmod(dest_notebook.stat().st_mode | 0o200)

    _symlink_data_files(runfiles, args.data_files, work_dir)

    real_runfiles_dir = os.environ.get("RUNFILES_DIR", "")
    if real_runfiles_dir:
        repo_mapping = Path(real_runfiles_dir) / "_repo_mapping"
        if repo_mapping.exists():
            shutil.copy2(repo_mapping, work_dir / "_repo_mapping")

    os.environ["RUNFILES_DIR"] = str(work_dir)
    os.environ.pop("RUNFILES_MANIFEST_FILE", None)

    return _WorkspaceLayout(
        notebook_dir=dest_notebook.parent,
        notebook_name=dest_notebook.name,
        config_dir=work_dir,
    )


def _build_lab_argv(
    layout: _WorkspaceLayout, args: argparse.Namespace, *, ibazel: bool = False
) -> list[str]:
    """Assemble the ``jupyterlab`` CLI arguments."""
    token = secrets.token_hex(24)
    port = _find_free_port()
    name = layout.notebook_name
    url = f"http://localhost:{port}/lab/tree/{name}?token={token}"
    print(f"\n  Jupyter Lab: {url}\n", flush=True)

    config_path = _write_jupyter_config(
        layout.config_dir, execute=args.execute, ibazel=ibazel
    )

    argv = [
        f"--ServerApp.token={token}",
        f"--ServerApp.port={port}",
        f"--ServerApp.default_url=/lab/tree/{name}",
        f"--notebook-dir={layout.notebook_dir}",
        f"--JupyterApp.config_file={config_path}",
    ]

    app_settings_dir = _write_overrides(
        layout.config_dir / "settings", args.overrides, execute=args.execute
    )
    argv.append(f"--LabServerApp.app_settings_dir={app_settings_dir}")

    app_dir = _find_lab_app_dir()
    if app_dir:
        argv.append(f"--app-dir={app_dir}")

    return argv


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

    args_file_path = os.environ.get("RULES_JUPYTER_LAB_ARGS_FILE")
    if not args_file_path:
        logging.error("RULES_JUPYTER_LAB_ARGS_FILE environment variable not set")
        sys.exit(1)

    args_file = _rlocation(runfiles, args_file_path)
    argv = args_file.read_text(encoding="utf-8").splitlines()
    args = parse_args(argv + sys.argv[1:], runfiles)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        configure_jupyter_environment(Path(tmp_dir))
        configure_pandoc(args.pandoc)
        if args.playwright_browsers_dir:
            configure_playwright(args.playwright_browsers_dir)

        ibazel_mode = os.environ.get("IBAZEL_NOTIFY_CHANGES") == "y"

        if args.run_mode == "source":
            layout = _prepare_source_mode(args)
            os.environ.pop("RUNFILES_DIR", None)
            os.environ.pop("RUNFILES_MANIFEST_FILE", None)
        else:
            layout = _prepare_runfiles_mode(args, runfiles)

        if ibazel_mode:
            if not args.run_mode == "runfiles":
                raise RuntimeError(
                    "ibazel cannot be used with `jupyter_lab.run_mode = 'source'`"
                )
            # pylint: disable-next=import-outside-toplevel
            from tools.process_wrappers.ibazel_handler import setup_ibazel

            setup_ibazel(
                source_path=args.notebook,
                dest_path=layout.notebook_dir / layout.notebook_name,
            )

        lab_argv = _build_lab_argv(layout, args, ibazel=ibazel_mode)

        # pylint: disable-next=import-outside-toplevel
        from jupyterlab.labapp import main as lab_main  # type: ignore[import-untyped]

        try:
            lab_main(argv=lab_argv)
        except SystemExit:
            pass
        finally:
            if args.run_mode == "runfiles":
                nb = layout.notebook_dir / layout.notebook_name
                print(f"\n  Modified notebook saved at: {nb}\n")


if __name__ == "__main__":
    main()
