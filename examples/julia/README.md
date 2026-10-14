# Julia Example

This example runs a Jupyter notebook written in Julia with `rules_jupyter`. The
kernel is [IJulia](https://github.com/JuliaLang/IJulia.jl), built by
[rules_julia](https://github.com/periareon/rules_julia) as an ordinary
`julia_binary` and described with `jupyter_kernelspec`.

Nothing is read from the host: Julia, its packages and the kernel are all
fetched and built by Bazel.

## Files

- `BUILD.bazel` - The `jupyter_toolchain` listing the kernel, and the notebook targets.
- `kernel/` - The kernel: a `julia_binary` running `IJulia.run_kernel()` and its `jupyter_kernelspec`.
  The binary is launched with `--color=yes`, as IJulia's own kernelspec does.
  `Project.toml`/`Manifest.toml` pin `IJulia`; regenerate with `bazel run //kernel:pkg_update`.
  `conda_deps.patch` and `ijulia_deps.patch` define the constants the `Pkg.build` steps of
  `Conda` and `IJulia` would generate, since rules_julia does not run build scripts; they are
  applied through `pkg_annotation` in `MODULE.bazel`.
- `notebook.jl` - The notebook in [Jupytext](https://jupytext.readthedocs.io/en/latest/) percent format.

## Usage

```bash
# From examples/julia
bazel test //...

# Execute the notebook and write reports next to the current directory
bazel run //:run

# Open the notebook in Jupyter Lab with its kernel available
bazel run //:lab
```

## How the kernel is defined

```python
jupyter_kernelspec(
    name = "julia",
    display_name = "Julia",
    language = "julia",
    argv = [
        "$(rlocationpath :ijulia_kernel)",
        "{connection_file}",
    ],
    data = [":ijulia_kernel"],
    # A file holding the cell that forwards notebook `args`; `{args}` is a JSON array.
    args_template = "args_template.jl",
)
```

`argv` and `env` describe the kernel launch command the way a `kernel.json` does.
File references use `$(rlocationpath ...)` and are resolved wherever the notebook
runs: build actions (`jupyter_report`), tests, `bazel run` and Jupyter Lab.

Notebooks select a kernel by name:

```python
jupyter_notebook(
    name = "notebook",
    src = "notebook.jl",
    kernel = "julia",
)
```

Only the files of the selected kernel are added to the notebook's actions and
tests, so Python notebooks in the same workspace do not depend on Julia.

## Platform support

Linux (x86_64, aarch64), macOS and Windows.
