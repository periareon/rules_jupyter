"""# Jupyter rules"""

load("@rules_venv//python:py_info.bzl", "PyInfo")
load("@rules_venv//python/venv:defs.bzl", "py_venv_common")
load(":kernelspec.bzl", "rlocationpath")
load(":providers.bzl", "JupyterNotebookInfo")
load(":rules_venv_aspects.bzl", "aspects_provider")
load(":toolchain.bzl", "TOOLCHAIN_TYPE")

_rlocationpath = rlocationpath

# Build actions only reference files through `Args` so Bazel may rewrite
# output paths (`--experimental_output_paths=strip`).
_PATH_MAPPING_REQUIREMENTS = {"supports-path-mapping": "1"}

# Every report the rules can produce, mirrored by `REPORT_FORMATS` in
# `tools/process_wrappers/exporters.py`. `requires` names the toolchain
# attribute a report depends on; `output` and `template` name the
# `jupyter_report` attributes driving it.
_REPORTS = {
    "html": struct(output = "out_html", template = "out_html_template_type", requires = None),
    "latex": struct(output = "out_latex", template = "out_latex_template_type", requires = None),
    "markdown": struct(output = "out_markdown", template = None, requires = "pandoc"),
    "pdf": struct(output = "out_pdf", template = None, requires = "latex_engine"),
    "rst": struct(output = "out_rst", template = None, requires = None),
    "webpdf": struct(output = "out_webpdf", template = None, requires = "playwright_browsers_dir"),
}

_REPORTS_DOC = (
    "Valid values: `html`, `latex`, `markdown` (requires `jupyter_toolchain.pandoc`), `pdf` (requires " +
    "`jupyter_toolchain.latex_engine`), `rst`, `webpdf` (requires `jupyter_toolchain.playwright_browsers_dir`)."
)

_CWD_MODE_VALUES = [
    "execution_root",
    "notebook_root",
]

def _resolve_kernel(toolchain, kernel):
    """Determine the kernel a notebook should be executed with.

    Args:
        toolchain (ToolchainInfo): The current `jupyter_toolchain`.
        kernel (str): The kernel requested by the notebook, if any.

    Returns:
        struct: `name` (str or None), the kernel name to request and `spec`
            (JupyterKernelspecInfo or None), the matching toolchain kernel.
    """
    if not kernel:
        kernel = toolchain.default_kernel
    spec = None
    if kernel and kernel in toolchain.kernels:
        spec = toolchain.kernels[kernel]
    return struct(name = kernel or None, spec = spec)

def _check_kernel_args(ctx, kernelspec, args):
    """Ensure a kernel is able to receive notebook args.

    Args:
        ctx (ctx): The rule's context object.
        kernelspec (JupyterKernelspecInfo): The kernel in use, if any.
        args (list): The notebook args.
    """
    if args and kernelspec and not kernelspec.args_template:
        fail("Kernel `{}` does not define `jupyter_kernelspec.args_template` so notebooks using it cannot be given `args`. Please update `{}`".format(
            kernelspec.kernel_name,
            ctx.label,
        ))

def _check_reports(ctx, toolchain, reports):
    """Ensure the current toolchain can produce the requested reports.

    Args:
        ctx (ctx): The rule's context object.
        toolchain (ToolchainInfo): The current `jupyter_toolchain`.
        reports (list[str]): The requested report names.
    """
    for report in reports:
        if report not in _REPORTS:
            fail("Invalid report `{}` requested by `{}`. {}".format(
                report,
                ctx.label,
                _REPORTS_DOC,
            ))
        requires = _REPORTS[report].requires
        if requires and not getattr(toolchain, requires):
            fail("`jupyter_toolchain.{}` is not set on the current toolchain yet {} reports were requested by `{}`. Please update `{}`".format(
                requires,
                report,
                ctx.label,
                toolchain.label,
            ))

