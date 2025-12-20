"""Rules for fetching Pandoc"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load(":pandoc_versions.bzl", _PANDOC_VERSIONS = "PANDOC_VERSIONS")

DEFAULT_PANDOC_VERSION = "3.8.2"
PANDOC_VERSIONS = _PANDOC_VERSIONS

_BUILD_TEMPLATE_UNIX = """\
filegroup(
    name = "{name}",
    srcs = ["bin/pandoc"],
    data = glob(
        include = ["bin/**", "share/**"],
        exclude = ["bin/pandoc"],
    ),
    visibility = ["//visibility:public"],
)
"""

_BUILD_TEMPLATE_WINDOWS = """\
filegroup(
    name = "{name}",
    srcs = ["pandoc.exe"],
    visibility = ["//visibility:public"],
)
"""

_ALIAS_REPO_TEMPLATE = """\
TARGETS = {targets}

alias(
    name = "{name}",
    actual = select(TARGETS),
    visibility = ["//visibility:public"],
)
"""

def _alias_repository_impl(repository_ctx):
    repository_ctx.file("BUILD.bazel", _ALIAS_REPO_TEMPLATE.format(
        name = repository_ctx.original_name,
        targets = json.encode_indent({
            "@rules_jupyter//tools/constraints:{}".format(platform): str(binary)
            for binary, platform in repository_ctx.attr.binaries.items()
        }),
    ))

    repository_ctx.file("WORKSPACE.bazel", """workspace(name = "{}")""".format(
        repository_ctx.name,
    ))

pandoc_alias_repository = repository_rule(
    doc = "Creates a platform-aware alias repository for Pandoc binaries. Selects the appropriate Pandoc binary based on the target platform.",
    implementation = _alias_repository_impl,
    attrs = {
        "binaries": attr.label_keyed_string_dict(
            doc = "Mapping of Pandoc archive repository labels to platform identifiers. Used to select the correct Pandoc binary for the target platform.",
            mandatory = True,
        ),
    },
)

def pandoc_archive(*, name, platform, url, integrity, strip_prefix):
    template = _BUILD_TEMPLATE_WINDOWS if "windows" in platform else _BUILD_TEMPLATE_UNIX
    http_archive(
        name = name,
        urls = [url],
        integrity = integrity,
        strip_prefix = strip_prefix,
        build_file_content = template.format(
            name = name,
        ),
    )

    return name
