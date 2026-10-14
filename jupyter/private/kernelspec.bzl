"""jupyter_kernelspec"""

load(":providers.bzl", "JupyterKernelspecInfo")

def rlocationpath(file, workspace_name):
    """Compute the rlocationpath of a file.

    Args:
        file (File): The file.
        workspace_name (str): The name of the main workspace (`ctx.workspace_name`).

    Returns:
        str: The runfiles path of the file.
    """
    if file.short_path.startswith("../"):
        return file.short_path[len("../"):]

    return "{}/{}".format(workspace_name, file.short_path)

def _jupyter_kernelspec_impl(ctx):
    kernel_name = ctx.attr.kernel_name or ctx.label.name
    display_name = ctx.attr.display_name or kernel_name

    targets = ctx.attr.data + ctx.attr.path_tools

    argv = [ctx.expand_location(arg, targets) for arg in ctx.attr.argv]
    env = {key: ctx.expand_location(value, targets) for key, value in ctx.attr.env.items()}

    args_template = ctx.file.args_template
    files = []
    runfiles = ctx.runfiles(files = [args_template] if args_template else [])
    tools = []
    for target in targets:
        info = target[DefaultInfo]
        files.append(info.files)
        runfiles = runfiles.merge(info.default_runfiles)
        if info.files_to_run and info.files_to_run.executable:
            tools.append(info.files_to_run)

    path_tools = []
    for target in ctx.attr.path_tools:
        tool_files = target[DefaultInfo].files.to_list()
        if len(tool_files) != 1:
            fail("`jupyter_kernelspec.path_tools` entries must provide exactly one file but `{}` provides {}. Please update `{}`".format(
                target.label,
                len(tool_files),
                ctx.label,
            ))
        path_tools.append(rlocationpath(tool_files[0], ctx.workspace_name))

    # Only files directly referenced by the launch configuration need to
    # have their paths resolved at runtime.
    strings = argv + env.values()
    rlocations = {}
    for file in ctx.files.data:
        rloc = rlocationpath(file, ctx.workspace_name)
        for value in strings:
            if rloc in value:
                rlocations[rloc] = file
                break
    for target in ctx.attr.path_tools:
        file = target[DefaultInfo].files.to_list()[0]
        rlocations[rlocationpath(file, ctx.workspace_name)] = file
    if args_template:
        rlocations[rlocationpath(args_template, ctx.workspace_name)] = args_template

    spec = ctx.actions.declare_file("{}.kernelspec.json".format(ctx.label.name))
    ctx.actions.write(
        output = spec,
        content = json.encode_indent(struct(
            name = kernel_name,
            display_name = display_name,
            language = ctx.attr.language,
            argv = argv,
            env = env,
            interrupt_mode = ctx.attr.interrupt_mode,
            args_template = rlocationpath(args_template, ctx.workspace_name) if args_template else "",
            transport = ctx.attr.transport,
            path_tools = path_tools,
            rlocations = sorted(rlocations.keys()),
        ), indent = " " * 4) + "\n",
    )

    return [
        DefaultInfo(
            files = depset([spec]),
            runfiles = runfiles,
        ),
        JupyterKernelspecInfo(
            args_template = args_template,
            argv = argv,
            display_name = display_name,
            env = env,
            files = depset(transitive = files + [runfiles.files]),
            interrupt_mode = ctx.attr.interrupt_mode,
            kernel_name = kernel_name,
            language = ctx.attr.language,
            path_tools = path_tools,
            rlocations = rlocations,
            runfiles = runfiles,
            spec = spec,
            tools = tools,
            transport = ctx.attr.transport,
        ),
    ]

