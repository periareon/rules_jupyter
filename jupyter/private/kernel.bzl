"""Jupyter kernel rule for alternate kernel support."""

load(":providers.bzl", "JupyterKernelInfo")

_KERNEL_JSON_TEMPLATE = """\
{{
  "argv": {argv},
  "display_name": "{display_name}",
  "language": "{language}"{interrupt_mode}{env}
}}
"""

def _jupyter_kernel_impl(ctx):
    kernel_json = ctx.actions.declare_file("{}_kernel.json".format(ctx.label.name))

    argv_items = ["__KERNEL_BINARY__"] + list(ctx.attr.args)
    argv_json = json.encode(argv_items)

    display_name = ctx.attr.display_name if ctx.attr.display_name else ctx.attr.kernel_name.capitalize()
    language = ctx.attr.language if ctx.attr.language else ctx.attr.kernel_name

    interrupt_mode = ""
    if ctx.attr.interrupt_mode:
        interrupt_mode = ',\n  "interrupt_mode": "{}"'.format(ctx.attr.interrupt_mode)

    env = ""
    if ctx.attr.env:
        env = ',\n  "env": {}'.format(json.encode(ctx.attr.env))

    ctx.actions.write(
        output = kernel_json,
        content = _KERNEL_JSON_TEMPLATE.format(
            argv = argv_json,
            display_name = display_name,
            language = language,
            interrupt_mode = interrupt_mode,
            env = env,
        ),
    )

    # Include the binary label's runtime data (e.g. Julia's stdlib, shared libs)
    # so that kernels with non-trivial installation trees work in the sandbox.
    binary_runfiles_files = []
    if DefaultInfo in ctx.attr.binary:
        default_runfiles = ctx.attr.binary[DefaultInfo].default_runfiles
        if default_runfiles:
            binary_runfiles_files.append(default_runfiles.files)

    data = depset(ctx.files.data, transitive = binary_runfiles_files)

    return [
        JupyterKernelInfo(
            kernel_name = ctx.attr.kernel_name,
            kernel_json = kernel_json,
            binary = ctx.file.binary,
            data = data,
        ),
        DefaultInfo(
            files = depset([kernel_json, ctx.file.binary]),
            default_runfiles = ctx.runfiles(transitive_files = data),
        ),
    ]

jupyter_kernel = rule(
    doc = """\
Declares a Jupyter kernel for use in sandboxed notebook execution.

This rule packages a kernel binary with its configuration into a `JupyterKernelInfo`
provider. At build time it generates a `kernel.json` template; at execution time the
reporter/tester substitutes the real binary path so Jupyter can discover the kernel.

Example:

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
""",
    implementation = _jupyter_kernel_impl,
    attrs = {
        "args": attr.string_list(
            doc = "Arguments appended after the kernel binary in the kernel.json `argv` field. Must include the `{connection_file}` placeholder somewhere for Jupyter to pass the connection file path.",
            default = ["{connection_file}"],
        ),
        "binary": attr.label(
            doc = "The kernel binary executable (e.g., `@evcxr_jupyter`).",
            mandatory = True,
            allow_single_file = True,
        ),
        "data": attr.label_list(
            doc = "Additional data files required by the kernel at runtime.",
            allow_files = True,
        ),
        "display_name": attr.string(
            doc = "Human-readable display name for the kernel (e.g., 'Rust'). Defaults to the capitalized `kernel_name`.",
        ),
        "env": attr.string_dict(
            doc = "Environment variables to include in the kernel.json `env` field.",
        ),
        "interrupt_mode": attr.string(
            doc = "Interrupt mode for the kernel. Use `message` for kernels that handle interrupt via Jupyter messages (like evcxr), or `signal` for POSIX signal-based interrupts.",
            values = [
                "message",
                "signal",
            ],
        ),
        "kernel_name": attr.string(
            doc = "The kernelspec name used for Jupyter kernel discovery (e.g., 'rust'). This must match the `kernel` attribute on `jupyter_notebook` targets that use this kernel.",
            mandatory = True,
        ),
        "language": attr.string(
            doc = "The language identifier for the kernel (e.g., 'rust'). Defaults to `kernel_name`.",
        ),
    },
    provides = [JupyterKernelInfo],
)
