"""Playwright bzlmod extension"""

load(
    ":browser_versions.bzl",
    _BROWSER_VERSIONS = "BROWSER_VERSIONS",
)
load(
    ":browsers.bzl",
    "CHROMIUM_HEADLESS_SHELL_VERSIONS",
    "CHROMIUM_VERSIONS",
    "FFMPEG_VERSIONS",
    "FIREFOX_VERSIONS",
    "WEBKIT_VERSIONS",
    "chromium_archive",
    "chromium_headless_shell_archive",
    "ffmpeg_archive",
    "firefox_archive",
    "webkit_archive",
)
load(
    ":requirements_parser.bzl",
    _parse_playwright_version_from_requirements_content = "parse_playwright_version_from_requirements",
)

# Platform to constraint mapping
PLATFORM_TO_CONSTRAINTS = {
    "linux-aarch64": ["@platforms//os:linux", "@platforms//cpu:aarch64"],
    "linux-x86_64": ["@platforms//os:linux", "@platforms//cpu:x86_64"],
    "macos-aarch64": ["@platforms//os:macos", "@platforms//cpu:aarch64"],
    "macos-x86_64": ["@platforms//os:macos", "@platforms//cpu:x86_64"],
    "windows-x86_64": ["@platforms//os:windows", "@platforms//cpu:x86_64"],
}

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

def _parse_playwright_version_from_requirements(module_ctx, requirements_file):
    """Parse playwright version from a requirements.txt file.

    Args:
        module_ctx: Module context
        requirements_file: File object from module_ctx.read()

    Returns:
        Version string (e.g., "1.57.0") or None if not found
    """
    content = module_ctx.read(requirements_file)
    return _parse_playwright_version_from_requirements_content(content)

# Template for BUILD file that creates playwright_toolchain rule for a specific platform
_TOOLCHAIN_BUILD_TEMPLATE = """\
load("@rules_jupyter//jupyter/playwright/private:playwright.bzl", "playwright_toolchain")

playwright_toolchain(
    name = "playwright_toolchain",
    version = {playwright_version},
    chromium = {chromium_label},
    chromium_version = {chromium_version},
    chromium_headless_shell = {chromium_headless_shell_label},
    chromium_headless_shell_version = {chromium_headless_shell_version},
    firefox = {firefox_label},
    firefox_version = {firefox_version},
    webkit = {webkit_label},
    webkit_version = {webkit_version},
    ffmpeg = {ffmpeg_label},
    ffmpeg_version = {ffmpeg_version},
    visibility = ["//visibility:public"],
)

alias(
    name = "{name}",
    actual = ":playwright_toolchain",
    visibility = ["//visibility:public"],
)
"""

