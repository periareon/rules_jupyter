"""Repository rule that creates a target collecting shared libraries for LD_LIBRARY_PATH.

Generates a BUILD file that instantiates `playwright_ld_library_dir` with
the given debian archive dependencies, producing a directory of .so files.
"""

_BUILD_TEMPLATE = """\
load("@rules_jupyter//playwright/ld_library_dir:ld_library_dir.bzl", "playwright_ld_library_dir")

playwright_ld_library_dir(
    name = "{name}",
    deps = {deps},
    visibility = ["//visibility:public"],
)
"""

def _playwright_ld_library_dir_repo_impl(repository_ctx):
    repository_ctx.file("BUILD.bazel", _BUILD_TEMPLATE.format(
        name = repository_ctx.original_name,
        deps = json.encode(repository_ctx.attr.deps),
    ))
    repository_ctx.file("WORKSPACE.bazel", """workspace(name = "{}")""".format(
        repository_ctx.original_name,
    ))

playwright_ld_library_dir_repo = repository_rule(
    doc = "Creates a repository with a playwright_ld_library_dir target that collects .so files from debian archive deps.",
    implementation = _playwright_ld_library_dir_repo_impl,
    attrs = {
        "deps": attr.string_list(
            doc = "Label strings of debian_archive filegroup targets to collect shared libraries from.",
            mandatory = True,
        ),
    },
)