def _add_kernelspec_args(args, kernelspec, workspace_name = None):
    """Add the kernelspec flags understood by the process wrappers.

    Args:
        args (Args): The args object to extend.
        kernelspec (JupyterKernelspecInfo): The kernel to install.
        workspace_name (str, optional): When set, paths are rendered as
            rlocationpaths and resolved via runfiles at runtime. Otherwise
            execpaths are provided for every file the kernel references.
    """
    if workspace_name == None:
        args.add("--kernelspec", kernelspec.spec)
        rlocs = {file: rloc for rloc, file in kernelspec.rlocations.items()}

        def _rlocation_arg(file):
            # `file.path` is path-mapped within `map_each`.
            return "{}={}".format(rlocs[file], file.path)

        args.add_all(
            rlocs.keys(),
            map_each = _rlocation_arg,
            format_each = "--kernelspec_rlocation=%s",
            allow_closure = True,
            expand_directories = False,
        )
    else:
        args.add("--kernelspec", _rlocationpath(kernelspec.spec, workspace_name))

def _notebook_args(ctx, toolchain, notebook_info, reports, workspace_name = None):
    """Build the command line flags shared by every process wrapper.

    Args:
        ctx (ctx): The rule's context object.
        toolchain (ToolchainInfo): The current `jupyter_toolchain`.
        notebook_info (JupyterNotebookInfo): The notebook to run.
        reports (list[str]): The report names requested by the rule.
        workspace_name (str, optional): When set, files are rendered as
            rlocationpaths for runfiles lookups. Otherwise files are passed
            as-is so their paths can be mapped within actions.

    Returns:
        struct: `args` (Args), `kernel` (see `_resolve_kernel`) and `files`
            (list[depset]), the toolchain files the wrapper needs.
    """
    kernel = _resolve_kernel(toolchain, notebook_info.kernel)
    _check_kernel_args(ctx, kernel.spec, ctx.attr.args)
    _check_reports(ctx, toolchain, reports)

    args = ctx.actions.args()
    args.set_param_file_format("multiline")

    def _add_path(flag, file):
        if workspace_name != None:
            file = _rlocationpath(file, workspace_name)

        # Directories are added without expansion so their (path-mapped) path is used.
        args.add_all(flag, [file], expand_directories = False)

    _add_path("--notebook", notebook_info.notebook)
    args.add("--cwd_mode", ctx.attr.cwd_mode or toolchain.default_cwd_mode or "execution_root")
    if kernel.name:
        args.add("--kernel", kernel.name)
    if kernel.spec:
        _add_kernelspec_args(args, kernel.spec, workspace_name)

    files = [toolchain.all_files]
    if toolchain.pandoc:
        _add_path("--pandoc", toolchain.pandoc)
    if toolchain.playwright_browsers_dir:
        _add_path("--playwright_browsers_dir", toolchain.playwright_browsers_dir)
    if toolchain.playwright_ld_library_dir:
        _add_path("--ld_library_dir", toolchain.playwright_ld_library_dir)
    if "pdf" in reports:
        _add_path("--latex_engine", toolchain.latex_engine)
        _add_path("--latex_format", toolchain.latex_format)
        _add_path("--latex_texmf_cnf", toolchain.latex_texmf_cnf)
        if toolchain.bibtex:
            _add_path("--bibtex", toolchain.bibtex)
        files.append(toolchain.latex_files)

    exporter_args = toolchain.default_exporter_args + getattr(ctx.attr, "exporter_args", [])
    args.add_all(exporter_args, format_each = "--exporter_arg=%s")

    return struct(args = args, kernel = kernel, files = files)

def _known_variables(ctx):
    """Collect `TemplateVariableInfo` variables from the rule's toolchains."""
    known_variables = {}
    for target in ctx.attr.toolchains:
        if platform_common.TemplateVariableInfo in target:
            variables = getattr(target[platform_common.TemplateVariableInfo], "variables", {})
            known_variables.update(variables)
    return known_variables

