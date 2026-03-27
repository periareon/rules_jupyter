"""Self-contained repository rule for Chromium headless-shell with system libraries.

Downloads the browser archive and all required Debian packages directly,
extracts .so files next to the browser binary, and produces a filegroup
with select() to optionally include them at runtime via RPATH=$ORIGIN.
"""

load(
    "//tools/debian:debian_archive.bzl",
    "download_and_extract",
)

_BUILD_TEMPLATE = """\
CHROME_HEADLESS = glob(["chrome-headless-shell-linux*/*headless-shell"], allow_empty = True)
CHROME_LINUX = glob(["chrome-linux*/*headless_shell"], allow_empty = True)

BROWSER_SRCS = CHROME_HEADLESS if CHROME_HEADLESS else CHROME_LINUX
BROWSER_DIR = "chrome-headless-shell-linux" if CHROME_HEADLESS else "chrome-linux"

ALL_DATA = glob(
    include = ["{{}}*/**".format(BROWSER_DIR)],
    exclude = BROWSER_SRCS,
)

SYSROOT_SO_FILES = {sysroot_so_files}

DATA_WITHOUT_SYSROOT = glob(
    include = ["{{}}*/**".format(BROWSER_DIR)],
    exclude = BROWSER_SRCS + SYSROOT_SO_FILES,
)

filegroup(
    name = "browser",
    srcs = BROWSER_SRCS,
    data = ALL_DATA,
    visibility = ["//visibility:public"],
)

alias(
    name = "{name}",
    actual = select({{
        "@rules_jupyter//playwright/settings:embedded_linux_chrome_sys_libs_enabled": ":browser",
        "//conditions:default": "{original_chromium}",
    }}),
    visibility = ["//visibility:public"],
)
"""

_DEBIAN_LIB_DIRS = [
    "usr/lib/x86_64-linux-gnu",
    "usr/lib/aarch64-linux-gnu",
    "lib/x86_64-linux-gnu",
    "lib/aarch64-linux-gnu",
    "usr/lib",
    "lib",
]

def _is_shared_lib(basename):
    """Returns True if the filename looks like a shared library (.so or .so.N...)."""
    parts = basename.split(".so")
    if len(parts) < 2:
        return False
    suffix = parts[-1]
    return suffix == "" or suffix.startswith(".")

def _is_browser_dir(basename):
    """Returns True if the directory name matches a Chromium browser directory."""
    return basename.startswith("chrome-headless-shell-linux") or basename.startswith("chrome-linux")

def _copy_shared_libs(repository_ctx, deb_root, dest_dir):
    """Scan known Debian lib directories and copy .so files into dest_dir.

    Returns:
        List of relative paths (from repo root) for each copied file.
    """
    copied = []
    for lib_dir in _DEBIAN_LIB_DIRS:
        candidate = deb_root.get_child(lib_dir)
        if not candidate.exists:
            continue
        for entry in candidate.readdir():
            if entry.is_dir:
                continue
            if _is_shared_lib(entry.basename):
                dest = dest_dir.get_child(entry.basename)
                if not dest.exists:
                    repository_ctx.execute(
                        ["cp", str(entry), str(dest)],
                        quiet = True,
                    )
                    copied.append("{}/{}".format(dest_dir.basename, entry.basename))
    return copied

def _playwright_chromium_with_sysroot_impl(repository_ctx):
    repository_ctx.download_and_extract(
        url = repository_ctx.attr.browser_urls,
        integrity = repository_ctx.attr.browser_integrity,
        stripPrefix = repository_ctx.attr.browser_strip_prefix,
    )

    browser_bin_dir = None
    for entry in repository_ctx.path("").readdir():
        if _is_browser_dir(entry.basename):
            browser_bin_dir = entry
            break

    if not browser_bin_dir:
        fail("Could not find browser binary directory in browser archive")

    sysroot_so_files = []
    packages = json.decode(repository_ctx.attr.sysroot_packages_json)
    for i, pkg in enumerate(packages):
        prefix = ".sysroot_tmp_{}".format(i)
        download_and_extract(
            repository_ctx = repository_ctx,
            urls = pkg["urls"],
            sha256 = pkg.get("sha256", ""),
            integrity = pkg.get("integrity", ""),
            add_prefix = prefix,
        )
        sysroot_so_files.extend(
            _copy_shared_libs(
                repository_ctx,
                repository_ctx.path(prefix),
                browser_bin_dir,
            ),
        )
        repository_ctx.delete(prefix)

    repository_ctx.file("BUILD.bazel", _BUILD_TEMPLATE.format(
        name = repository_ctx.original_name,
        sysroot_so_files = json.encode(sysroot_so_files),
        original_chromium = repository_ctx.attr.original_chromium
    ))
    repository_ctx.file("WORKSPACE.bazel", """workspace(name = "{}")""".format(
        repository_ctx.original_name,
    ))

playwright_chromium_with_sysroot = repository_rule(
    doc = """\
Self-contained repository that downloads Chromium headless-shell and all required
system library Debian packages. Extracts .so files next to the browser binary and
produces a filegroup with select() to optionally include the sysroot libraries
when the experimental_embedded_linux_chrome_sys_libs flag is enabled.
""",
    implementation = _playwright_chromium_with_sysroot_impl,
    attrs = {
        "browser_integrity": attr.string(
            doc = "Integrity hash for the browser archive.",
            mandatory = True,
        ),
        "browser_strip_prefix": attr.string(
            doc = "Strip prefix for the browser archive.",
            default = "",
        ),
        "browser_urls": attr.string_list(
            doc = "URLs to download the Chromium headless-shell browser archive.",
            mandatory = True,
        ),
        "sysroot_packages_json": attr.string(
            doc = "JSON-encoded list of sysroot package descriptors, each with 'urls' and 'integrity' fields.",
            mandatory = True,
        ),
        "original_chromium": attr.label(
            doc = "The label to the original chromium filegroup.",
            mandatory = True,
        ),
    },
)
