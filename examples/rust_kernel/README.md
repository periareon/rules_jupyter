# Rust Kernel Example: Using evcxr with rules_jupyter

This example demonstrates how to use the evcxr Rust kernel with `rules_jupyter` to execute Rust code in Jupyter notebooks and generate reports.

## Prerequisites

You must have the Rust toolchain installed (via [rustup](https://rustup.rs/)).

The `rust-src` component is required by evcxr for interactive compilation:

```bash
rustup component add rust-src
```

The evcxr binary is fetched automatically by Bazel via the module extension in `extensions.bzl` — no manual `cargo install` is needed.

## Files

- `notebook.ipynb` - A Jupyter notebook with Rust code cells
- `BUILD.bazel` - Bazel build file showing `jupyter_kernel`, `jupyter_notebook`, and `jupyter_report` with the Rust kernel
- `extensions.bzl` - Module extension that fetches the prebuilt evcxr_jupyter binary per platform
- `MODULE.bazel` - Module configuration

## Usage

Build from within the `examples/rust_kernel` directory:

```bash
cd examples/rust_kernel
bazel build :report_markdown
```

The generated markdown report will be at:
```
bazel-bin/report.md
```

## How It Works

1. **`jupyter_kernel` rule**: Declares the evcxr Rust kernel with its binary, argv pattern, and metadata. This generates a `kernel.json` template at build time.

2. **`jupyter_toolchain`**: Registers the Rust kernel via the `kernels` attribute so it is available to all report and test rules.

3. **Runtime kernel discovery**: When a report or test executes, the runner creates a temporary kernelspec directory, substitutes the real binary path into the `kernel.json` template, and prepends the directory to `JUPYTER_PATH`. This lets Jupyter's `ExecutePreprocessor` discover and launch the kernel.

4. **`jupyter_notebook`**: Sets `kernel = "rust"` to tell Jupyter to use the Rust kernelspec.

5. **`jupyter_report`**: Executes the notebook with the Rust kernel and converts the output to Markdown and/or WebPDF.

## Kernel Configuration

The `jupyter_kernel` rule in `BUILD.bazel` defines the evcxr kernel:

```python
jupyter_kernel(
    name = "rust_kernel",
    kernel_name = "rust",
    display_name = "Rust",
    language = "rust",
    binary = "@evcxr_jupyter",
    args = ["--control_file", "{connection_file}"],
    interrupt_mode = "message",
)
```

The `binary` attribute points to the evcxr_jupyter binary fetched by the module extension. The `args` list specifies the arguments passed after the binary in the kernel.json `argv` field — `{connection_file}` is a Jupyter protocol placeholder that gets replaced with the actual connection file at runtime.
