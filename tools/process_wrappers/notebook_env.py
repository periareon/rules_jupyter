"""The shared runtime of the rules_jupyter process wrappers.

Every wrapper (the `JupyterReport` action, `jupyter_notebook_test`,
`jupyter_notebook_binary` and `jupyter_lab`) prepares a notebook run the same
way: the process is pointed at the Bazel provided Jupyter, pandoc, Playwright
and LaTeX files, a kernelspec is installed, then the notebook is executed and
reports are exported. :func:`notebook_session` does all of that from the flags
registered by :func:`add_notebook_arguments`; the wrappers only differ in where
their arguments come from and where outputs go.
"""

import argparse
import asyncio
import functools
import json
import logging
import os
import platform
import sys
import tempfile
import warnings
from collections.abc import Callable, Generator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import Any, Optional

import nbformat
from nbclient.exceptions import CellExecutionError
from python.runfiles import Runfiles

from tools.process_wrappers.exporters import (
    LatexSettings,
    ReportRequest,
    configure_latex,
    export_report,
    parse_exporter_config,
    parse_report_templates,
    postprocess_notebook_outputs,
)
from tools.process_wrappers.kernels import (
    RUNFILES_ENV_VARS,
    KernelSpec,
    configure_kernelspec,
    parse_kernelspec_rlocations,
)


class CwdMode(StrEnum):
    """Notebook current working directory modes."""

    EXECUTION_ROOT = "execution_root"
    """The location where a bazel execution would normally spawn (e.g. within the runfiles dir for tests)."""

    NOTEBOOK_ROOT = "notebook_root"
    """The location of the notebook itself (within runfiles)"""


# -- Command line -------------------------------------------------------------


def init_logging() -> None:
    """Configure logging; `RULES_JUPYTER_DEBUG` enables debug output."""
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if "RULES_JUPYTER_DEBUG" in os.environ else logging.WARNING,
    )