def _playwright_toolchain_repository_impl(repository_ctx):
    """Creates a repository with playwright_toolchain rule for a specific platform."""

    # Validate that if a browser is provided, its version is also provided
    if repository_ctx.attr.chromium and not repository_ctx.attr.chromium_version:
        fail("chromium_version is required when chromium is provided")
    if repository_ctx.attr.chromium_headless_shell and not repository_ctx.attr.chromium_headless_shell_version:
        fail("chromium_headless_shell_version is required when chromium_headless_shell is provided")
    if repository_ctx.attr.ffmpeg and not repository_ctx.attr.ffmpeg_version:
        fail("ffmpeg_version is required when ffmpeg is provided")
    if repository_ctx.attr.firefox and not repository_ctx.attr.firefox_version:
        fail("firefox_version is required when firefox is provided")
    if repository_ctx.attr.webkit and not repository_ctx.attr.webkit_version:
        fail("webkit_version is required when webkit is provided")

    # Get platform constraints
    platform = repository_ctx.attr.platform
    if platform not in PLATFORM_TO_CONSTRAINTS:
        fail("Unknown platform: {}".format(platform))
    constraints = PLATFORM_TO_CONSTRAINTS[platform]

    # Use repr() to render values as None or quoted strings
    repository_ctx.file("BUILD.bazel", _TOOLCHAIN_BUILD_TEMPLATE.format(
        name = repository_ctx.original_name,
        playwright_version = repr(repository_ctx.attr.playwright_version),
        chromium_label = repr(str(repository_ctx.attr.chromium)) if repository_ctx.attr.chromium else "None",
        chromium_version = repr(repository_ctx.attr.chromium_version) if repository_ctx.attr.chromium_version else "None",
        chromium_headless_shell_label = repr(str(repository_ctx.attr.chromium_headless_shell)) if repository_ctx.attr.chromium_headless_shell else "None",
        chromium_headless_shell_version = repr(repository_ctx.attr.chromium_headless_shell_version) if repository_ctx.attr.chromium_headless_shell_version else "None",
        firefox_label = repr(str(repository_ctx.attr.firefox)) if repository_ctx.attr.firefox else "None",
        firefox_version = repr(repository_ctx.attr.firefox_version) if repository_ctx.attr.firefox_version else "None",
        webkit_label = repr(str(repository_ctx.attr.webkit)) if repository_ctx.attr.webkit else "None",
        webkit_version = repr(repository_ctx.attr.webkit_version) if repository_ctx.attr.webkit_version else "None",
        ffmpeg_label = repr(str(repository_ctx.attr.ffmpeg)) if repository_ctx.attr.ffmpeg else "None",
        ffmpeg_version = repr(repository_ctx.attr.ffmpeg_version) if repository_ctx.attr.ffmpeg_version else "None",
        exec_constraints = json.encode(constraints),
        target_constraints = json.encode(constraints),
    ))
    repository_ctx.file("WORKSPACE.bazel", """workspace(name = "{}")""".format(
        repository_ctx.original_name,
    ))

playwright_toolchain_repository = repository_rule(
    doc = "Creates a repository with playwright_toolchain rule for a specific platform",
    implementation = _playwright_toolchain_repository_impl,
    attrs = {
        "chromium": attr.label(
            doc = "Label to the Chromium browser filegroup for this platform.",
            mandatory = False,
        ),
        "chromium_headless_shell": attr.label(
            doc = "Label to the Chromium headless-shell browser filegroup for this platform.",
            mandatory = False,
        ),
        "chromium_headless_shell_version": attr.string(
            doc = "Version string for the Chromium headless-shell browser (e.g., \"1200\"). Required if chromium_headless_shell is provided.",
            mandatory = False,
        ),
        "chromium_version": attr.string(
            doc = "Version string for the Chromium browser (e.g., \"1200\"). Required if chromium is provided.",
            mandatory = False,
        ),
        "ffmpeg": attr.label(
            doc = "Label to the FFmpeg filegroup for this platform.",
            mandatory = False,
        ),
        "ffmpeg_version": attr.string(
            doc = "Version string for FFmpeg (e.g., \"1011\"). Required if ffmpeg is provided.",
            mandatory = False,
        ),
        "firefox": attr.label(
            doc = "Label to the Firefox browser filegroup for this platform.",
            mandatory = False,
        ),
        "firefox_version": attr.string(
            doc = "Version string for the Firefox browser (e.g., \"1497\"). Required if firefox is provided.",
            mandatory = False,
        ),
        "platform": attr.string(
            doc = "Platform identifier (e.g., \"linux-x86_64\", \"macos-aarch64\", \"windows-x86_64\").",
            mandatory = True,
        ),
        "playwright_version": attr.string(
            doc = "Playwright version string (e.g., \"1.57.0\").",
            mandatory = True,
        ),
        "webkit": attr.label(
            doc = "Label to the WebKit browser filegroup for this platform.",
            mandatory = False,
        ),
        "webkit_version": attr.string(
            doc = "Version string for the WebKit browser (e.g., \"2227\"). Required if webkit is provided.",
            mandatory = False,
        ),
    },
)

