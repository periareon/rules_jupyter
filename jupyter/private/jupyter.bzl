"""# Jupyter rules"""

load("@rules_venv//python:py_info.bzl", "PyInfo")
load("@rules_venv//python/venv:defs.bzl", "py_venv_common")
load(":providers.bzl", "JupyterNotebookInfo")
load(":rules_venv_aspects.bzl", "aspects_provider")
load(":toolchain.bzl", "TOOLCHAIN_TYPE")

def _jupyter_notebook_impl(ctx):
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

        out_notebook = ctx.actions.declare_file("{}.ipynb".format(name.strip("/")[:-len(".py")]))
        args.add("--out_notebook", out_notebook)

        if ctx.attr.kernel:
            args.add("--kernel", ctx.attr.kernel)

        ctx.actions.run(
            mnemonic = "JupyterCompile",
            executable = ctx.executable._compiler,
            arguments = [args],
            outputs = [out_notebook],
            inputs = [notebook],
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
            data = depset(ctx.files.data),
        ),
        aspects_provider(ctx, ctx.file.src),
        py_info,
    ]

jupyter_notebook = rule(
    doc = """\
Compiles a Jupyter notebook from source and prepares it for execution.

This rule processes notebook source files and converts them to the standard `.ipynb` format.
If the source is a .py file in Jupytext format (with `# %%` cell markers), it will be converted
to `.ipynb` format. If the source is already a `.ipynb` file, it is used directly.

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
            doc = "The name of the Jupyter kernel to use for executing the notebook (e.g., `python3`, `rust`). If not specified, the default kernel from the toolchain is used.",
        ),
        "src": attr.label(
            doc = "The notebook source file. Can be either a .ipynb file or a `.py` file in [Jupytext](https://jupytext.readthedocs.io/en/latest/) format (with `# %%` cell markers).",
            allow_single_file = [".py", ".ipynb"],
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

    kernel = notebook_info.kernel
    if not kernel:
        kernel = toolchain.default_kernel

    cwd_mode = ctx.attr.cwd_mode
    if not cwd_mode:
        cwd_mode = toolchain.default_cwd_mode

    out_notebook = ctx.outputs.out_notebook
    if not out_notebook:
        out_notebook = ctx.actions.declare_file("{}.ipynb".format(ctx.label.name))

    outputs = {"jupiter_report_notebook": out_notebook}

    args = ctx.actions.args()
    args.add("--notebook", notebook_info.notebook)
    args.add("--cwd_mode", cwd_mode)
    if kernel:
        args.add("--kernel", kernel)
    args.add("--out_notebook", out_notebook)

    if toolchain.pandoc:
        args.add("--pandoc", toolchain.pandoc)
    if toolchain.playwright_browsers_dir:
        args.add("--playwright_browsers_dir", toolchain.playwright_browsers_dir.path)

    if ctx.outputs.out_html:
        out_html = ctx.outputs.out_html
        outputs.update({"jupiter_report_html": out_html})
        args.add("--out_html", out_html)
        if ctx.attr.out_html_template_type:
            args.add("--out_html_template_type", ctx.attr.out_html_template_type)

    if ctx.outputs.out_latex:
        out_latex = ctx.outputs.out_latex
        outputs.update({"jupiter_report_latex": out_latex})
        args.add("--out_latex", out_latex)
        if ctx.attr.out_latex_template_type:
            args.add("--out_latex_template_type", ctx.attr.out_latex_template_type)

    if ctx.outputs.out_markdown:
        if not toolchain.pandoc:
            fail("`jupyter_toolchain.pandoc` is not set on the current toolchain yet markdown outputs were requested. Please update `{}`".format(
                toolchain.label,
            ))
        out_markdown = ctx.outputs.out_markdown
        outputs.update({"jupiter_report_markdown": out_markdown})
        args.add("--out_markdown", out_markdown)

    # TODO: Requires a latex toolchain
    # if ctx.outputs.out_pdf:
    #     out_pdf = ctx.outputs.out_pdf
    #     outputs.update({"jupiter_report_pdf": out_pdf})
    #     args.add("--out_pdf", out_pdf)

    if ctx.outputs.out_rst:
        out_rst = ctx.outputs.out_rst
        outputs.update({"jupiter_report_rst": out_rst})
        args.add("--out_rst", out_rst)

    if ctx.outputs.out_webpdf:
        if not toolchain.playwright_browsers_dir:
            fail("`jupyter_toolchain.playwright_browsers_dir` is not set on the current toolchain yet webpdf outputs were requested. Please update `{}`".format(
                toolchain.label,
            ))
        out_webpdf = ctx.outputs.out_webpdf
        outputs.update({"jupiter_report_webpdf": out_webpdf})
        args.add("--out_webpdf", out_webpdf)

    args.add("--")

    known_variables = {}
    for target in ctx.attr.toolchains:
        if platform_common.TemplateVariableInfo in target:
            variables = getattr(target[platform_common.TemplateVariableInfo], "variables", {})
            known_variables.update(variables)

    notebook_args = _expand_args(ctx, ctx.attr.args, ctx.attr.data, known_variables)

    args.add_all(notebook_args)

    env = _expand_env(ctx, ctx.attr.env, ctx.attr.data, known_variables)

    reporter, runfiles = _create_executable(
        ctx = ctx,
        cfg = "exec",
        runner = ctx.attr._reporter,
        runner_main = ctx.file._reporter_main,
        notebook = ctx.attr.notebook,
    )

    ctx.actions.run(
        mnemonic = "JupyterReport",
        progress_message = "JupyterReport %{label}",
        executable = reporter,
        arguments = [args],
        inputs = depset([notebook_info.notebook] + ctx.files.data, transitive = [notebook_info.data, toolchain.all_files]),
        outputs = outputs.values(),
        tools = depset(transitive = [runfiles.files, toolchain.all_files]),
        env = env | ctx.configuration.default_shell_env,
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
            values = [
                "execution_root",
                "notebook_root",
            ],
        ),
        "data": attr.label_list(
            doc = "Additional data files required by the notebook (e.g., input data files, images, configuration files).",
            allow_files = True,
        ),
        "env": attr.string_dict(
            doc = "Environment variables to set when executing the notebook. Values support location expansion (e.g., `$(location :target)`).",
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
            doc = "Template type for LaTeX output.",
            values = [
                "article",
                "report",
                "basic",
            ],
        ),
        "out_markdown": attr.output(
            doc = "Output path for a Markdown report. If specified, the notebook will be converted to Markdown format.",
        ),
        "out_notebook": attr.output(
            doc = "Output path for the executed notebook (`.ipynb` file with cell outputs). If not specified, a default name is generated.",
        ),
        # TODO: Requires a latex toolchain
        # "out_pdf": attr.output(
        #     doc = "Output path for a PDF report (generated via LaTeX). If specified, the notebook will be converted to PDF format using LaTeX.",
        # ),
        "out_rst": attr.output(
            doc = "Output path for a reStructuredText report. If specified, the notebook will be converted to RST format.",
        ),
        "out_webpdf": attr.output(
            doc = "Output path for a WebPDF report (generated via Playwright/Chromium). If specified, the notebook will be converted to PDF format using headless browser rendering.",
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

def _rlocationpath(file, workspace_name):
    if file.short_path.startswith("../"):
        return file.short_path[len("../"):]

    return "{}/{}".format(workspace_name, file.short_path)

_REPORT_VALUES = [
    "html",
    "markdown",
    "latex",
    "html",
    "webpdf",
    # TODO: Requires a latex toolchain
    # "pdf",
]

def _jupyter_notebook_test_impl(ctx):
    toolchain = ctx.toolchains[TOOLCHAIN_TYPE]
    notebook_info = ctx.attr.notebook[JupyterNotebookInfo]

    kernel = notebook_info.kernel
    if not kernel:
        kernel = toolchain.default_kernel

    cwd_mode = ctx.attr.cwd_mode
    if not cwd_mode:
        cwd_mode = toolchain.default_cwd_mode

    args = ctx.actions.args()
    args.set_param_file_format("multiline")
    args.add("--pandoc", _rlocationpath(toolchain.pandoc, ctx.workspace_name))
    if toolchain.playwright_browsers_dir:
        args.add("--playwright_browsers_dir", _rlocationpath(toolchain.playwright_browsers_dir, ctx.workspace_name))
    args.add("--notebook", _rlocationpath(notebook_info.notebook, ctx.workspace_name))
    args.add("--cwd_mode", cwd_mode)
    if kernel:
        args.add("--kernel", kernel)

    for report in ctx.attr.reports:
        if report not in _REPORT_VALUES:
            fail("Invalid `jupyter_notebook_test.report` value `{}`. Please update `{}` to use one of the available types: {}".format(
                report,
                ctx.label,
                _REPORT_VALUES,
            ))
        if report == "markdown" and not toolchain.pandoc:
            fail("`jupyter_toolchain.pandoc` is not set on the current toolchain yet markdown reports were requested. Please update `{}`".format(
                toolchain.label,
            ))
        if report == "webpdf" and not toolchain.playwright_browsers_dir:
            fail("`jupyter_toolchain.playwright_browsers_dir` is not set on the current toolchain yet markdown reports were requested. Please update `{}`".format(
                toolchain.label,
            ))
        args.add("--report", report)
    args.add("--")

    known_variables = {}
    for target in ctx.attr.toolchains:
        if platform_common.TemplateVariableInfo in target:
            variables = getattr(target[platform_common.TemplateVariableInfo], "variables", {})
            known_variables.update(variables)

    notebook_args = _expand_args(ctx, ctx.attr.args, ctx.attr.data, known_variables)
    args.add_all(notebook_args)

    args_file = ctx.actions.declare_file("{}.args.txt".format(ctx.label.name))
    ctx.actions.write(
        output = args_file,
        content = args,
    )

    # TODO: Make runner with notebook deps
    executable, runfiles = _create_executable(
        ctx = ctx,
        cfg = "target",
        runner = ctx.attr._tester,
        runner_main = ctx.file._tester_main,
        notebook = ctx.attr.notebook,
    )

    runfiles = runfiles.merge(ctx.runfiles(
        [executable, args_file, notebook_info.notebook] + ctx.files.data,
        transitive_files = depset(transitive = [notebook_info.data, toolchain.all_files]),
    ))

    return [
        DefaultInfo(
            executable = executable,
            runfiles = runfiles,
        ),
        _create_run_environment_info(
            ctx = ctx,
            env = ctx.attr.env | {
                "RULES_JUPYTER_TEST_ARGS_FILE": _rlocationpath(args_file, ctx.workspace_name),
            },
            env_inherit = ctx.attr.env_inherit,
            targets = ctx.attr.data,
            known_variables = known_variables,
        ),
    ]

jupyter_notebook_test = rule(
    doc = "A test rule that executes a Jupyter notebook and optionally generates reports. The test fails if any notebook cell raises an error.",
    implementation = _jupyter_notebook_test_impl,
    attrs = {
        "cwd_mode": attr.string(
            doc = "The working directory mode for notebook execution. If not specified, uses the toolchain's `default_cwd`. `workspace_root` sets the working directory to the workspace root, while `notebook_root` sets it to the notebook's parent directory. This affects how relative paths in the notebook are resolved.",
            values = [
                "workspace_root",
                "notebook_root",
            ],
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
        "notebook": attr.label(
            doc = "The notebook to execute and test. Must be a jupyter_notebook target.",
            providers = [JupyterNotebookInfo, PyInfo],
            mandatory = True,
        ),
        "reports": attr.string_list(
            doc = "List of report types to generate after successful notebook execution. Valid values: 'html', 'markdown', 'latex'.",
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