def rlocation(runfiles: Runfiles, rlocationpath: str) -> Path:
    """Look up a runfile and ensure the file exists.

    Args:
        runfiles: The runfiles object.
        rlocationpath: The runfile key.

    Returns:
        The requested runfile.
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


def create_runfiles() -> Runfiles:
    """Create the runfiles object of the current process or exit."""
    runfiles = Runfiles.Create()
    if not runfiles:
        logging.error("Failed to create runfiles")
        sys.exit(1)
    return runfiles


def collect_argv(runfiles: Runfiles, args_file_var: str) -> list[str]:
    """Assemble ``sys.argv`` with the contents of an args file prepended.

    Args:
        runfiles: The runfiles object for lookups.
        args_file_var: The environment variable pointing to the args file.
    """
    argv = []
    args_file_path = os.environ.get(args_file_var)
    if args_file_path:
        args_file = rlocation(runfiles, args_file_path)
        argv = args_file.read_text(encoding="utf-8").splitlines()

    return argv + sys.argv[1:]


def path_type(runfiles: Optional[Runfiles]) -> Callable[[str], Path]:
    """The argparse ``type`` for path flags.

    Build actions pass paths directly; everything else passes rlocationpaths
    which are looked up in *runfiles*.
    """
    if runfiles is None:
        return Path
    return lambda value: rlocation(runfiles, value)


def add_notebook_arguments(
    parser: argparse.ArgumentParser, path: Callable[[str], Path] = Path
) -> None:
    """Register the flags shared by every process wrapper.

    Args:
        parser: The parser to extend.
        path: The argparse ``type`` used for path arguments.
    """
    parser.add_argument(
        "--notebook", type=path, required=True, help="The notebook file to execute."
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
        "--kernelspec",
        type=path,
        help=(
            "A `jupyter_kernelspec` json file describing the kernel to install. "
            "Defaults to the Python kernel of the toolchain's environment."
        ),
    )
    parser.add_argument(
        "--kernelspec_rlocation",
        dest="kernelspec_rlocations",
        action="append",
        default=[],
        help=(
            "A `rlocationpath=path` pair resolving a file referenced by the "
            "kernelspec. When absent, paths are resolved via runfiles."
        ),
    )
    parser.add_argument("--pandoc", type=path, help="The path to a pandoc binary.")
    parser.add_argument(
        "--playwright_browsers_dir",
        type=path,
        help="The path to a playwright browsers cache.",
    )
    parser.add_argument(
        "--ld_library_dir",
        type=path,
        help="Directory of shared libraries to prepend to LD_LIBRARY_PATH.",
    )
    parser.add_argument(
        "--latex_engine",
        type=path,
        help="A TeX engine executable (e.g. pdftex) used for pdf reports.",
    )
    parser.add_argument(
        "--latex_format",
        type=path,
        help="A precompiled `.fmt` file loaded by the engine via `-fmt`.",
    )
    parser.add_argument(
        "--latex_texmf_cnf",
        type=path,
        help="The `web2c/texmf.cnf` anchor of the texmf tree.",
    )
    parser.add_argument(
        "--bibtex",
        type=path,
        help="An optional bibtex executable.",
    )
    parser.add_argument(
        "--report",
        dest="reports",
        type=ReportRequest.parse,
        action="append",
        default=[],
        help="A report to generate as `<name>` or `<name>=<output path>`.",
    )
    parser.add_argument(
        "--report_template",
        dest="report_templates",
        action="append",
        default=[],
        help="A `<report>=<template>` pair selecting a layout for a report.",
    )
    parser.add_argument(
        "--exporter-arg",
        "--exporter_arg",
        dest="exporter_args",
        action="append",
        default=[],
        help="Traitlets-style flag forwarded to nbconvert exporters.",
    )
    parser.add_argument(
        "params",
        nargs="*",
        default=[],
        help="Additional args to be passed to the notebook.",
    )


# -- Environment --------------------------------------------------------------


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

    jupyter_data_dirs: list[str] = []

    for path_str in sys.path:
        path = Path(path_str)
        if not path.exists():
            continue

        # Look for *.data/data/share/jupyter pattern in site-packages
        if "site-packages" in path_str:
            site_packages = path
            while (
                site_packages.name != "site-packages"
                and site_packages.parent != site_packages
            ):
                site_packages = site_packages.parent
            if site_packages.name == "site-packages":
                for data_dir in site_packages.glob("*.data"):
                    jupyter_share = data_dir / "data" / "share" / "jupyter"
                    if jupyter_share.is_dir():
                        jupyter_data_dirs.append(str(jupyter_share))

        jupyter_share = path / "share" / "jupyter"
        if jupyter_share.is_dir():
            jupyter_data_dirs.append(str(jupyter_share))

    if jupyter_data_dirs:
        existing = os.environ.get("JUPYTER_PATH", "")
        all_paths = jupyter_data_dirs + ([existing] if existing else [])
        os.environ["JUPYTER_PATH"] = os.pathsep.join(all_paths)
        logging.debug(
            "Configured JUPYTER_PATH with %d directories", len(jupyter_data_dirs)
        )


def configure_pandoc(pandoc_path: Path) -> None:
    """Prepend the directory of the pandoc binary to ``PATH``.

    nbconvert looks for pandoc in PATH using ``shutil.which("pandoc")``.

    Args:
        pandoc_path: Path to the pandoc binary.
    """
    if not pandoc_path.exists():
        raise FileNotFoundError(f"Pandoc binary not found: {pandoc_path}")

    pandoc_dir = str(pandoc_path.parent.absolute())
    current_path = os.environ.get("PATH", "")
    os.environ["PATH"] = pandoc_dir + os.pathsep + current_path
    logging.debug("Added pandoc directory to PATH: %s", pandoc_dir)


def configure_playwright(browsers_dir: Path) -> None:
    """Point Playwright at the provided browser cache.

    Args:
        browsers_dir: Path to the playwright install cache.
    """
    if not browsers_dir.exists():
        raise FileNotFoundError(f"Chromium binary not found: {browsers_dir}")

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
def temporary_home(tmp_dir: Path) -> Generator[Path, None, None]:
    """Redirect HOME (and USERPROFILE on Windows) into ``<tmp_dir>/home``.

    On exit the original environment variables are restored.

    Args:
        tmp_dir: The caller-managed base directory.

    Yields:
        The home directory.
    """
    original_home = os.environ.get("HOME")
    original_userprofile = os.environ.get("USERPROFILE")
    temp_home = tmp_dir / "home"
    temp_home.mkdir(exist_ok=True, parents=True)
    os.environ["HOME"] = str(temp_home)
    if platform.system() == "Windows":
        os.environ["USERPROFILE"] = str(temp_home)
    try:
        yield temp_home
    finally:
        for var, original in (
            ("HOME", original_home),
            ("USERPROFILE", original_userprofile),
        ):
            if original is not None:
                os.environ[var] = original
            else:
                os.environ.pop(var, None)


def runfiles_environment() -> dict[str, str]:
    """Capture the runfiles variables of the current process.

    Kernels launched by Jupyter inherit these so executables built with
    Bazel (and their runfiles libraries) resolve files from the same tree.
    """
    return {var: os.environ[var] for var in RUNFILES_ENV_VARS if os.environ.get(var)}


# -- Execution ----------------------------------------------------------------


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
    old_stdout, old_stderr = sys.stdout, sys.stderr
    stream: StringIO | None = None
    if suppress_log:
        stream = StringIO()
        sys.stdout = stream
        sys.stderr = stream

    original_policy = None
    if sys.platform == "win32":
        original_policy = asyncio.get_event_loop_policy()
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    tornado_logger = logging.getLogger("tornado.general")
    tornado_orig_level = tornado_logger.level
    tornado_logger.setLevel(logging.CRITICAL)

    saved_stderr_fd: int | None = None
    if suppress_log and sys.platform == "win32":
        saved_stderr_fd = os.dup(2)
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, 2)
        os.close(devnull_fd)

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


def inject_args_cell(
    notebook: nbformat.NotebookNode,
    params: list[str],
    args_template: str,
    kernel_name: Optional[str],
) -> None:
    """Prepend a cell forwarding *params* to the notebook.

    ``ExecutePreprocessor.extra_arguments`` configures the kernel rather than
    its ``argv``, so a kernel specific cell is injected instead. The cell is
    injected even without params so notebooks see the args of the Bazel
    target rather than those of the kernel process.

    Args:
        notebook: The notebook to modify.
        params: The notebook args.
        args_template: The kernel's cell template; ``{args}`` is replaced by
            a JSON array of *params*. Kernels without one cannot take params.
        kernel_name: The kernel, for error messages.
    """
    if not args_template:
        if params:
            raise ValueError(
                f"Kernel `{kernel_name}` does not support notebook args but got: {params}"
            )
        return
    # `str.replace` rather than `str.format` so templates may contain braces.
    code = args_template.replace("{args}", json.dumps(params, indent=4))
    cell = nbformat.v4.new_code_cell(code)  # type: ignore[no-untyped-call]
    # Strip the 'id' field so notebooks using nbformat 4.0-4.4 don't fail
    # schema validation ("id" is only valid in 4.5+).
    cell.pop("id", None)
    cell.metadata["tags"] = ["injected-argv"]
    notebook.cells.insert(0, cell)


def execute_notebook(  # pylint: disable=too-many-arguments
    notebook_path: Path,
    cwd: Path,
    *,
    kernel: KernelSpec,
    kernel_name: Optional[str] = None,
    params: Optional[list[str]] = None,
    timeout: int = 600,
    suppress_log: bool = False,
) -> nbformat.NotebookNode:
    """Execute a Jupyter notebook and return the executed notebook.

    Args:
        notebook_path: Path to the notebook file (.ipynb).
        cwd: The path to use as `cwd`.
        kernel: The installed kernelspec, providing the args template and
            ZeroMQ transport.
        kernel_name: The kernel to request. Defaults to the notebook's
            metadata.
        params: Command-line arguments forwarded to the notebook.
        timeout: Timeout in seconds for cell execution.
        suppress_log: Whether to capture output while the notebook runs.

    Returns:
        The executed notebook.

    Raises:
        CellExecutionError: If a notebook cell raises an error.
    """
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)  # type: ignore[no-untyped-call]

    inject_args_cell(notebook, params or [], kernel.args_template, kernel_name)

    from traitlets.config import Config  # pylint: disable=import-outside-toplevel

    # IPC avoids ZeroMQ port collisions when Bazel runs many notebook actions
    # in parallel, but is not available on Windows and not supported by every
    # kernel, so kernelspecs may choose.
    config = Config()
    config.KernelManager.transport = kernel.transport or (
        "tcp" if sys.platform == "win32" else "ipc"
    )
    ep_kwargs: dict[str, Any] = {"timeout": timeout, "config": config}
    if kernel_name:
        ep_kwargs["kernel_name"] = kernel_name

    with _notebook_execution_environment(suppress_log):
        # Import ExecutePreprocessor here so environment variables can take effect
        # pylint: disable=import-outside-toplevel
        import nbconvert.preprocessors  # isort: skip

        ExecutePreprocessor = nbconvert.preprocessors.ExecutePreprocessor
        ep = ExecutePreprocessor(**ep_kwargs)  # type: ignore[no-untyped-call]
        ep.preprocess(notebook, {"metadata": {"path": str(cwd)}})

    return notebook  # type: ignore[no-any-return]


# -- Session ------------------------------------------------------------------


@dataclass
class NotebookSession:  # pylint: disable=too-many-instance-attributes
    """A process configured to run one notebook.

    Created by :func:`notebook_session`; the environment variables pointing at
    the toolchain are set for the lifetime of the session.
    """

    notebook: Path
    cwd: Path
    tmp_dir: Path
    kernel: KernelSpec
    kernel_name: Optional[str]
    params: list[str]
    reports: list[ReportRequest]
    report_templates: dict[str, str] = field(default_factory=dict)
    exporter_config: Optional[Any] = None
    latex: Optional[LatexSettings] = None

    def execute(self, *, suppress_log: bool) -> nbformat.NotebookNode:
        """Execute the notebook and post-process its outputs.

        A failing cell is reported on stderr and exits the process with
        status 1, which is the outcome every wrapper wants.
        """
        if not self.notebook.exists():
            raise FileNotFoundError(f"Notebook does not exist: {self.notebook}")

        logging.debug("Executing notebook: %s", self.notebook)
        try:
            notebook = execute_notebook(
                self.notebook,
                self.cwd,
                kernel=self.kernel,
                kernel_name=self.kernel_name,
                params=self.params,
                suppress_log=suppress_log,
            )
        except CellExecutionError as e:
            print(f"\nCellExecutionError: {e}", file=sys.stderr)
            sys.exit(1)
        logging.debug("Notebook execution completed successfully")

        postprocess_notebook_outputs(notebook)
        return notebook

    def write_reports(
        self, notebook: nbformat.NotebookNode, default_dir: Path, stem: str
    ) -> list[Path]:
        """Write every requested report.

        Args:
            notebook: The executed notebook.
            default_dir: Where reports without an explicit path are written.
            stem: The file stem for such reports.

        Returns:
            The paths written, in request order.
        """
        return [
            export_report(
                notebook,
                request,
                default_dir=default_dir,
                stem=stem,
                template_type=self.report_templates.get(request.format.name),
                exporter_config=self.exporter_config,
                latex=self.latex,
            )
            for request in self.reports
        ]


def _configure_tools(
    args: argparse.Namespace, tmp_dir: Path
) -> Optional[LatexSettings]:
    """Point the process at the toolchain's pandoc, Playwright and LaTeX files.

    Returns:
        The LaTeX settings when a TeX engine was given.
    """
    if args.pandoc:
        configure_pandoc(args.pandoc)
    if args.playwright_browsers_dir:
        configure_playwright(args.playwright_browsers_dir)
    if args.ld_library_dir:
        configure_ld_library_path(args.ld_library_dir)
    if not args.latex_engine:
        return None
    return configure_latex(
        args.latex_engine,
        args.latex_format,
        args.latex_texmf_cnf,
        args.bibtex,
        tmp_dir,
    )


def _table_resolver(rlocations: dict[str, Path]) -> Callable[[str], Path]:
    """Resolve rlocationpaths from the ``--kernelspec_rlocation`` table."""

    def resolve(rloc: str) -> Path:
        if rloc not in rlocations:
            raise KeyError(f"No --kernelspec_rlocation given for {rloc}")
        return rlocations[rloc]

    return resolve


@contextmanager
def notebook_session(
    args: argparse.Namespace,
    *,
    runfiles: Optional[Runfiles],
    tmp_dir: Optional[Path] = None,
    redirect_home: bool = True,
) -> Generator[NotebookSession, None, None]:
    """Configure the process from parsed :func:`add_notebook_arguments` flags.

    Args:
        args: The parsed arguments.
        runfiles: The runfiles of the process, or ``None`` inside a build
            action where every path is given explicitly.
        tmp_dir: A caller-managed scratch directory. A temporary directory
            is created and removed when ``None``.
        redirect_home: Whether to point ``HOME`` into *tmp_dir* so nothing is
            read from or written to the user's configuration.

    Yields:
        The configured session.
    """
    with ExitStack() as stack:
        if tmp_dir is None:
            tmp_dir = Path(
                stack.enter_context(
                    tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
                )
            )
        if redirect_home:
            stack.enter_context(temporary_home(tmp_dir))

        configure_jupyter_environment(tmp_dir)

        if runfiles is None:
            resolve = _table_resolver(
                parse_kernelspec_rlocations(args.kernelspec_rlocations)
            )
            extra_env = None
        else:
            resolve = functools.partial(rlocation, runfiles)
            extra_env = runfiles_environment()

        if args.kernelspec:
            kernel = KernelSpec.from_json(args.kernelspec, resolve)
        else:
            kernel = KernelSpec.python()
        configure_kernelspec(kernel, tmp_dir / "jupyter", resolve, extra_env=extra_env)

        if runfiles is None and args.kernelspec:
            # Within a build action kernel executables are tools which discover
            # their own runfiles next to themselves. Runfiles variables
            # inherited from this process would point them at the wrong tree.
            for var in RUNFILES_ENV_VARS:
                os.environ.pop(var, None)

        latex = _configure_tools(args, tmp_dir)

        if args.cwd_mode == CwdMode.NOTEBOOK_ROOT:
            cwd = args.notebook.parent
        else:
            cwd = Path.cwd()

        yield NotebookSession(
            notebook=args.notebook,
            cwd=cwd,
            tmp_dir=tmp_dir,
            kernel=kernel,
            kernel_name=args.kernel,
            params=list(args.params),
            reports=list(args.reports),
            report_templates=parse_report_templates(args.report_templates),
            exporter_config=(
                parse_exporter_config(args.exporter_args)
                if args.exporter_args
                else None
            ),
            latex=latex,
        )
