"""Rule to collect shared libraries from debian archive dependencies into a single directory."""

def _playwright_ld_library_dir_impl(ctx):
    output_dir = ctx.actions.declare_directory(ctx.label.name)

    all_inputs = []
    for dep in ctx.attr.deps:
        all_inputs.append(dep[DefaultInfo].files)

    inputs = depset(transitive = all_inputs)

    args = ctx.actions.args()
    args.add("--output-dir", output_dir.path)
    for f in inputs.to_list():
        args.add("--dep-file", f)

    ctx.actions.run(
        mnemonic = "PlaywrightLdLibraryDir",
        executable = ctx.executable._generator,
        arguments = [args],
        inputs = inputs,
        outputs = [output_dir],
    )

    return [DefaultInfo(
        files = depset([output_dir]),
    )]

playwright_ld_library_dir = rule(
    doc = "Collects .so files from debian archive dependencies into a single flat directory suitable for LD_LIBRARY_PATH.",
    implementation = _playwright_ld_library_dir_impl,
    attrs = {
        "deps": attr.label_list(
            doc = "Debian archive filegroup targets containing shared libraries.",
            mandatory = True,
        ),
        "_generator": attr.label(
            cfg = "exec",
            executable = True,
            default = Label("//playwright/ld_library_path/private:generator"),
        ),
    },
)
