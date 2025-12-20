"""# Jupyter bzlmod extensions"""

# buildifier: disable=bzl-visibility
load(
    "//jupyter/playwright/private:extensions.bzl",
    _playwright = "playwright",
)
load(
    "//jupyter/private:pandoc.bzl",
    "DEFAULT_PANDOC_VERSION",
    "PANDOC_VERSIONS",
    "pandoc_alias_repository",
    "pandoc_archive",
)

playwright = _playwright

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

def _jupyter_impl(module_ctx):
    root_mod, rules_mod = _find_modules(module_ctx)

    pandocs = root_mod.tags.pandoc
    if not pandocs:
        pandocs = rules_mod.tags.pandoc

    direct_deps = []
    for attrs in pandocs:
        version = attrs.version
        name = attrs.name
        binaries = {}
        for platform, data in PANDOC_VERSIONS[version].items():
            repo_name = "{}_{}_{}".format(name, version, platform)

            pandoc_archive(
                name = repo_name,
                platform = platform,
                url = data["url"],
                integrity = data["integrity"],
                strip_prefix = data["strip_prefix"],
            )
            binaries[str("@{}".format(repo_name))] = platform

        pandoc_alias_repository(
            name = name,
            binaries = binaries,
        )

        direct_deps.append(name)

    return module_ctx.extension_metadata(
        reproducible = True,
        root_module_direct_deps = direct_deps,
        root_module_direct_dev_deps = [],
    )

_PANDOC_TAG = tag_class(
    doc = "Tag class for configuring Pandoc in the Jupyter module extension. Use this to specify which Pandoc version to use.",
    attrs = {
        "name": attr.string(
            doc = "Name of the Pandoc repository to create. This name can be referenced in use_repo() to access the Pandoc binary.",
            mandatory = True,
        ),
        "version": attr.string(
            doc = "Pandoc version to use. Must be one of the versions available in PANDOC_VERSIONS. Defaults to the latest version.",
            default = DEFAULT_PANDOC_VERSION,
            values = PANDOC_VERSIONS.keys(),
        ),
    },
)

jupyter = module_extension(
    doc = "Jupyter dependencies.",
    implementation = _jupyter_impl,
    tag_classes = {
        "pandoc": _PANDOC_TAG,
    },
)
