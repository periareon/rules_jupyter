"""Repository rule for bundling Chromium headless-shell with system library dependencies.

Creates a repository that symlinks a browser archive's files alongside .so files
extracted from Debian packages, producing a real filegroup where RPATH=$ORIGIN
resolves the sysroot libraries at runtime.
"""

_BUILD_TEMPLATE = """\
CHROME_HEADLESS = glob(["chrome-headless-shell-linux*/*headless-shell"], allow_empty = True)
CHROME_LINUX = glob(["chrome-linux*/*headless_shell"], allow_empty = True)

BROWSER_SRCS = CHROME_HEADLESS if CHROME_HEADLESS else CHROME_LINUX
BROWSER_DIR = "chrome-headless-shell-linux" if CHROME_HEADLESS else "chrome-linux"

filegroup(
    name = "_with_sysroot",
    srcs = BROWSER_SRCS,
    data = glob(
        include = ["{{}}*/**".format(BROWSER_DIR)],
        exclude = BROWSER_SRCS,
    ),
    visibility = ["//visibility:public"],
)

alias(
    name = "{name}",
    actual = select({{
        "@rules_jupyter//playwright/settings:embedded_linux_chrome_sys_libs_enabled": ":_with_sysroot",
        "//conditions:default": "{browser_label}",
    }}),
    visibility = ["//visibility:public"],
)
"""

def _is_shared_lib(basename):
    """Returns True if the filename looks like a shared library (.so or .so.N...)."""
    parts = basename.split(".so")
    if len(parts) < 2:
        return False
    suffix = parts[-1]
    return suffix == "" or suffix.startswith(".")

def _symlink_shared_libs(repository_ctx, root, dest_dir):
    """Recursively walk `root` and symlink .so files into `dest_dir`."""
    for entry in root.readdir():
        if entry.is_dir:
            _symlink_shared_libs(repository_ctx, entry, dest_dir)
        elif _is_shared_lib(entry.basename):
            dest = dest_dir.get_child(entry.basename)
            if not dest.exists:
                repository_ctx.symlink(entry, dest)

def _playwright_chromium_with_sysroot_impl(repository_ctx):
    # Symlink browser archive contents into this repo
    browser_build = repository_ctx.path(
        Label("@{}//:BUILD.bazel".format(repository_ctx.attr.browser)),
    )
    for entry in browser_build.dirname.readdir():
        if entry.basename in ["BUILD.bazel", "WORKSPACE.bazel", "WORKSPACE", "MODULE.bazel"]:
            continue
        repository_ctx.symlink(entry, entry.basename)

    # Find the browser binary directory (e.g. chrome-headless-shell-linux64/)
    browser_bin_dir = None
    for entry in repository_ctx.path(".").readdir():
        basename = entry.basename
        if basename.startswith("chrome-headless-shell-linux") or basename.startswith("chrome-linux"):
            browser_bin_dir = entry
            break

    if not browser_bin_dir:
        fail("Could not find browser binary directory in @{}".format(repository_ctx.attr.browser))

    # Symlink .so files from each sysroot repo directly next to the browser binary
    for sysroot_repo in repository_ctx.attr.sysroot_repos:
        lib_root = repository_ctx.path(
            Label("@{}//:BUILD.bazel".format(sysroot_repo)),
        ).dirname
        _symlink_shared_libs(repository_ctx, lib_root, browser_bin_dir)

    # Generate BUILD and WORKSPACE files
    repository_ctx.file("BUILD.bazel", _BUILD_TEMPLATE.format(
        name = repository_ctx.original_name,
        browser_label = "@{}".format(repository_ctx.attr.browser),
    ))
    repository_ctx.file("WORKSPACE.bazel", """workspace(name = "{}")""".format(
        repository_ctx.original_name,
    ))

playwright_chromium_with_sysroot = repository_rule(
    doc = """\
Creates a repository containing the Chromium headless-shell browser files with
system shared libraries symlinked next to the binary. A select()-based alias
chooses between this enhanced filegroup (flag ON) and the raw browser archive
(flag OFF).
""",
    implementation = _playwright_chromium_with_sysroot_impl,
    attrs = {
        "browser": attr.string(
            doc = "Repository name of the raw Chromium headless-shell browser archive.",
            mandatory = True,
        ),
        "sysroot_repos": attr.string_list(
            doc = "Repository names of debian_archive repos providing system shared libraries.",
            default = [],
        ),
    },
)
