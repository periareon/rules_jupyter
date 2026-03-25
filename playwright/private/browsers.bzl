"""Rules for fetching Playwright browser archives"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load(":chromium_headless_shell_versions.bzl", _CHROMIUM_HEADLESS_SHELL_VERSIONS = "CHROMIUM_HEADLESS_SHELL_VERSIONS")
load(":chromium_versions.bzl", _CHROMIUM_VERSIONS = "CHROMIUM_VERSIONS")
load(":ffmpeg_versions.bzl", _FFMPEG_VERSIONS = "FFMPEG_VERSIONS")
load(":firefox_versions.bzl", _FIREFOX_VERSIONS = "FIREFOX_VERSIONS")
load(":webkit_versions.bzl", _WEBKIT_VERSIONS = "WEBKIT_VERSIONS")

# Version dictionaries
CHROMIUM_VERSIONS = _CHROMIUM_VERSIONS
CHROMIUM_HEADLESS_SHELL_VERSIONS = _CHROMIUM_HEADLESS_SHELL_VERSIONS
FIREFOX_VERSIONS = _FIREFOX_VERSIONS
WEBKIT_VERSIONS = _WEBKIT_VERSIONS
FFMPEG_VERSIONS = _FFMPEG_VERSIONS

# Chromium BUILD templates
_CHROMIUM_BUILD_TEMPLATE_LINUX = """\
filegroup(
    name = "{name}",
    srcs = glob(["chrome-linux*/chrome"]),
    data = glob(
        include = ["chrome-linux*/**"],
        exclude = ["chrome-linux*/chrome"],
    ),
    visibility = ["//visibility:public"],
)
"""

_CHROMIUM_BUILD_TEMPLATE_MACOS = """\
CHROME = glob(["chrome-mac*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"], allow_empty = True)
CHROMIUM = glob(["chrome-mac*/Chromium.app/Contents/MacOS/Chromium"], allow_empty = True)

filegroup(
    name = "{name}",
    srcs = CHROME if CHROME else CHROMIUM,
    data = glob(
        include = ["chrome-mac*/**"],
        exclude = CHROME + CHROMIUM,
    ),
    visibility = ["//visibility:public"],
)
"""

_CHROMIUM_BUILD_TEMPLATE_WINDOWS = """\
filegroup(
    name = "{name}",
    srcs = glob(["chrome-win*/chrome.exe"]),
    data = glob(
        include = ["chrome-win*/**"],
        exclude = ["chrome-win*/chrome.exe"],
    ),
    visibility = ["//visibility:public"],
)
"""

# Chromium headless-shell BUILD templates
_CHROMIUM_HEADLESS_SHELL_BUILD_TEMPLATE_LINUX = """\
CHROME_HEADLESS = glob(["chrome-headless-shell-linux*/*headless-shell"], allow_empty = True)
CHROME_LINUX = glob(["chrome-linux*/*headless_shell"], allow_empty = True)

