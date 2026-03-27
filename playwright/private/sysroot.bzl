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

SYSROOT_SO_FILES = {sysroot_so_files}

filegroup(
    name = "_without_sysroot",
    srcs = BROWSER_SRCS,
    data = glob(
        include = ["{{}}*/**".format(BROWSER_DIR)],
        exclude = BROWSER_SRCS + SYSROOT_SO_FILES,
    ),
    visibility = ["//visibility:public"],
)

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
        "//conditions:default": ":_without_sysroot",
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

def _symlink_shared_libs(repository_ctx, deb_root, dest_dir):
    """Scan known Debian lib directories and symlink .so files into `dest_dir`.

    Returns:
        List of relative paths (from repo root) for each symlinked file.
    """
    symlinked = []
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
                    repository_ctx.symlink(entry, dest)
                    symlinked.append("{}/{}".format(dest_dir.basename, entry.basename))
    return symlinked

def _is_browser_dir(basename):
    """Returns True if the directory name matches a Chromium browser directory."""
    return basename.startswith("chrome-headless-shell-linux") or basename.startswith("chrome-linux")

def _symlink_dir_contents(repository_ctx, source_dir, dest_dir_name):
    """Symlink the individual files inside a directory rather than the directory itself.

    This creates a real directory in the repo so additional files (e.g. sysroot
    .so files) can be added alongside the originals.
    """
    for entry in source_dir.readdir():
        dest = dest_dir_name + "/" + entry.basename
        repository_ctx.symlink(entry, dest)

def _playwright_chromium_with_sysroot_impl(repository_ctx):
    browser_root = repository_ctx.path(repository_ctx.attr.browser).dirname

    browser_bin_dir = None
    for entry in browser_root.readdir():
        if entry.basename in ["BUILD.bazel", "WORKSPACE.bazel", "WORKSPACE", "MODULE.bazel"]:
            continue
        if _is_browser_dir(entry.basename):
            _symlink_dir_contents(repository_ctx, entry, entry.basename)
            browser_bin_dir = repository_ctx.path(entry.basename)
        else:
            repository_ctx.symlink(entry, entry.basename)

    if not browser_bin_dir:
        fail("Could not find browser binary directory in browser archive")

    # Symlink .so files from each sysroot repo directly next to the browser binary
    sysroot_so_files = []
    for sysroot_label in repository_ctx.attr.sysroot_repos:
        deb_root = repository_ctx.path(sysroot_label).dirname
        sysroot_so_files.extend(
            _symlink_shared_libs(repository_ctx, deb_root, browser_bin_dir),
        )

    repository_ctx.file("BUILD.bazel", _BUILD_TEMPLATE.format(
        name = repository_ctx.original_name,
        sysroot_so_files = json.encode(sysroot_so_files),
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
        "browser": attr.label(
            doc = "Label to a file in the raw Chromium headless-shell browser archive (used for path resolution).",
            mandatory = True,
        ),
        "sysroot_repos": attr.label_list(
            doc = "Labels to files in debian_archive repos (used for path resolution).",
            default = [],
        ),
    },
)