def _jupyter_notebook_impl(ctx):
    toolchain = ctx.toolchains[TOOLCHAIN_TYPE]
    kernel = _resolve_kernel(toolchain, ctx.attr.kernel)

    dep_info = py_venv_common.create_dep_info(
        ctx = ctx,
        deps = ctx.attr.deps,
    )

    py_info = py_venv_common.create_py_info(
        ctx = ctx,
        imports = [],
        srcs = [ctx.file.src],
        dep_info = dep_info,
    )

    notebook = ctx.file.src
    if not notebook.basename.endswith(".ipynb"):
        args = ctx.actions.args()
        args.add("--notebook", notebook)

        name = notebook.path[len(notebook.root.path):].strip("/")
        if ctx.label.package:
            _, _, name = name.partition(ctx.label.package)

        stem, _, _ = name.strip("/").rpartition(".")
        out_notebook = ctx.actions.declare_file("{}.ipynb".format(stem))
        args.add("--out_notebook", out_notebook)

        if kernel.name:
            args.add("--kernel", kernel.name)
        if kernel.spec:
            args.add("--kernel_display_name", kernel.spec.display_name)
            args.add("--kernel_language", kernel.spec.language)

        ctx.actions.run(
            mnemonic = "JupyterCompile",
            executable = ctx.executable._compiler,
            arguments = [args],
            outputs = [out_notebook],
            inputs = [notebook],
            execution_requirements = _PATH_MAPPING_REQUIREMENTS,
            # The compiler is an implicit dependency rather than a toolchain tool.
            toolchain = None,
        )

        notebook = out_notebook

    return [
        DefaultInfo(
            files = depset([notebook]),
            runfiles = ctx.runfiles(files = [ctx.file.src] + ctx.files.data).merge(dep_info.runfiles),
        ),
        JupyterNotebookInfo(
            kernel = ctx.attr.kernel,
            notebook = notebook,
            src = ctx.file.src,
            data = depset(ctx.files.data),
        ),
        aspects_provider(ctx, ctx.file.src),
        py_info,
    ]

jupyter_notebook = rule(
    doc = """\
Compiles a Jupyter notebook from source and prepares it for execution.

This rule processes notebook source files and converts them to the standard `.ipynb` format.
If the source is a script in [Jupytext](https://jupytext.readthedocs.io/en/latest/) format
(e.g. a `.py`, `.jl` or `.rs` file with `# %%` / `// %%` cell markers), it will be converted
to `.ipynb` format. If the source is already a `.ipynb` file, it is used directly.

The kernel a notebook runs with is selected by name. Kernels defined with `jupyter_kernelspec`
and registered on the `jupyter_toolchain` are used when their name matches; otherwise the kernel
must be discoverable from the toolchain's Jupyter Python environment (e.g. `python3`).

Example:

```python
jupyter_notebook(
    name = "my_notebook",
    src = "notebook.py",  # or "notebook.ipynb"
    kernel = "python3",   # optional
    deps = ["@pip_deps//polars"],
    data = ["data.csv"],
)
```
""",
    implementation = _jupyter_notebook_impl,
    attrs = {
        "data": attr.label_list(
            doc = "Additional data files required by the notebook (e.g., input data files, images, configuration files).",
            allow_files = True,
        ),
        "deps": attr.label_list(
            doc = "Python dependencies required by the notebook. These are typically Python packages needed for code execution.",
            providers = [PyInfo],
        ),
        "kernel": attr.string(
            doc = "The name of the Jupyter kernel to use for executing the notebook (e.g., `python3`, `rust`). Matches `jupyter_kernelspec.kernel_name` of the kernels registered on the toolchain. If not specified, the default kernel from the toolchain is used.",
        ),
        "src": attr.label(
            doc = "The notebook source file. Can be either a `.ipynb` file or a script in [Jupytext](https://jupytext.readthedocs.io/en/latest/) format (e.g. `.py`, `.jl`, `.rs` with `# %%` or `// %%` cell markers).",
            allow_single_file = True,
            mandatory = True,
        ),
        "_compiler": attr.label(
            cfg = "exec",
            executable = True,
            default = Label("//tools/process_wrappers:compiler"),
        ),
    },
    provides = [
        JupyterNotebookInfo,
        PyInfo,
    ],
    toolchains = [TOOLCHAIN_TYPE],
)

def _create_executable(ctx, notebook, runner, runner_main, cfg = "target"):
    venv_toolchain = py_venv_common.get_toolchain(ctx, cfg = cfg)

    dep_info = py_venv_common.create_dep_info(
        ctx = ctx,
        deps = [notebook, runner],
    )

    py_info = py_venv_common.create_py_info(
        ctx = ctx,
        imports = [],
        srcs = [runner_main],
        dep_info = dep_info,
    )

    executable, runfiles = py_venv_common.create_venv_entrypoint(
        ctx = ctx,
        venv_toolchain = venv_toolchain,
        py_info = py_info,
        main = runner_main,
        use_runfiles_in_entrypoint = False if cfg == "exec" else True,
        force_runfiles = True if cfg == "exec" else False,
        runfiles = dep_info.runfiles,
    )

    return executable, runfiles