jupyter_kernelspec = rule(
    doc = """\
Defines a [Jupyter kernel](https://jupyter-client.readthedocs.io/en/latest/kernels.html) that notebooks can be executed with.

The rule is language agnostic. It describes how to launch a kernel process in the same way a
`kernel.json` file does, but with files tracked by Bazel. Kernels are attached to a
`jupyter_toolchain` via its `kernels` attribute and selected by notebooks using
`jupyter_notebook.kernel` (or `jupyter_toolchain.kernel` for a default).

File references in `argv` and `env` use `$(rlocationpath ...)` expansion over the targets in
`data`. The rules resolve them to real paths wherever the notebook is executed (build actions,
tests, `bazel run` and Jupyter Lab). Jupyter's own `{connection_file}` placeholder and `${VAR}`
environment substitution continue to work.

Example:

```python
jupyter_kernelspec(
    name = "julia",
    display_name = "Julia",
    language = "julia",
    argv = [
        "$(rlocationpath :ijulia_kernel)",
        "{connection_file}",
    ],
    data = [":ijulia_kernel"],
    # A file containing `empty!(ARGS); append!(ARGS, {args})`.
    args_template = "args_template.jl",
)

jupyter_toolchain(
    name = "jupyter_toolchain",
    kernels = [":julia"],
    ...
)

jupyter_notebook(
    name = "notebook",
    src = "notebook.jl",
    kernel = "julia",
)
```
""",
    implementation = _jupyter_kernelspec_impl,
    attrs = {
        "args_template": attr.label(
            doc = (
                "A file holding a code cell template used to forward `args` of `jupyter_notebook_test`, " +
                "`jupyter_notebook_binary`, `jupyter_report` and `jupyter_lab` to the notebook. The cell is prepended to " +
                "the notebook before execution. The only placeholder is `{args}`, replaced by a JSON array of the " +
                "arguments (e.g. a file containing `empty!(ARGS); append!(ARGS, {args})` for Julia); other braces are " +
                "left as they are. When unset, notebooks using this kernel cannot be given `args`."
            ),
            allow_single_file = True,
        ),
        "argv": attr.string_list(
            doc = (
                "The command used to launch the kernel. Supports `$(rlocationpath ...)` expansion for targets in `data` " +
                "and `path_tools` as well as Jupyter's `{connection_file}` placeholder."
            ),
            mandatory = True,
        ),
        "data": attr.label_list(
            doc = "Files and executables required by the kernel at runtime. These are the targets available for `$(rlocationpath ...)` expansion.",
            allow_files = True,
        ),
        "display_name": attr.string(
            doc = "The human readable name of the kernel. Defaults to `kernel_name`.",
        ),
        "env": attr.string_dict(
            doc = (
                "Environment variables for the kernel process. Values support `$(rlocationpath ...)` expansion and " +
                "Jupyter's `${VAR}` substitution with the environment of the process launching the kernel."
            ),
        ),
        "interrupt_mode": attr.string(
            doc = "How the kernel is interrupted. `signal` sends `SIGINT`, `message` sends an `interrupt_request`. Defaults to Jupyter's default (`signal`).",
            values = ["", "signal", "message"],
        ),
        "kernel_name": attr.string(
            doc = "The name of the kernel as referenced by `jupyter_notebook.kernel` and notebook metadata. Defaults to the target name.",
        ),
        "language": attr.string(
            doc = "The language of the kernel (e.g. `python`, `julia`, `rust`). Recorded in notebook metadata and used by exporters for syntax highlighting.",
            mandatory = True,
        ),
        "path_tools": attr.label_list(
            doc = (
                "Executables whose parent directories are prepended to `PATH` for the kernel process. Useful for kernels that " +
                "shell out to compilers or interpreters. Each target must provide exactly one file."
            ),
            allow_files = True,
        ),
        "transport": attr.string(
            doc = (
                "The ZeroMQ transport used to talk to the kernel. Defaults to `ipc` on Unix, which avoids port collisions " +
                "between notebooks Bazel runs in parallel, and `tcp` on Windows. Kernels whose ZeroMQ lacks IPC support " +
                "(e.g. prebuilt `evcxr_jupyter` binaries) must set `tcp`."
            ),
            values = ["", "ipc", "tcp"],
        ),
    },
    provides = [JupyterKernelspecInfo],
)
