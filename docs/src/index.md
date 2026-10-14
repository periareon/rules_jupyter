# rules_jupyter

Bazel rules for running [Jupyter notebooks](https://jupyter.org/) and generating reports.

## Setup

To use the rules, add the following to your `MODULE.bazelrc`.

```python
bazel_dep(name = "rules_jupyter", version = "{version}")
```

### Toolchains

These rules rely heavily on a [`jupyter_toolchain`](./rules.md#jupyter_toolchain) which will need to be setup.

In your `MODULE.bazel`, configure the convenience extensions. If [Pandoc](https://pandoc.org/) and [Playwright browsers](https://playwright.dev/)
are available by some other means this can be skipped:

```python
# Configure Pandoc (required for markdown reports)
jupyter = use_extension("@rules_jupyter//jupyter:extensions.bzl", "jupyter")
jupyter.pandoc(name = "pandoc")
use_repo(jupyter, "pandoc")

# Configure Playwright (required for WebPDF reports)
playwright = use_extension("@rules_jupyter//jupyter:extensions.bzl", "playwright")
playwright.toolchain(name = "playwright_toolchains", version = "1.57.0")
use_repo(playwright, "playwright_toolchains")
register_toolchains("@playwright_toolchains//:all")
```

Python dependencies will also be required for the toolchain. Rules such as [rules_req_compile](https://github.com/periareon/req-compile) can be
used for this.

In your `BUILD.bazel`:

```python
load("@rules_jupyter//jupyter:jupyter_toolchain.bzl", "jupyter_toolchain")

jupyter_toolchain(
    name = "jupyter_toolchain",
    jupyter = "@pip_deps//jupyter",
    jupytext = "@pip_deps//jupytext",
    # Produced by rules_jupyter module extension.
    pandoc = "@pandoc",
    # Produced by rules_jupyter module extension.
    playwright_browsers_dir = "@rules_jupyter//playwright:current_browsers_dir",
)

toolchain(
    name = "jupyter_toolchain",
    toolchain = ":jupyter_toolchain",
    toolchain_type = "@rules_jupyter//jupyter:toolchain_type",
)
```

Register it in `MODULE.bazel`:

```python
register_toolchains(
    "//:jupyter_toolchain",
)
```

### Kernels

Notebooks are executed by the kernel named in `jupyter_notebook.kernel` (or the toolchain's default `kernel`).
Python notebooks use the `python3` kernel from `ipykernel` in the toolchain's Python environment and need no further setup.

Kernels for other languages are declared with [`jupyter_kernelspec`](./jupyter_kernelspec.md) and attached to the
toolchain via `kernels`. The rule is language agnostic: it describes how to launch a kernel executable, like a
`kernel.json` does, with files tracked by Bazel. A single toolchain can serve notebooks of many languages.

```python
load("@rules_jupyter//jupyter:jupyter_kernelspec.bzl", "jupyter_kernelspec")

jupyter_kernelspec(
    name = "julia",
    display_name = "Julia",
    language = "julia",
    argv = [
        "$(rlocationpath :ijulia_kernel)",
        "{connection_file}",
    ],
    data = [":ijulia_kernel"],
    # How notebook `args` reach the kernel. Omit for kernels without arguments.
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

Sources in any language [Jupytext](https://jupytext.readthedocs.io/en/latest/) understands (`.py`, `.jl`, `.rs`, ...)
are converted to notebooks with the kernel's metadata. Only the files of the selected kernel are added to a notebook's
actions and tests. See [`examples/julia`](https://github.com/periareon/rules_jupyter/tree/main/examples/julia) for a
Julia kernel ([IJulia](https://github.com/JuliaLang/IJulia.jl) via [rules_julia](https://github.com/periareon/rules_julia))
and [`examples/rust`](https://github.com/periareon/rules_jupyter/tree/main/examples/rust) for a Rust kernel
([evcxr](https://github.com/evcxr/evcxr) via [rules_rust](https://github.com/bazelbuild/rules_rust)).