def _expand_args(ctx, args, targets, known_variables):
    expanded = []
    for arg in args:
        expanded.append(ctx.expand_make_variables(
            arg,
            ctx.expand_location(arg, targets),
            known_variables,
        ))

    return expanded

def _expand_env(ctx, env, targets, known_variables):
    expanded_env = {}
    for key, value in env.items():
        expanded_env[key] = ctx.expand_make_variables(
            key,
            ctx.expand_location(value, targets),
            known_variables,
        )
    return expanded_env

def _jupyter_report_impl(ctx):
    toolchain = ctx.toolchains[TOOLCHAIN_TYPE]
    notebook_info = ctx.attr.notebook[JupyterNotebookInfo]

    reports = [name for name, report in _REPORTS.items() if getattr(ctx.outputs, report.output)]
    common = _notebook_args(ctx, toolchain, notebook_info, reports)
    args = common.args

    out_notebook = ctx.outputs.out_notebook
    if not out_notebook:
        out_notebook = ctx.actions.declare_file("{}.ipynb".format(ctx.label.name))
    args.add("--out_notebook", out_notebook)

    outputs = {"jupyter_report_notebook": out_notebook}
    for name in reports:
        report = _REPORTS[name]
        out = getattr(ctx.outputs, report.output)
        outputs["jupyter_report_{}".format(name)] = out
        args.add("--report", out, format = name + "=%s")
        template = getattr(ctx.attr, report.template) if report.template else None
        if template:
            args.add("--report_template", template, format = name + "=%s")

    args.add("--")

    known_variables = _known_variables(ctx)
    args.add_all(_expand_args(ctx, ctx.attr.args, ctx.attr.data, known_variables))
    env = _expand_env(ctx, ctx.attr.env, ctx.attr.data, known_variables)

    reporter, runfiles = _create_executable(
        ctx = ctx,
        cfg = "exec",
        runner = ctx.attr._reporter,
        runner_main = ctx.file._reporter_main,
        notebook = ctx.attr.notebook,
    )

    kernel_inputs = []
    kernel_tools = []
    if common.kernel.spec:
        kernel_inputs = [common.kernel.spec.files, depset([common.kernel.spec.spec])]
        kernel_tools = common.kernel.spec.tools

    ctx.actions.run(
        mnemonic = "JupyterReport",
        progress_message = "JupyterReport %{label}",
        executable = reporter,
        arguments = [args],
        inputs = depset([notebook_info.notebook] + ctx.files.data, transitive = [notebook_info.data] + common.files + kernel_inputs),
        outputs = outputs.values(),
        tools = [depset(transitive = [runfiles.files] + common.files)] + kernel_tools,
        env = env | ctx.configuration.default_shell_env,
        # TODO: Declare `_PATH_MAPPING_REQUIREMENTS` once rules_venv entrypoints
        # created with `use_runfiles_in_entrypoint = False` stop embedding
        # execpaths in the entrypoint script and runfiles collection. All paths
        # on this command line are already passed through `Args`.
        # Pandoc, LaTeX, browsers and kernels come from the Jupyter toolchain.
        toolchain = TOOLCHAIN_TYPE,
    )

    return [
        DefaultInfo(
            files = depset([out_notebook]),
        ),
        OutputGroupInfo(**{
            key: depset([out])
            for key, out in outputs.items()
        }),
    ]

