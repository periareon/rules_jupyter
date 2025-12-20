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
    playwright_browsers_dir = "@rules_jupyter//jupyter/playwright:current_browsers_dir",
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
