"""Kernelspecs: how the kernel process of a notebook is launched.

`jupyter_kernelspec` writes a json description of a kernel in which every file
reference is an rlocationpath. The process wrappers resolve those to real paths
(execpaths inside build actions, runfiles everywhere else) and install an
ordinary `kernel.json` that Jupyter can discover.

The Python environment of the toolchain is a kernel like any other: when no
kernelspec is given, :meth:`KernelSpec.python` describes `ipykernel` running in
the current interpreter, so every wrapper installs exactly one kernelspec and
there is a single launch path for all kernels.
"""

import json
import logging
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

RUNFILES_ENV_VARS = (
    "RUNFILES_DIR",
    "RUNFILES_MANIFEST_FILE",
    "RUNFILES_REPO_MAPPING",
    "RULES_VENV_RUNFILES_COLLECTION",
    "RULES_VENV_RUNFILES_DIR",
)
"""Environment variables describing the runfiles of the current process.

Kernels are separate executables. Within tests and `bazel run` they share the
runfiles tree of the process launching them, but within build actions they are
tools with runfiles of their own and these variables must not leak into them.
"""

PYTHON_ARGS_TEMPLATE = """\
import sys
sys.argv = [sys.argv[0]] + {args}
"""
"""The cell used to forward notebook args to Python kernels."""

DEFAULT_KERNEL_NAME = "python3"
"""The name of the kernel provided by the toolchain's Python environment."""


@dataclass(frozen=True)
class KernelSpec:  # pylint: disable=too-many-instance-attributes
    """A kernel definition as produced by the `jupyter_kernelspec` rule.

    File references in ``argv``, ``env`` and ``path_tools`` are rlocationpaths
    which :func:`configure_kernelspec` resolves.
    """

    name: str
    display_name: str
    language: str
    argv: list[str]
    env: dict[str, str] = field(default_factory=dict)
    interrupt_mode: str = ""
    args_template: str = ""
    """The code cell forwarding notebook args; ``{args}`` is replaced by a JSON
    array. Empty when the kernel does not take args."""
    transport: str = ""
    """The ZeroMQ transport (``ipc`` or ``tcp``); empty for the platform default."""
    path_tools: list[str] = field(default_factory=list)
    """rlocationpaths of executables; the directory of each resolved file is
    prepended to ``PATH``."""
    rlocations: list[str] = field(default_factory=list)
    """Every rlocationpath referenced by ``argv``, ``env`` or ``path_tools``."""

    @classmethod
    def from_json(cls, spec_file: Path, resolve: Callable[[str], Path]) -> "KernelSpec":
        """Load a kernelspec json file written by the `jupyter_kernelspec` rule.

        Args:
            spec_file: The json file.
            resolve: Resolves the rlocationpath of the args template file.
        """
        data = json.loads(spec_file.read_text(encoding="utf-8"))
        args_template = ""
        if data.get("args_template"):
            args_template = resolve(data["args_template"]).read_text(encoding="utf-8")
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            language=data["language"],
            argv=list(data["argv"]),
            env=dict(data.get("env", {})),
            interrupt_mode=data.get("interrupt_mode", ""),
            args_template=args_template,
            transport=data.get("transport", ""),
            path_tools=list(data.get("path_tools", [])),
            rlocations=list(data.get("rlocations", [])),
        )

    @classmethod
    def python(cls) -> "KernelSpec":
        """The kernel of the toolchain's own Python environment.

        This is what `ipykernel` installs as ``python3``, pinned to the
        interpreter running the wrapper so the kernel shares its venv.
        """
        return cls(
            name=DEFAULT_KERNEL_NAME,
            display_name="Python 3",
            language="python",
            argv=[
                sys.executable,
                "-m",
                "ipykernel_launcher",
                "-f",
                "{connection_file}",
            ],
            args_template=PYTHON_ARGS_TEMPLATE,
        )


def parse_kernelspec_rlocations(entries: list[str]) -> dict[str, Path]:
    """Parse ``rlocationpath=path`` flags into a lookup table.

    Args:
        entries: The raw ``--kernelspec_rlocation`` values.

    Returns:
        A mapping of rlocationpath to the path it resolves to.
    """
    paths = {}
    for entry in entries:
        rloc, sep, path = entry.partition("=")
        if not sep:
            raise ValueError(
                f"Invalid --kernelspec_rlocation {entry!r}: expected rlocationpath=path"
            )
        paths[rloc] = Path(path)
    return paths


def configure_kernelspec(
    spec: KernelSpec,
    data_dir: Path,
    resolve: Callable[[str], Path],
    extra_env: Optional[dict[str, str]] = None,
) -> Path:
    """Install a kernelspec so Jupyter can launch the kernel.

    A ``kernels/<name>/kernel.json`` file is written below *data_dir* with
    every rlocationpath replaced by the absolute path it resolves to, and
    *data_dir* is prepended to ``JUPYTER_PATH`` so the kernel takes
    precedence over kernels of the same name found in the Python
    environment.

    Args:
        spec: The kernelspec to install.
        data_dir: A writable Jupyter data directory.
        resolve: A function resolving an rlocationpath to a path.
        extra_env: Additional environment variables for the kernel process.

    Returns:
        The kernelspec directory.
    """
    resolved: dict[str, str] = {}
    for rloc in spec.rlocations:
        path = resolve(rloc)
        if not path.exists():
            raise FileNotFoundError(f"Kernel file not found: ({rloc}) {path}")
        # Absolute but unresolved so symlink farms (runfiles, sandboxes) keep
        # providing exactly the declared files.
        resolved[rloc] = str(path.absolute())

    # A single pass with longer paths first so an rlocationpath that is a
    # prefix of another (or of a substituted path) cannot corrupt it.
    pattern = re.compile(
        "|".join(re.escape(rloc) for rloc in sorted(resolved, key=len, reverse=True))
    )

    def _substitute(value: str) -> str:
        if not resolved:
            return value
        return pattern.sub(lambda match: resolved[match.group(0)], value)

    argv = [_substitute(arg) for arg in spec.argv]
    env = {key: _substitute(value) for key, value in spec.env.items()}

    if spec.path_tools:
        # The entries are files; their directories go on PATH.
        dirs = [str(Path(resolved[rloc]).parent) for rloc in spec.path_tools]
        # Jupyter substitutes `${PATH}` with the launching process' PATH.
        env["PATH"] = os.pathsep.join(dirs + [env.get("PATH", "${PATH}")])

    if extra_env:
        env.update(extra_env)

    kernel_json: dict[str, Any] = {
        "argv": argv,
        "display_name": spec.display_name,
        "language": spec.language,
        "env": env,
    }
    if spec.interrupt_mode:
        kernel_json["interrupt_mode"] = spec.interrupt_mode

    kernel_dir = data_dir / "kernels" / spec.name
    kernel_dir.mkdir(parents=True, exist_ok=True)
    (kernel_dir / "kernel.json").write_text(
        json.dumps(kernel_json, indent=2), encoding="utf-8"
    )

    existing = os.environ.get("JUPYTER_PATH", "")
    os.environ["JUPYTER_PATH"] = os.pathsep.join(
        [str(data_dir)] + ([existing] if existing else [])
    )
    logging.debug("Installed kernelspec `%s` at %s", spec.name, kernel_dir)

    return kernel_dir