_TOOLCHAIN_DECLARATION_TEMPLATE = """\
toolchain(
    name = "{toolchain_name}",
    exec_compatible_with = {exec_constraints},
    target_compatible_with = {target_constraints},
    toolchain = "{toolchain_label}",
    toolchain_type = "@rules_jupyter//jupyter/playwright:toolchain_type",
    visibility = ["//visibility:public"],
)
"""

def _playwright_toolchain_hub_impl(repository_ctx):
    """Creates a hub repository that registers all platform-specific toolchains."""
    toolchain_declarations = []

    for toolchain_name, toolchain_label in repository_ctx.attr.toolchain_labels.items():
        exec_constraints = repository_ctx.attr.exec_compatible_with.get(toolchain_name, [])
        target_constraints = repository_ctx.attr.target_compatible_with.get(toolchain_name, [])

        toolchain_declarations.append(_TOOLCHAIN_DECLARATION_TEMPLATE.format(
            toolchain_name = toolchain_name,
            exec_constraints = json.encode(exec_constraints),
            target_constraints = json.encode(target_constraints),
            toolchain_label = toolchain_label,
        ))

    repository_ctx.file("BUILD.bazel", "\n".join(toolchain_declarations))
    repository_ctx.file("WORKSPACE.bazel", """workspace(name = "{}")""".format(
        repository_ctx.name,
    ))

_playwright_toolchain_hub = repository_rule(
    doc = "Creates a hub repository that registers all platform-specific playwright toolchains",
    implementation = _playwright_toolchain_hub_impl,
    attrs = {
        "exec_compatible_with": attr.string_list_dict(
            doc = "A list of constraints for the execution platform for each toolchain, keyed by toolchain name.",
            mandatory = True,
        ),
        "target_compatible_with": attr.string_list_dict(
            doc = "A list of constraints for the target platform for each toolchain, keyed by toolchain name.",
            mandatory = True,
        ),
        "toolchain_labels": attr.string_dict(
            doc = "The label of the toolchain implementation target, keyed by toolchain name.",
            mandatory = True,
        ),
    },
)