jupyter_report = rule(
    doc = "Executes a Jupyter notebook and generates reports in various formats (HTML, Markdown, LaTeX, PDF, RST, WebPDF).",
    implementation = _jupyter_report_impl,
    attrs = {
        "args": attr.string_list(
            doc = "Additional command-line arguments to pass to the notebook execution.",
        ),
        "cwd_mode": attr.string(
            doc = "The working directory mode for notebook execution. If not specified, uses the `jupyter_toolchain.cwd`.",
            values = _CWD_MODE_VALUES,
        ),
        "data": attr.label_list(
            doc = "Additional data files required by the notebook (e.g., input data files, images, configuration files).",
            allow_files = True,
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when executing the notebook. Values support location expansion (e.g., `$(location :target)`).",
        ),
        "exporter_args": attr.string_list(
            doc = "Traitlets-style flags forwarded to nbconvert exporters (e.g. ``--WebPDFExporter.exclude_input=true``).",
        ),
        "notebook": attr.label(
            doc = "The notebook to execute and convert. Must be a `jupyter_notebook` target.",
            providers = [JupyterNotebookInfo, PyInfo],
            mandatory = True,
        ),
        "out_html": attr.output(
            doc = "Output path for an HTML report. If specified, the notebook will be converted to HTML format.",
        ),
        "out_html_template_type": attr.string(
            doc = "Template type for HTML output.",
            values = [
                "full",
                "basic",
            ],
        ),
        "out_latex": attr.output(
            doc = "Output path for a LaTeX report. If specified, the notebook will be converted to LaTeX format.",
        ),
        "out_latex_template_type": attr.string(
            doc = "Document layout for LaTeX output. `article` (the nbconvert default) or `report`.",
            values = [
                "article",
                "report",
            ],
        ),
        "out_markdown": attr.output(
            doc = "Output path for a Markdown report. If specified, the notebook will be converted to Markdown format. Requires `jupyter_toolchain.pandoc`.",
        ),
        "out_notebook": attr.output(
            doc = "Output path for the executed notebook (`.ipynb` file with cell outputs). If not specified, a default name is generated.",
        ),
        "out_pdf": attr.output(
            doc = "Output path for a PDF report generated via LaTeX. Requires `jupyter_toolchain.latex_engine`. For a browser rendered PDF that does not need LaTeX see `out_webpdf`.",
        ),
        "out_rst": attr.output(
            doc = "Output path for a reStructuredText report. If specified, the notebook will be converted to RST format.",
        ),
        "out_webpdf": attr.output(
            doc = "Output path for a WebPDF report (generated via Playwright/Chromium). If specified, the notebook will be converted to PDF format using headless browser rendering. Requires `jupyter_toolchain.playwright_browsers_dir`.",
        ),
        "_py_venv_toolchain": attr.label(
            doc = "A py_venv_toolchain in the exec configuration.",
            cfg = "exec",
            default = Label("@rules_venv//python/venv:current_py_venv_toolchain"),
        ),
        "_reporter": attr.label(
            cfg = "exec",
            default = Label("//tools/process_wrappers:reporter"),
        ),
        "_reporter_main": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = Label("//tools/process_wrappers:reporter.py"),
        ),
    },
    toolchains = [TOOLCHAIN_TYPE],
)

def _create_run_environment_info(ctx, env, env_inherit, targets, known_variables):
    """Create an environment info provider

    This macro performs location expansions.

    Args:
        ctx (ctx): The rule's context object.
        env (dict): Environment variables to set.
        env_inherit (list): Environment variables to inehrit from the host.
        targets (List[Target]): Targets to use in location expansion.
        known_variables (dict): A map of `TemplateVariableInfo` variables.

    Returns:
        RunEnvironmentInfo: The provider.
    """

    expanded_env = {}
    for key, value in env.items():
        expanded_env[key] = ctx.expand_make_variables(
            key,
            ctx.expand_location(value, targets),
            known_variables,
        )

    workspace_name = ctx.label.workspace_name
    if not workspace_name:
        workspace_name = ctx.workspace_name

    if not workspace_name:
        workspace_name = "_main"

    # Needed for bzlmod-aware runfiles resolution.
    expanded_env["REPOSITORY_NAME"] = workspace_name

    return RunEnvironmentInfo(
        environment = expanded_env,
        inherited_environment = env_inherit,
    )

def _kernel_runfiles(ctx, kernelspec):
    """Collect the runfiles required to launch a kernel.

    Args:
        ctx (ctx): The rule's context object.
        kernelspec (JupyterKernelspecInfo): The kernel.

    Returns:
        runfiles: The kernel's runfiles.
    """
    return ctx.runfiles(
        files = [kernelspec.spec],
        transitive_files = kernelspec.files,
    ).merge(kernelspec.runfiles)

