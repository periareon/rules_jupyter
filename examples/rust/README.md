# Rust Example

This example runs a Jupyter notebook written in Rust with `rules_jupyter`. The
kernel is [evcxr](https://github.com/evcxr/evcxr): `evcxr_jupyter` built from
source with `crate_universe`, with `cargo` from
[rules_rust](https://github.com/bazelbuild/rules_rust) on its `PATH`. The
kernel is described with `jupyter_kernelspec`.

Nothing is read from the host: Rust, `cargo` and the kernel are all fetched by
Bazel. The kernel does need a C linker (`cc`) on the host for `cargo`.

## Files

- `BUILD.bazel` - The `jupyter_toolchain` listing the kernel, and the notebook targets.
- `kernel/` - The kernel: the `evcxr_jupyter` binary with the `rules_rust` toolchain's `cargo` on `PATH`.
  `Cargo.lock` and `Cargo.Bazel.lock` pin the crates it is built from; `evcxr_build.patch` lets its
  build script find `rustc` and `cargo` without `PATH`.
- `notebook.rs` - The notebook in [Jupytext](https://jupytext.readthedocs.io/en/latest/) percent format.

## Usage

```bash
# From examples/rust
bazel test //...

# Execute the notebook and write reports next to the current directory
bazel run //:run

# Open the notebook in Jupyter Lab with its kernel available
bazel run //:lab
```

## How the kernel is defined

```python
jupyter_kernelspec(
    name = "rust",
    display_name = "Rust",
    language = "rust",
    argv = [
        "$(rlocationpath :evcxr_jupyter)",
        "--control_file",
        "{connection_file}",
    ],
    data = [
        ":evcxr_jupyter",
        "@rules_rust//rust/toolchain:current_rust_stdlib_files",
    ],
    # Directories prepended to `PATH`; this is how evcxr finds `cargo` and `rustc`.
    path_tools = ["@rules_rust//rust/toolchain:current_cargo_files"],
    # evcxr's ZeroMQ is built with TCP transport only.
    transport = "tcp",
    # A file holding the cell that forwards notebook `args`; `{args}` is a JSON array.
    args_template = "args_template.rs",
)
```

`argv` and `env` describe the kernel launch command the way a `kernel.json` does.
File references use `$(rlocationpath ...)` and are resolved wherever the notebook
runs: build actions (`jupyter_report`), tests, `bazel run` and Jupyter Lab.

Notebooks select a kernel by name:

```python
jupyter_notebook(
    name = "notebook",
    src = "notebook.rs",
    kernel = "rust",
)
```

## Platform support

The kernel is built from source, so it runs wherever `rules_rust` provides a
toolchain and a C linker (`cc`) is available for `cargo`.
