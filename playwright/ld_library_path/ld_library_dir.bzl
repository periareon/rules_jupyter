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

_BUILD_TEMPLATE = """\
load("@rules_jupyter//playwright/ld_library_path:ld_library_dir.bzl", "playwright_ld_library_dir")

playwright_ld_library_dir(
    name = "{name}",
    deps = {deps},
    visibility = ["//visibility:public"],
)
"""

def _playwright_ld_library_dir_repository_impl(repository_ctx):
    repository_ctx.file("BUILD.bazel", _BUILD_TEMPLATE.format(
        name = repository_ctx.original_name,
        deps = json.encode(repository_ctx.attr.deps),
    ))
    repository_ctx.file("WORKSPACE.bazel", """workspace(name = "{}")""".format(
        repository_ctx.original_name,
    ))

playwright_ld_library_dir_repository = repository_rule(
    doc = "Creates a repository with a playwright_ld_library_dir target that collects .so files from debian archive deps.",
    implementation = _playwright_ld_library_dir_repository_impl,
    attrs = {
        "deps": attr.string_list(
            doc = "Label strings of debian_archive filegroup targets to collect shared libraries from.",
            mandatory = True,
        ),
    },
)