def _runner_providers(ctx, common, runner, runner_main, args_file_var, env = {}, extra_files = []):
    """Create the executable of a wrapper launched by `bazel run` or `bazel test`.

    The flags are written to an args file the wrapper reads from the
    environment, leaving the command line itself to the user (and to Bazel,
    which appends `args`).

    Args:
        ctx (ctx): The rule's context object.
        common (struct): The result of `_notebook_args`.
        runner (Target): The wrapper's `py_binary`.
        runner_main (File): The wrapper's main source file.
        args_file_var (str): The environment variable naming the args file.
        env (dict, optional): Additional environment variables.
        extra_files (list[File], optional): Additional runfiles.

    Returns:
        list: `DefaultInfo` and `RunEnvironmentInfo` providers.
    """
    notebook_info = ctx.attr.notebook[JupyterNotebookInfo]

    args_file = ctx.actions.declare_file("{}.args.txt".format(ctx.label.name))
    ctx.actions.write(
        output = args_file,
        content = common.args,
    )

    executable, runfiles = _create_executable(
        ctx = ctx,
        cfg = "target",
        runner = runner,
        runner_main = runner_main,
        notebook = ctx.attr.notebook,
    )

    runfiles = runfiles.merge(ctx.runfiles(
        [executable, args_file, notebook_info.notebook] + ctx.files.data + extra_files,
        transitive_files = depset(transitive = [notebook_info.data] + common.files),
    ))
    if common.kernel.spec:
        runfiles = runfiles.merge(_kernel_runfiles(ctx, common.kernel.spec))

    return [
        DefaultInfo(
            executable = executable,
            runfiles = runfiles,
        ),
        _create_run_environment_info(
            ctx = ctx,
            env = ctx.attr.env | {
                args_file_var: _rlocationpath(args_file, ctx.workspace_name),
            } | env,
            env_inherit = ctx.attr.env_inherit,
            targets = ctx.attr.data,
            known_variables = _known_variables(ctx),
        ),
    ]

def _jupyter_notebook_test_impl(ctx):
    toolchain = ctx.toolchains[TOOLCHAIN_TYPE]
    notebook_info = ctx.attr.notebook[JupyterNotebookInfo]

    common = _notebook_args(ctx, toolchain, notebook_info, ctx.attr.reports, ctx.workspace_name)
    common.args.add_all(ctx.attr.reports, format_each = "--report=%s")

    # Bazel appends `args` to the command line of tests, so the args file only
    # marks where the notebook args begin. Test args are always forwarded to
    # the notebook and never to the runner.
    common.args.add("--")

    return _runner_providers(
        ctx,
        common,
        runner = ctx.attr._tester,
        runner_main = ctx.file._tester_main,
        args_file_var = "RULES_JUPYTER_TEST_ARGS_FILE",
    )

jupyter_notebook_test = rule(
    doc = "A test rule that executes a Jupyter notebook and optionally generates reports. The test fails if any notebook cell raises an error.",
    implementation = _jupyter_notebook_test_impl,
    attrs = {
        "cwd_mode": attr.string(
            doc = "The working directory mode for notebook execution. If not specified, uses the toolchain's `default_cwd`.",
            values = _CWD_MODE_VALUES,
        ),
        "data": attr.label_list(
            doc = "Additional data files required by the notebook (e.g., input data files, images, configuration files).",
            allow_files = True,
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when executing the notebook. Values support location expansion (e.g., $(location :target)).",
        ),
        "env_inherit": attr.string_list(
            doc = "Specifies additional environment variables to inherit from the external environment when the test is executed by `bazel test`.",
        ),
        "exporter_args": attr.string_list(
            doc = "Traitlets-style flags forwarded to nbconvert exporters (e.g. ``--WebPDFExporter.exclude_input=true``).",
        ),
        "notebook": attr.label(
            doc = "The notebook to execute and test. Must be a jupyter_notebook target.",
            providers = [JupyterNotebookInfo, PyInfo],
            mandatory = True,
        ),
        "reports": attr.string_list(
            doc = "List of report types to generate after successful notebook execution. " + _REPORTS_DOC,
            default = ["webpdf"],
        ),
        "_tester": attr.label(
            cfg = "target",
            default = Label("//tools/process_wrappers:tester"),
        ),
        "_tester_main": attr.label(
            cfg = "target",
            allow_single_file = True,
            default = Label("//tools/process_wrappers:tester.py"),
        ),
    },
    test = True,
    toolchains = [
        TOOLCHAIN_TYPE,
        py_venv_common.TOOLCHAIN_TYPE,
    ],
)

