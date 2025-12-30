# Rust Kernel Example: Using evcxr with rules_jupyter

This example demonstrates how to use the evcxr Rust kernel with `rules_jupyter` to execute Rust code in Jupyter notebooks and generate reports.

## Prerequisites

The evcxr_jupyter kernel must be installed and registered with Jupyter. You can install it using:

```bash
cargo install --locked evcxr_jupyter
evcxr_jupyter --install
```

This registers the Rust kernel with Jupyter, making it available as the "rust" kernel.

## Files

- `notebook.ipynb` - A Jupyter notebook with Rust code cells
- `BUILD.bazel` - Bazel build file showing how to use `jupyter_notebook` and `jupyter_report` with the Rust kernel
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

## What This Example Shows

1. **Using Rust in Jupyter**: The notebook uses the evcxr Rust kernel to execute Rust code cells.

2. **Rust code execution**: The notebook demonstrates:
   - Basic Rust operations and variables
   - Working with vectors and iterators
   - Defining and calling functions
   - String formatting and output

3. **Generating reports**: The `jupyter_report` rule executes the notebook with the Rust kernel and generates markdown and PDF reports.

## Kernel Configuration

The notebook is configured to use the "rust" kernel by specifying `kernel = "rust"` in the `jupyter_notebook` rule. This tells Jupyter to use the evcxr kernel for executing the cells.

## Note on evcxr_jupyter Binary

The current BUILD.bazel includes a placeholder for building evcxr_jupyter. In a production setup, you would:

1. Add evcxr_jupyter as a Rust dependency using rules_rust
2. Build it as a binary target
3. Ensure it's available in the Jupyter kernel path

For this example, we assume evcxr_jupyter is installed system-wide via `cargo install`.
