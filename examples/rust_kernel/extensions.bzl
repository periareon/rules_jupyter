"""Rust Kernel extensions"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

DEFAULT_EVCXR_VERSION = "0.21.1"

EVCXR_VERSIONS = {
    "0.21.1": {
        "linux-x86_64": {
            "integrity": "sha256-jaj3FnpmrXDBfsAcLBmSSWKYeVmw/2Q0v6qxRZfRCgs=",
            "strip_prefix": "evcxr_jupyter-v0.21.1-x86_64-unknown-linux-gnu",
            "url": "https://github.com/evcxr/evcxr/releases/download/v0.21.1/evcxr_jupyter-v0.21.1-x86_64-unknown-linux-gnu.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-ayfxA1I0LbloyPwzTIM4YZJgW5DvnPn8DAFGtlfWcRw=",
            "strip_prefix": "evcxr_jupyter-v0.21.1-aarch64-apple-darwin",
            "url": "https://github.com/evcxr/evcxr/releases/download/v0.21.1/evcxr_jupyter-v0.21.1-aarch64-apple-darwin.tar.gz",
        },
        "windows-x86_64": {
            "integrity": "sha256-F0C1gvDa4anULOqg5TRdzcbl/JB1OjH382WFgnMS05g=",
            "strip_prefix": "evcxr_jupyter-v0.21.1-x86_64-pc-windows-msvc",
            "url": "https://github.com/evcxr/evcxr/releases/download/v0.21.1/evcxr_jupyter-v0.21.1-x86_64-pc-windows-msvc.zip",
        },
    },
}

# evcxr_jupyter BUILD templates
_EVCXR_BUILD_TEMPLATE_UNIX = """\
filegroup(
    name = "{name}",
    srcs = ["evcxr_jupyter"],
    data = glob(
        ["**"],
        exclude = ["evcxr_jupyter"],
    ),
    visibility = ["//visibility:public"],
)
"""

_EVCXR_BUILD_TEMPLATE_WINDOWS = """\
filegroup(
    name = "{name}",
    srcs = ["evcxr_jupyter.exe"],
    data = glob(
        ["**"],
        exclude = ["evcxr_jupyter.exe"],
    ),
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
    # Build targets dict: platform -> filegroup label
    # Use canonical format with @@ for repositories in the same module extension
    targets_dict = {}
    for binary_label, platform in repository_ctx.attr.binaries.items():
        # Extract repository name from workspace_name (e.g., "+jupyter+evcxr_jupyter_0.21.1_linux-x86_64")
        workspace_name = binary_label.workspace_name
        if "+" in workspace_name:
            repo_name = workspace_name.split("+")[-1]  # "evcxr_jupyter_0.21.1_linux-x86_64"
        else:
            repo_name = workspace_name

        # Construct full label with @@ for canonical format: @@workspace_name//:repo_name
        filegroup_label = "@@{}//:{}".format(workspace_name, repo_name)
        targets_dict["@rules_jupyter//tools/constraints:{}".format(platform)] = filegroup_label

    repository_ctx.file("BUILD.bazel", _ALIAS_REPO_TEMPLATE.format(
        name = repository_ctx.original_name,
        targets = json.encode_indent(targets_dict),
    ))

    repository_ctx.file("WORKSPACE.bazel", """workspace(name = "{}")""".format(
        repository_ctx.name,
    ))

evcxr_alias_repository = repository_rule(
    doc = "Creates a platform-aware alias repository for evcxr_jupyter binaries. Selects the appropriate binary based on the target platform.",
    implementation = _alias_repository_impl,
    attrs = {
        "binaries": attr.label_keyed_string_dict(
            doc = "Mapping of evcxr_jupyter archive repository labels to platform identifiers. Used to select the correct binary for the target platform.",
            mandatory = True,
        ),
    },
)

def evcxr_archive(*, name, platform, url, integrity, strip_prefix):
    """Create an http_archive for an evcxr_jupyter binary archive."""
    template = _EVCXR_BUILD_TEMPLATE_WINDOWS if "windows" in platform else _EVCXR_BUILD_TEMPLATE_UNIX
    http_archive(
        name = name,
        urls = [url],
        integrity = integrity,
        strip_prefix = strip_prefix,
        build_file_content = template.format(name = name),
    )
    return name

def _find_modules(module_ctx):
    root = None
    rules_module = None
    for mod in module_ctx.modules:
        if mod.is_root:
            root = mod
        if mod.name == "rules_jupyter":
            rules_module = mod
    if root == None:
        root = rules_module
    if rules_module == None:
        fail("Unable to find rules_jupyter module")

    return root, rules_module

def _evcxr_impl(module_ctx):
    root_mod, rules_mod = _find_modules(module_ctx)

    # Process evcxr_jupyter tags
    evcxrs = root_mod.tags.jupyter
    if not evcxrs:
        evcxrs = rules_mod.tags.jupyter

    for attrs in evcxrs:
        version = attrs.version
        name = attrs.name
        binaries = {}
        archive_repos = []
        for platform, data in EVCXR_VERSIONS[version].items():
            repo_name = "{}_{}_{}".format(name, version, platform)

            evcxr_archive(
                name = repo_name,
                platform = platform,
                url = data["url"],
                integrity = data["integrity"],
                strip_prefix = data["strip_prefix"],
            )
            binaries[str("@{}".format(repo_name))] = platform
            archive_repos.append(repo_name)

        evcxr_alias_repository(
            name = name,
            binaries = binaries,
        )

        direct_deps.append(name)

        # Add archive repositories to direct_deps so they're visible
        direct_deps.extend(archive_repos)

    return module_ctx.extension_metadata(
        reproducible = True,
        root_module_direct_deps = direct_deps,
        root_module_direct_dev_deps = [],
    )

_JUPYTER_TAG = tag_class(
    doc = "Tag class for configuring evcxr_jupyter in the Jupyter module extension. Use this to specify which evcxr_jupyter version to use.",
    attrs = {
        "name": attr.string(
            doc = "Name of the evcxr_jupyter repository to create. This name can be referenced in use_repo() to access the evcxr_jupyter binary.",
            mandatory = True,
        ),
        "version": attr.string(
            doc = "evcxr_jupyter version to use. Must be one of the versions available in EVCXR_VERSIONS. Defaults to the latest version.",
            default = DEFAULT_EVCXR_VERSION,
            values = EVCXR_VERSIONS.keys(),
        ),
    },
)

evcxr = module_extension(
    doc = "Evcxr dependencies.",
    implementation = _evcxr_impl,
    tag_classes = {
        "jupyter": _JUPYTER_TAG,
    },
)