filegroup(
    name = "{name}",
    srcs = CHROME_HEADLESS if CHROME_HEADLESS else CHROME_LINUX,
    data = glob(
        include = ["{{}}*/**".format("chrome-headless-shell-linux" if CHROME_HEADLESS else "chrome-linux")],
        exclude = CHROME_HEADLESS + CHROME_LINUX,
    ),
    visibility = ["//visibility:public"],
)
"""

_CHROMIUM_HEADLESS_SHELL_BUILD_TEMPLATE_MACOS = """\
filegroup(
    name = "{name}",
    srcs = glob(["chrome-headless-shell-mac*/chrome-headless-shell"]),
    data = glob(
        include = ["chrome-headless-shell-mac*/**"],
        exclude = ["chrome-headless-shell-mac*/chrome-headless-shell"],
    ),
    visibility = ["//visibility:public"],
)
"""

_CHROMIUM_HEADLESS_SHELL_BUILD_TEMPLATE_WINDOWS = """\
filegroup(
    name = "{name}",
    srcs = glob(["chrome-headless-shell-win*/chrome-headless-shell.exe"]),
    data = glob(
        include = ["chrome-headless-shell-win*/**"],
        exclude = ["chrome-headless-shell-win*/chrome-headless-shell.exe"],
    ),
    visibility = ["//visibility:public"],
)
"""

# Firefox BUILD templates
_FIREFOX_BUILD_TEMPLATE_LINUX = """\
filegroup(
    name = "{name}",
    srcs = ["firefox/firefox"],
    data = glob(
        include = ["firefox/**"],
        exclude = ["firefox/firefox"],
    ),
    visibility = ["//visibility:public"],
)
"""

_FIREFOX_BUILD_TEMPLATE_MACOS = """\
filegroup(
    name = "{name}",
    srcs = ["firefox/Nightly.app/Contents/MacOS/firefox"],
    data = glob(
        include = ["firefox/**"],
        exclude = ["firefox/Nightly.app/Contents/MacOS/firefox"],
    ),
    visibility = ["//visibility:public"],
)
"""

_FIREFOX_BUILD_TEMPLATE_WINDOWS = """\
filegroup(
    name = "{name}",
    srcs = ["firefox/firefox.exe"],
    data = glob(
        include = ["firefox/**"],
        exclude = ["firefox/firefox.exe"],
    ),
    visibility = ["//visibility:public"],
)
"""

# WebKit BUILD templates
_WEBKIT_BUILD_TEMPLATE_LINUX = """\
filegroup(
    name = "{name}",
    srcs = ["pw_run.sh"],
    data = glob(
        include = ["**"],
        exclude = ["pw_run.sh", "*.bazel"],
    ),
    visibility = ["//visibility:public"],
)
"""

_WEBKIT_BUILD_TEMPLATE_WINDOWS = """\
filegroup(
    name = "{name}",
    srcs = ["Playwright.exe"],
    data = glob(
        include = ["**"],
        exclude = ["Playwright.exe"],
    ),
    visibility = ["//visibility:public"],
)
"""

# FFmpeg BUILD templates
_FFMPEG_BUILD_TEMPLATE_MACOS = """\
filegroup(
    name = "{name}",
    srcs = ["ffmpeg-mac"],
    data = glob(
        include = ["**"],
        exclude = [
            "ffmpeg-mac",
            "*.bazel",
            "WORKSPACE",
            "BUILD",
        ],
    ),
    visibility = ["//visibility:public"],
)
"""

_FFMPEG_BUILD_TEMPLATE_LINUX = """\
filegroup(
    name = "{name}",
    srcs = ["ffmpeg-linux"],
    data = glob(
        include = ["**"],
        exclude = [
            "ffmpeg-linux",
            "*.bazel",
            "WORKSPACE",
            "BUILD",
        ],
    ),
    visibility = ["//visibility:public"],
)
"""

_FFMPEG_BUILD_TEMPLATE_WINDOWS = """\
filegroup(
    name = "{name}",
    srcs = ["ffmpeg-win64.exe"],
    data = glob(
        include = ["**"],
        exclude = [
            "ffmpeg-win64.exe",
            "*.bazel",
            "WORKSPACE",
            "BUILD",
        ],
    ),
    visibility = ["//visibility:public"],
)
"""

def _get_chromium_build_template(platform):
    """Get the BUILD template for Chromium based on platform and revision.

    Args:
        platform: Platform identifier
    """
    if platform.startswith("linux"):
        return _CHROMIUM_BUILD_TEMPLATE_LINUX
    if platform.startswith("macos"):
        return _CHROMIUM_BUILD_TEMPLATE_MACOS
    if platform.startswith("windows"):
        return _CHROMIUM_BUILD_TEMPLATE_WINDOWS

    fail("Unknown platform: {}".format(platform))

def _get_chromium_headless_shell_build_template(platform):
    """Get the BUILD template for Chromium headless-shell based on platform."""
    if platform.startswith("linux"):
        return _CHROMIUM_HEADLESS_SHELL_BUILD_TEMPLATE_LINUX
    if platform.startswith("macos"):
        return _CHROMIUM_HEADLESS_SHELL_BUILD_TEMPLATE_MACOS
    if platform.startswith("windows"):
        return _CHROMIUM_HEADLESS_SHELL_BUILD_TEMPLATE_WINDOWS

    fail("Unknown platform: {}".format(platform))

def _get_firefox_build_template(platform):
    """Get the BUILD template for Firefox based on platform."""
    if platform.startswith("windows"):
        return _FIREFOX_BUILD_TEMPLATE_WINDOWS
    elif platform.startswith("macos"):
        return _FIREFOX_BUILD_TEMPLATE_MACOS
    else:
        return _FIREFOX_BUILD_TEMPLATE_LINUX

def _get_webkit_build_template(platform):
    """Get the BUILD template for WebKit based on platform."""
    if platform.startswith("windows"):
        return _WEBKIT_BUILD_TEMPLATE_WINDOWS
    else:
        return _WEBKIT_BUILD_TEMPLATE_LINUX

def _get_ffmpeg_build_template(platform):
    """Get the BUILD template for FFmpeg based on platform."""
    if platform.startswith("windows"):
        return _FFMPEG_BUILD_TEMPLATE_WINDOWS
    elif platform.startswith("macos"):
        return _FFMPEG_BUILD_TEMPLATE_MACOS
    else:
        return _FFMPEG_BUILD_TEMPLATE_LINUX

def chromium_archive(*, name, platform, urls, integrity, strip_prefix):
    """Create an http_archive for a Chromium browser archive.

    Args:
        name: Repository name
        platform: Platform identifier
        urls: Archive URLs
        integrity: Archive integrity hash
        strip_prefix: Strip prefix for archive extraction
    """
    template = _get_chromium_build_template(platform)
    http_archive(
        name = name,
        urls = urls,
        integrity = integrity,
        strip_prefix = strip_prefix,
        build_file_content = template.format(name = name),
    )
    return name

def chromium_headless_shell_archive(*, name, platform, urls, integrity, strip_prefix):
    """Create an http_archive for a Chromium headless-shell browser archive."""
    template = _get_chromium_headless_shell_build_template(platform)
    http_archive(
        name = name,
        urls = urls,
        integrity = integrity,
        strip_prefix = strip_prefix,
        build_file_content = template.format(name = name),
    )
    return name

def firefox_archive(*, name, platform, urls, integrity, strip_prefix):
    """Create an http_archive for a Firefox browser archive."""
    template = _get_firefox_build_template(platform)
    http_archive(
        name = name,
        urls = urls,
        integrity = integrity,
        strip_prefix = strip_prefix,
        build_file_content = template.format(name = name),
    )
    return name

def webkit_archive(*, name, platform, urls, integrity, strip_prefix):
    """Create an http_archive for a WebKit browser archive."""
    template = _get_webkit_build_template(platform)
    http_archive(
        name = name,
        urls = urls,
        integrity = integrity,
        strip_prefix = strip_prefix,
        build_file_content = template.format(name = name),
    )
    return name

def ffmpeg_archive(*, name, platform, urls, integrity, strip_prefix):
    """Create an http_archive for an FFmpeg archive."""
    template = _get_ffmpeg_build_template(platform)
    http_archive(
        name = name,
        urls = urls,
        integrity = integrity,
        strip_prefix = strip_prefix,
        build_file_content = template.format(name = name),
    )
    return name

# Common alias repository template
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

browser_alias_repository = repository_rule(
    doc = "Alias repository for Playwright browser archives",
    implementation = _alias_repository_impl,
    attrs = {
        "binaries": attr.label_keyed_string_dict(
            doc = "Mapping of repository labels to platform identifiers",
            mandatory = True,
        ),
    },
)