def _playwright_impl(module_ctx):
    root_mod, rules_mod = _find_modules(module_ctx)

    toolchains = root_mod.tags.toolchain
    if not toolchains:
        toolchains = rules_mod.tags.toolchain
    direct_deps = []

    for attrs in toolchains:
        # Determine version - either from explicit version or from requirements.txt
        if attrs.version_from_requirements:
            version = _parse_playwright_version_from_requirements(module_ctx, attrs.version_from_requirements)
            if not version:
                fail("Could not find playwright version in requirements file: {}".format(attrs.version_from_requirements))
        elif attrs.version:
            version = attrs.version
        else:
            fail("Either 'version' or 'version_from_requirements' must be specified")

        name = attrs.name

        # Get browser versions from browser_versions.bzl based on playwright version
        browser_versions = _BROWSER_VERSIONS.get(version, {})
        if not browser_versions:
            available_versions = list(_BROWSER_VERSIONS.keys())
            version_list = ", ".join(available_versions[:10])
            if len(available_versions) > 10:
                version_list += "..."
            fail("Playwright version {} not found in BROWSER_VERSIONS. Available versions: {}".format(
                version,
                version_list,
            ))

        # All browser versions are determined by the playwright version
        chromium_version = browser_versions.get("chromium")
        chromium_headless_shell_version = browser_versions.get("chromium-headless-shell")
        firefox_version = browser_versions.get("firefox")
        webkit_version = browser_versions.get("webkit")
        ffmpeg_version = browser_versions.get("ffmpeg")

        # Collect all platforms that have at least one browser available
        all_platforms = set()
        if chromium_version and chromium_version in CHROMIUM_VERSIONS:
            all_platforms.update(CHROMIUM_VERSIONS[chromium_version].keys())
        if chromium_headless_shell_version and chromium_headless_shell_version in CHROMIUM_HEADLESS_SHELL_VERSIONS:
            all_platforms.update(CHROMIUM_HEADLESS_SHELL_VERSIONS[chromium_headless_shell_version].keys())
        if firefox_version and firefox_version in FIREFOX_VERSIONS:
            all_platforms.update(FIREFOX_VERSIONS[firefox_version].keys())
        if webkit_version and webkit_version in WEBKIT_VERSIONS:
            all_platforms.update(WEBKIT_VERSIONS[webkit_version].keys())
        if ffmpeg_version and ffmpeg_version in FFMPEG_VERSIONS:
            all_platforms.update(FFMPEG_VERSIONS[ffmpeg_version].keys())

        # Create platform-specific toolchain repositories
        toolchain_names = []
        toolchain_labels = {}
        exec_compatible_with = {}
        target_compatible_with = {}

        for platform in all_platforms:
            # Skip platforms that don't have constraint mappings
            if platform not in PLATFORM_TO_CONSTRAINTS:
                continue

            # Create archive repositories for each browser available on this platform
            browser_labels = {}
            browser_versions_dict = {}

            # Chromium
            if chromium_version and chromium_version in CHROMIUM_VERSIONS and platform in CHROMIUM_VERSIONS[chromium_version]:
                repo_name = "{}_{}_{}".format(name, "chromium", platform)
                chromium_archive(
                    name = repo_name,
                    platform = platform,
                    urls = CHROMIUM_VERSIONS[chromium_version][platform]["urls"],
                    integrity = CHROMIUM_VERSIONS[chromium_version][platform]["integrity"],
                    strip_prefix = CHROMIUM_VERSIONS[chromium_version][platform]["strip_prefix"],
                )
                browser_labels["chromium"] = "@{}".format(repo_name)
                browser_versions_dict["chromium_version"] = chromium_version

            # Chromium headless-shell
            if chromium_headless_shell_version and chromium_headless_shell_version in CHROMIUM_HEADLESS_SHELL_VERSIONS and platform in CHROMIUM_HEADLESS_SHELL_VERSIONS[chromium_headless_shell_version]:
                repo_name = "{}_{}_{}".format(name, "chromium_headless_shell", platform)
                chromium_headless_shell_archive(
                    name = repo_name,
                    platform = platform,
                    urls = CHROMIUM_HEADLESS_SHELL_VERSIONS[chromium_headless_shell_version][platform]["urls"],
                    integrity = CHROMIUM_HEADLESS_SHELL_VERSIONS[chromium_headless_shell_version][platform]["integrity"],
                    strip_prefix = CHROMIUM_HEADLESS_SHELL_VERSIONS[chromium_headless_shell_version][platform]["strip_prefix"],
                )
                browser_labels["chromium_headless_shell"] = "@{}".format(repo_name)
                browser_versions_dict["chromium_headless_shell_version"] = chromium_headless_shell_version

            # Firefox
            if firefox_version and firefox_version in FIREFOX_VERSIONS and platform in FIREFOX_VERSIONS[firefox_version]:
                repo_name = "{}_{}_{}".format(name, "firefox", platform)
                firefox_archive(
                    name = repo_name,
                    platform = platform,
                    urls = FIREFOX_VERSIONS[firefox_version][platform]["urls"],
                    integrity = FIREFOX_VERSIONS[firefox_version][platform]["integrity"],
                    strip_prefix = FIREFOX_VERSIONS[firefox_version][platform]["strip_prefix"],
                )
                browser_labels["firefox"] = "@{}".format(repo_name)
                browser_versions_dict["firefox_version"] = firefox_version

            # WebKit
            if webkit_version and webkit_version in WEBKIT_VERSIONS and platform in WEBKIT_VERSIONS[webkit_version]:
                repo_name = "{}_{}_{}".format(name, "webkit", platform)
                webkit_archive(
                    name = repo_name,
                    platform = platform,
                    urls = WEBKIT_VERSIONS[webkit_version][platform]["urls"],
                    integrity = WEBKIT_VERSIONS[webkit_version][platform]["integrity"],
                    strip_prefix = WEBKIT_VERSIONS[webkit_version][platform]["strip_prefix"],
                )
                browser_labels["webkit"] = "@{}".format(repo_name)
                browser_versions_dict["webkit_version"] = webkit_version

            # FFmpeg
            if ffmpeg_version and ffmpeg_version in FFMPEG_VERSIONS and platform in FFMPEG_VERSIONS[ffmpeg_version]:
                repo_name = "{}_{}_{}".format(name, "ffmpeg", platform)
                ffmpeg_archive(
                    name = repo_name,
                    platform = platform,
                    urls = FFMPEG_VERSIONS[ffmpeg_version][platform]["urls"],
                    integrity = FFMPEG_VERSIONS[ffmpeg_version][platform]["integrity"],
                    strip_prefix = FFMPEG_VERSIONS[ffmpeg_version][platform]["strip_prefix"],
                )
                browser_labels["ffmpeg"] = "@{}".format(repo_name)
                browser_versions_dict["ffmpeg_version"] = ffmpeg_version

            # Create platform-specific toolchain repository
            toolchain_repo_name = "{}_{}".format(name, platform.replace("-", "_"))
            playwright_toolchain_repository(
                name = toolchain_repo_name,
                platform = platform,
                playwright_version = version,
                chromium = browser_labels.get("chromium"),
                chromium_version = browser_versions_dict.get("chromium_version"),
                chromium_headless_shell = browser_labels.get("chromium_headless_shell"),
                chromium_headless_shell_version = browser_versions_dict.get("chromium_headless_shell_version"),
                firefox = browser_labels.get("firefox"),
                firefox_version = browser_versions_dict.get("firefox_version"),
                webkit = browser_labels.get("webkit"),
                webkit_version = browser_versions_dict.get("webkit_version"),
                ffmpeg = browser_labels.get("ffmpeg"),
                ffmpeg_version = browser_versions_dict.get("ffmpeg_version"),
            )

            toolchain_names.append(toolchain_repo_name)
            toolchain_labels[toolchain_repo_name] = "@{}".format(toolchain_repo_name)
            exec_compatible_with[toolchain_repo_name] = PLATFORM_TO_CONSTRAINTS[platform]
            target_compatible_with[toolchain_repo_name] = PLATFORM_TO_CONSTRAINTS[platform]

        # Create hub repository
        _playwright_toolchain_hub(
            name = name,
            toolchain_labels = toolchain_labels,
            exec_compatible_with = exec_compatible_with,
            target_compatible_with = target_compatible_with,
        )

        direct_deps.append(name)

    return module_ctx.extension_metadata(
        reproducible = True,
        root_module_direct_deps = direct_deps,
        root_module_direct_dev_deps = [],
    )

_TOOLCHAIN_TAG = tag_class(
    doc = "Playwright toolchain configuration",
    attrs = {
        "name": attr.string(
            doc = "Name of the toolchain repository",
            default = "playwright_toolchains",
        ),
        "version": attr.string(
            doc = "Playwright version (e.g., '1.57.0'). Browser versions will be auto-selected based on this. Mutually exclusive with `version_from_requirements`.",
        ),
        "version_from_requirements": attr.label(
            doc = "A python `requirements.txt` file used for parsing the desired `playwright` version. Mutually exclusive with version.",
            allow_single_file = True,
        ),
        # "version_from_package_json": attr.label(
        #     doc = "A python `requirements.txt` file used for parsing the desired `playwright` version. Mutually exclusive with version.",
        #     allow_single_file = True,
        # ),
        # "version_from_pnpm_lock": attr.label(
        #     doc = "A python `requirements.txt` file used for parsing the desired `playwright` version. Mutually exclusive with version.",
        #     allow_single_file = True,
        # ),
    },
)

playwright = module_extension(
    doc = "Playwright browser dependencies.",
    implementation = _playwright_impl,
    tag_classes = {
        "toolchain": _TOOLCHAIN_TAG,
    },
)