def _jupyter_notebook_binary_impl(ctx):
    toolchain = ctx.toolchains[TOOLCHAIN_TYPE]
    notebook_info = ctx.attr.notebook[JupyterNotebookInfo]

    common = _notebook_args(ctx, toolchain, notebook_info, ctx.attr.reports, ctx.workspace_name)
    common.args.add_all(ctx.attr.reports, format_each = "--report=%s")
    if ctx.attr.out_dir:
        common.args.add("--out-dir", ctx.attr.out_dir)

    # Bazel appends `args` to the command line of `bazel run`. Marking where
    # the notebook args begin removes the ability to pass args to the runner;
    # for example, `args = ["--foo"]` would block the command line form of:
    # ```
    # bazel run //:jupyter_notebook_binary -- --out_dir=/tmp/notebook -- --foo
    # ```
    # so the marker is only written when the rule has args of its own.
    if ctx.attr.args:
        common.args.add("--")

    return _runner_providers(
        ctx,
        common,
        runner = ctx.attr._runner,
        runner_main = ctx.file._runner_main,
        args_file_var = "RULES_JUPYTER_ARGS_FILE",
        env = {"RULES_JUPYTER_BINARY_NAME": ctx.label.name},
    )

jupyter_notebook_binary = rule(
    doc = """\
An executable rule that runs a Jupyter notebook and optionally generates reports.

Unlike `jupyter_notebook_test`, this rule creates an executable target for use with `bazel run`.
Outputs (executed notebook and reports) are written to a configurable output directory, defaulting
to the caller's working directory (`BUILD_WORKING_DIRECTORY`).

Example:

```python
jupyter_notebook(
    name = "my_notebook",
    src = "notebook.py",
    deps = ["@pip_deps//polars"],
)

jupyter_notebook_binary(
    name = "run_notebook",
    notebook = ":my_notebook",
    reports = ["html"],
)
```

Then run: `bazel run :run_notebook` or `bazel run :run_notebook -- --my-flag value`
""",
    implementation = _jupyter_notebook_binary_impl,
    attrs = {
        "cwd_mode": attr.string(
            doc = "The working directory mode for notebook execution. If not specified, uses the toolchain's `default_cwd`. `execution_root` sets the working directory to the workspace root, while `notebook_root` sets it to the notebook's parent directory. This affects how relative paths in the notebook are resolved.",
            values = _CWD_MODE_VALUES,
        ),
        "data": attr.label_list(
            doc = "Additional data files required by the notebook (e.g., input data files, images, configuration files).",
            allow_files = True,
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when executing the notebook. Values support location expansion (e.g., `$(location :target)`).",
        ),
        "env_inherit": attr.string_list(
            doc = "Specifies additional environment variables to inherit from the external environment.",
        ),
        "exporter_args": attr.string_list(
            doc = "Traitlets-style flags forwarded to nbconvert exporters (e.g. ``--WebPDFExporter.exclude_input=true``).",
        ),
        "notebook": attr.label(
            doc = "The notebook to execute. Must be a `jupyter_notebook` target.",
            providers = [JupyterNotebookInfo, PyInfo],
            mandatory = True,
        ),
        "out_dir": attr.string(
            doc = "Directory to write output files to. If not specified, outputs are written to a subdirectory named after the target under the caller's working directory (e.g., `bazel run :run_notebook` writes to `./run_notebook/`). Absolute paths (e.g., `/tmp`) are used as-is; relative paths are resolved against the caller's working directory.",
        ),
        "reports": attr.string_list(
            doc = "List of report types to generate after successful notebook execution. " + _REPORTS_DOC,
            default = [],
        ),
        "_runner": attr.label(
            cfg = "target",
            default = Label("//tools/process_wrappers:runner"),
        ),
        "_runner_main": attr.label(
            cfg = "target",
            allow_single_file = True,
            default = Label("//tools/process_wrappers:runner.py"),
        ),
    },
    executable = True,
    toolchains = [
        TOOLCHAIN_TYPE,
        py_venv_common.TOOLCHAIN_TYPE,
    ],
)

