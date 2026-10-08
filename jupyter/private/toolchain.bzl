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
    pandoc = None
    if ctx.attr.pandoc:
        pandoc = ctx.file.pandoc
        if DefaultInfo in ctx.attr.pandoc:
            all_files.extend([
                ctx.attr.pandoc[DefaultInfo].files,
                ctx.attr.pandoc[DefaultInfo].default_runfiles.files,
            ])

    playwright_browsers_dir = None
    if ctx.file.playwright_browsers_dir:
        playwright_browsers_dir = ctx.file.playwright_browsers_dir
        all_files.append(depset([playwright_browsers_dir]))

    playwright_ld_library_dir = None
    if ctx.attr.playwright_ld_library_dir:
        ld_lib_files = ctx.attr.playwright_ld_library_dir[DefaultInfo].files.to_list()
        if ld_lib_files:
            playwright_ld_library_dir = ld_lib_files[0]
            all_files.append(depset([playwright_ld_library_dir]))

    # LaTeX support is optional and its texmf trees are large, so the
    # files are tracked separately from `all_files` and only pulled into
    # actions and runfiles that actually produce PDF output.
    latex_engine = None
    latex_format = None
    latex_texmf_cnf = None
    bibtex = None
    latex_files = []
    if ctx.attr.latex_engine:
        if not ctx.attr.latex_format or not ctx.attr.latex_texmf_cnf:
            fail("`jupyter_toolchain.latex_format` and `jupyter_toolchain.latex_texmf_cnf` are required when `latex_engine` is set. Please update `{}`".format(
                ctx.label,
            ))
        latex_engine = ctx.file.latex_engine
        latex_format = ctx.file.latex_format
        latex_texmf_cnf = ctx.file.latex_texmf_cnf
        latex_files.extend([
            ctx.attr.latex_engine[DefaultInfo].files,
            ctx.attr.latex_engine[DefaultInfo].default_runfiles.files,
            depset([latex_format, latex_texmf_cnf]),
        ])
        for target in ctx.attr.latex_data:
            latex_files.append(target[DefaultInfo].files)
        if ctx.attr.bibtex:
            bibtex = ctx.file.bibtex
            latex_files.extend([
                ctx.attr.bibtex[DefaultInfo].files,
                ctx.attr.bibtex[DefaultInfo].default_runfiles.files,
            ])
    elif ctx.attr.latex_format or ctx.attr.latex_texmf_cnf or ctx.attr.latex_data or ctx.attr.bibtex:
        fail("`jupyter_toolchain.latex_engine` must be set when any of `latex_format`, `latex_texmf_cnf`, `latex_data` or `bibtex` are set. Please update `{}`".format(
            ctx.label,
        ))

    providers = [
        platform_common.ToolchainInfo(
            label = ctx.label,
            default_cwd_mode = ctx.attr.cwd_mode if ctx.attr.cwd_mode else None,
            default_kernel = ctx.attr.kernel if ctx.attr.kernel else None,
            default_exporter_args = ctx.attr.exporter_args,
            jupyter = jupyter_target,
            jupytext = jupytext_target,
            pandoc = pandoc,
            playwright_browsers_dir = playwright_browsers_dir,
            playwright_ld_library_dir = playwright_ld_library_dir,
            latex_engine = latex_engine,
            latex_format = latex_format,
            latex_texmf_cnf = latex_texmf_cnf,
            bibtex = bibtex,
            latex_files = depset(transitive = latex_files),
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
    doc = """\
Defines a Jupyter toolchain that provides Jupyter, Jupytext, Pandoc, Playwright browser, and LaTeX support.

LaTeX (used for `pdf` reports) is optional. The [texlive](https://registry.bazel.build/modules/texlive)
module from the Bazel Central Registry provides everything required:

```python
jupyter_toolchain(
    name = "jupyter_toolchain",
    jupyter = "@pip_deps//jupyter",
    jupytext = "@pip_deps//jupytext",
    pandoc = "@pandoc",
    latex_engine = "@texlive//texk/web2c:pdftex",
    latex_format = "@texlive//:pdflatex_fmt",
    latex_texmf_cnf = "@texlive-texmf//:web2c/texmf.cnf",
    latex_data = [
        "@texlive//:texmf/fonts",
        "@texlive//:texmf/tex_inputs",
        "@texlive//:texmf/web2c_data",
    ],
    bibtex = "@texlive//texk/bibtex-x:bibtex8",
)
```
""",
    implementation = _jupyter_toolchain_impl,
    attrs = {
        "bibtex": attr.label(
            doc = "An optional BibTeX executable (e.g. `@texlive//texk/bibtex-x:bibtex8`). When unset, the bibliography pass of PDF generation is skipped.",
            allow_single_file = True,
            cfg = "exec",
            executable = True,
        ),
        "cwd_mode": attr.string(
            doc = "The default working directory mode for notebook execution. This value is used when `cwd_mode` is not specified in `jupyter_report` or `jupyter_notebook_test` rules. `workspace_root` sets the working directory to the workspace root, while `notebook_root` sets it to the notebook's parent directory. This affects how relative paths in notebooks are resolved.",
            values = [
                "execution_root",
                "notebook_root",
            ],
            default = "execution_root",
        ),
        "exporter_args": attr.string_list(
            doc = "Default traitlets-style flags forwarded to nbconvert exporters for all rules using this toolchain (e.g. ``--WebPDFExporter.exclude_input=true``). Per-rule ``exporter_args`` are appended after these defaults, allowing overrides.",
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
        "latex_data": attr.label_list(
            doc = "texmf trees (fonts, macro packages, `web2c` configuration) required by `latex_engine` at runtime. These files are only added to actions and runfiles that produce PDF output.",
            allow_files = True,
        ),
        "latex_engine": attr.label(
            doc = "A TeX engine executable used for `pdf` reports (e.g. `@texlive//texk/web2c:pdftex`). Requires `latex_format` and `latex_texmf_cnf`.",
            allow_single_file = True,
            cfg = "exec",
            executable = True,
        ),
        "latex_format": attr.label(
            doc = "A precompiled LaTeX format file for `latex_engine` (e.g. `@texlive//:pdflatex_fmt`). The engine is invoked with `-fmt=<stem>`.",
            allow_single_file = [".fmt"],
        ),
        "latex_texmf_cnf": attr.label(
            doc = "The `web2c/texmf.cnf` file of the texmf tree (e.g. `@texlive-texmf//:web2c/texmf.cnf`). Its directory becomes `TEXMFCNF` and its parent becomes `TEXMF`.",
            allow_single_file = True,
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
        "playwright_ld_library_dir": attr.label(
            doc = "A directory of shared libraries to prepend to LD_LIBRARY_PATH when launching browsers.",
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
