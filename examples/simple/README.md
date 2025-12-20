# Simple Example: Python Notebook to Markdown Report

This example demonstrates how to use a `.py` notebook file (using Jupytext format) with `rules_jupyter` to generate a markdown report.

## Files

- `notebook.py` - A Python notebook file using Jupytext format with `# %%` cell markers
- `BUILD.bazel` - Bazel build file showing how to use `jupyter_notebook` and `jupyter_report` rules
- `MODULE.bazel` - Module configuration (note: this example is designed to work from the repository root)

## Usage

**Note:** Due to Bazel module extension limitations with `local_path_override`, this example should be built from the repository root, not from within this directory:

```bash
# From the repository root
bazel build //examples/simple:report_markdown
```

The generated markdown report will be at:
```
bazel-bin/examples/simple/report.md
```

## What This Example Shows

1. **Using `.py` files as notebooks**: The `notebook.py` file uses Jupytext format with `# %%` cell markers to define code cells and `# %% [markdown]` for markdown cells.

2. **Converting to `.ipynb`**: The `jupyter_notebook` rule automatically converts the `.py` file to `.ipynb` format using Jupytext.

3. **Generating markdown reports**: The `jupyter_report` rule executes the notebook and generates a markdown report with both code and output.

## Building from the Example Directory

If you want to use this as a standalone example in your own project:

1. Copy the files to your project
2. Update `MODULE.bazel` to use `bazel_dep(name = "rules_jupyter", version = "...")` instead of `local_path_override`
3. Ensure all required extensions (jupyter, playwright, requirements) are configured
4. Build from your project root