def _jupyter_lab_impl(ctx):
    toolchain = ctx.toolchains[TOOLCHAIN_TYPE]
    notebook_info = ctx.attr.notebook[JupyterNotebookInfo]

    common = _notebook_args(ctx, toolchain, notebook_info, [], ctx.workspace_name)
    args = common.args

    notebook_rloc = _rlocationpath(notebook_info.notebook, ctx.workspace_name)

    if not ctx.attr.execute:
        args.add("--no-execute")
    args.add("--overrides", _rlocationpath(ctx.files.app_settings[0], ctx.workspace_name))
    args.add("--run_mode", ctx.attr.run_mode)
    args.add("--notebook_rlocationpath", notebook_rloc)
    args.add("--notebook_src_short_path", notebook_info.src.short_path)

    all_data_files = depset(ctx.files.data, transitive = [notebook_info.data]).to_list()
    for f in all_data_files:
        args.add("--data_file", "{}={}".format(_rlocationpath(f, ctx.workspace_name), f.short_path))

    if ctx.attr.run_mode == "source":
        if not notebook_info.src.is_source:
            fail("`run_mode='source'` requires a `.ipynb` source, but `{}` provides a generated source.".format(
                ctx.attr.notebook.label,
            ))
        if not notebook_info.src.basename.endswith(".ipynb"):
            fail("`run_mode='source'` requires a `.ipynb` source, but `{}` has `src='{}'`".format(
                ctx.attr.notebook.label,
                notebook_info.src.basename,
            ))
        args.add("--source_notebook", notebook_info.src.short_path)

    # As with `jupyter_notebook_binary`, Bazel appends `args` to the command line.
    if ctx.attr.args:
        args.add("--")

    return _runner_providers(
        ctx,
        common,
        runner = ctx.attr._launcher,
        runner_main = ctx.file._launcher_main,
        args_file_var = "RULES_JUPYTER_LAB_ARGS_FILE",
        extra_files = ctx.files.app_settings,
    )

jupyter_lab = rule(
    doc = """\
Launches a Jupyter Lab server for interactive notebook development.

This rule creates an executable target that, when run via `bazel run`, starts a Jupyter Lab
server with the notebook's dependencies available in the virtualenv. By default, when a user
opens the printed URL in their browser, all notebook cells are automatically executed — exactly
as if the user clicked "Run All Cells" in Lab's Run menu.

Example:

```python
jupyter_notebook(
    name = "my_notebook",
    src = "notebook.py",
    deps = ["@pip_deps//polars"],
)

jupyter_lab(
    name = "my_lab",
    notebook = ":my_notebook",
)
```

Then run: `bazel run :my_lab`
""",
    implementation = _jupyter_lab_impl,
    attrs = {
        "app_settings": attr.label(
            doc = "A JupyterLab `overrides.json` file providing default settings. Keys are `@jupyterlab/<extension>:<plugin>` and values are settings objects.",
            default = Label("//jupyter:lab_app_settings"),
            allow_single_file = [".json"],
        ),
        "cwd_mode": attr.string(
            doc = "The working directory mode for notebook execution. If not specified, uses the toolchain's `default_cwd`. `execution_root` sets the working directory to Bazel's execution root, while `notebook_root` sets it to the notebook's parent directory.",
            values = _CWD_MODE_VALUES,
        ),
        "data": attr.label_list(
            doc = "Additional data files required by the notebook (e.g., input data files, images, configuration files).",
            allow_files = True,
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when launching the server. Values support location expansion (e.g., `$(location :target)`).",
        ),
        "env_inherit": attr.string_list(
            doc = "Specifies additional environment variables to inherit from the external environment.",
        ),
        "execute": attr.bool(
            doc = "Whether to automatically execute all notebook cells when the user opens the notebook in their browser. When True, Lab triggers 'Run All Cells' as soon as the notebook loads. Can be overridden at runtime with `-- --no-execute`.",
            default = True,
        ),
        "notebook": attr.label(
            doc = "The notebook to serve. Must be a `jupyter_notebook` target.",
            providers = [JupyterNotebookInfo, PyInfo],
            mandatory = True,
        ),
        "run_mode": attr.string(
            doc = "Controls where the notebook is served from. `runfiles` (default) copies the notebook to a temp directory with symlinked data dependencies. `source` serves the notebook directly from the source tree for in-place editing with unrestricted file access; requires a `.ipynb` source.",
            values = [
                "runfiles",
                "source",
            ],
            default = "runfiles",
        ),
        "_launcher": attr.label(
            cfg = "target",
            default = Label("//tools/process_wrappers:lab_launcher"),
        ),
        "_launcher_main": attr.label(
            cfg = "target",
            allow_single_file = True,
            default = Label("//tools/process_wrappers:lab_launcher.py"),
        ),
    },
    executable = True,
    toolchains = [
        TOOLCHAIN_TYPE,
        py_venv_common.TOOLCHAIN_TYPE,
    ],
)
