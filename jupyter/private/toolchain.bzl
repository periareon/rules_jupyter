"""Jupyter toolchain"""

load("@rules_venv//python:py_info.bzl", "PyInfo")

TOOLCHAIN_TYPE = str(Label("//jupyter:toolchain_type"))

def _jupyter_toolchain_impl(ctx):
    jupyter_target = ctx.attr.jupyter
    jupytext_target = ctx.attr.jupytext

    # For some reason, simply forwarding `DefaultInfo` from
    # the target results in a loss of data. To avoid this a
    # new provider is created with teh same info.
    default_info = DefaultInfo(
        files = jupyter_target[DefaultInfo].files,
        runfiles = jupyter_target[DefaultInfo].default_runfiles,
    )

    all_files = []
    for target in [ctx.attr.pandoc, ctx.attr.chromium]:
        if not target:
            continue
        if DefaultInfo not in target:
            continue

        # Include both files and runfiles for chromium (needs data files like icudtl.dat)
        all_files.append(target[DefaultInfo].files)
        if target[DefaultInfo].default_runfiles:
            all_files.append(target[DefaultInfo].default_runfiles.files)

    playwright_browsers_dir = None
    if ctx.file.playwright_browsers_dir:
        playwright_browsers_dir = ctx.file.playwright_browsers_dir
        all_files.append(depset([playwright_browsers_dir]))

    providers = [
        platform_common.ToolchainInfo(
            label = ctx.label,
            jupyter = jupyter_target,
            kernel = ctx.attr.kernel if ctx.attr.kernel else None,
            pandoc = ctx.executable.pandoc,
            chromium = ctx.file.chromium,
            jupytext = jupytext_target,
            playwright_browsers_dir = playwright_browsers_dir,
            default_cwd = ctx.attr.default_cwd,
            all_files = depset(transitive = all_files),
        ),
        default_info,
        jupyter_target[PyInfo],
    ]

    if OutputGroupInfo in jupyter_target:
        providers.append(jupyter_target[OutputGroupInfo])
    if InstrumentedFilesInfo in jupyter_target:
        providers.append(jupyter_target[InstrumentedFilesInfo])

    return providers

jupyter_toolchain = rule(
    doc = "Defines a Jupyter toolchain that provides Jupyter, Jupytext, Pandoc, and Playwright browser support.",
    implementation = _jupyter_toolchain_impl,
    attrs = {
        "default_cwd": attr.string(
            doc = "The default working directory mode for notebook execution. This value is used when `cwd` is not specified in `jupyter_report` or `jupyter_notebook_test` rules. `workspace_root` sets the working directory to the workspace root, while `notebook_root` sets it to the notebook's parent directory. This affects how relative paths in notebooks are resolved.",
            values = [
                "workspace_root",
                "notebook_root",
            ],
            default = "workspace_root",
        ),
        "jupyter": attr.label(
            doc = "The Jupyter Python package providing notebook execution capabilities.",
            mandatory = True,
            providers = [PyInfo],
        ),
        "jupytext": attr.label(
            doc = "The [Jupytext](https://jupytext.readthedocs.io/en/latest/) Python package for converting between notebook formats (e.g., .py to .ipynb).",
            mandatory = True,
            providers = [PyInfo],
        ),
        "kernel": attr.string(
            doc = "Default kernel name to use for notebook execution if not specified in the notebook (e.g., 'python3', 'rust').",
        ),
        "pandoc": attr.label(
            doc = "The Pandoc executable for converting notebooks to various output formats (HTML, LaTeX, PDF, etc.).",
            allow_single_file = True,
            cfg = "exec",
            executable = True,
        ),
        "playwright_browsers_dir": attr.label(
            doc = "A directory containing the results of `playwright install`.",
            allow_single_file = True,
        ),
    },
)

def _current_jupyter_toolchain_impl(ctx):
    toolchain = ctx.toolchains[TOOLCHAIN_TYPE]
    jupyter_target = toolchain.jupyter

    # For some reason, simply forwarding `DefaultInfo` from
    # the target results in a loss of data. To avoid this a
    # new provider is created with teh same info.
    default_info = DefaultInfo(
        files = jupyter_target[DefaultInfo].files,
        runfiles = jupyter_target[DefaultInfo].default_runfiles,
    )

    providers = [
        default_info,
        jupyter_target[PyInfo],
    ]

    if OutputGroupInfo in jupyter_target:
        providers.append(jupyter_target[OutputGroupInfo])
    if InstrumentedFilesInfo in jupyter_target:
        providers.append(jupyter_target[InstrumentedFilesInfo])

    return providers

current_jupyter_toolchain = rule(
    doc = "A convenience rule that provides access to the Jupyter Python package from the current Jupyter toolchain.",
    implementation = _current_jupyter_toolchain_impl,
    provides = [PyInfo],
    toolchains = [TOOLCHAIN_TYPE],
)

def _current_jupytext_toolchain_impl(ctx):
    toolchain = ctx.toolchains[TOOLCHAIN_TYPE]
    jupyter_target = toolchain.jupytext

    # For some reason, simply forwarding `DefaultInfo` from
    # the target results in a loss of data. To avoid this a
    # new provider is created with teh same info.
    default_info = DefaultInfo(
        files = jupyter_target[DefaultInfo].files,
        runfiles = jupyter_target[DefaultInfo].default_runfiles,
    )

    providers = [
        default_info,
        jupyter_target[PyInfo],
    ]

    if OutputGroupInfo in jupyter_target:
        providers.append(jupyter_target[OutputGroupInfo])
    if InstrumentedFilesInfo in jupyter_target:
        providers.append(jupyter_target[InstrumentedFilesInfo])

    return providers

current_jupytext_toolchain = rule(
    doc = "A convenience rule that provides access to the Jupytext Python package from the current Jupyter toolchain.",
    implementation = _current_jupytext_toolchain_impl,
    provides = [PyInfo],
    toolchains = [TOOLCHAIN_TYPE],
)
