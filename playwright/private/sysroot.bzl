"""Rules for bundling Chromium headless-shell with system library dependencies.

Provides:
- `playwright_chromium_with_sysroot`: a build rule that overlays .so files from
  Debian packages into a browser directory.
- `chromium_headless_shell_selector`: a repository rule that generates a BUILD
  with a select()-based alias, choosing between the raw browser and the
  sysroot-enhanced variant based on the feature flag.
"""

def _playwright_chromium_with_sysroot_impl(ctx):
    output_dir = ctx.actions.declare_directory(ctx.attr.name + "_browser")

    browser_files = depset(transitive = [
        ctx.attr.browser[DefaultInfo].files,
        ctx.attr.browser[DefaultInfo].default_runfiles.files,
    ])

    sysroot_files = []
    for dep in ctx.attr.sysroot_libs:
        sysroot_files.append(dep[DefaultInfo].files)

    all_sysroot = depset(transitive = sysroot_files)

    browser_list = browser_files.to_list()
    sysroot_list = all_sysroot.to_list()

    manifest_content = {
        "browser_files": [f.path for f in browser_list],
        "output_dir": output_dir.path,
        "sysroot_files": [f.path for f in sysroot_list],
    }

    manifest_file = ctx.actions.declare_file(ctx.attr.name + "_sysroot_manifest.json")
    ctx.actions.write(
        output = manifest_file,
        content = json.encode_indent(manifest_content, indent = "  "),
    )

    ctx.actions.run(
        mnemonic = "ChromiumSysrootOverlay",
        progress_message = "Bundling Chromium with sysroot libraries %{label}",
        executable = ctx.executable._overlay_tool,
        arguments = [manifest_file.path],
        inputs = depset([manifest_file], transitive = [browser_files, all_sysroot]),
        outputs = [output_dir],
        env = ctx.configuration.default_shell_env,
    )

    return [DefaultInfo(
        files = depset([output_dir]),
    )]

playwright_chromium_with_sysroot = rule(
    doc = """\
Combines a Chromium headless-shell browser filegroup with system shared libraries
extracted from Debian packages. The .so files are placed in the same directory as
the browser binary so RPATH=$ORIGIN resolves them automatically.
""",
    implementation = _playwright_chromium_with_sysroot_impl,
    attrs = {
        "browser": attr.label(
            doc = "Label to the raw Chromium headless-shell browser filegroup.",
            mandatory = True,
        ),
        "sysroot_libs": attr.label_list(
            doc = "Labels to debian_archive filegroups providing system shared libraries.",
            allow_empty = True,
            default = [],
        ),
        "_overlay_tool": attr.label(
            cfg = "exec",
            executable = True,
            default = Label("//playwright/private:sysroot_overlay"),
        ),
    },
)

# -- Intermediate selector repository rule --

_SELECTOR_BUILD_TEMPLATE = """\
load("@rules_jupyter//playwright/private:sysroot.bzl", "playwright_chromium_with_sysroot")

playwright_chromium_with_sysroot(
    name = "with_sysroot",
    browser = "{browser_label}",
    sysroot_libs = {sysroot_libs},
)

alias(
    name = "{name}",
    actual = select({{
        "@rules_jupyter//playwright/settings:embedded_linux_chrome_sys_libs_enabled": ":with_sysroot",
        "//conditions:default": "{browser_label}",
    }}),
    visibility = ["//visibility:public"],
)
"""

def _chromium_headless_shell_selector_impl(repository_ctx):
    repository_ctx.file("BUILD.bazel", _SELECTOR_BUILD_TEMPLATE.format(
        name = repository_ctx.attr.original_name,
        browser_label = repository_ctx.attr.browser,
        sysroot_libs = json.encode(repository_ctx.attr.sysroot_libs),
    ))
    repository_ctx.file("WORKSPACE.bazel", """workspace(name = "{}")""".format(
        repository_ctx.attr.original_name,
    ))

chromium_headless_shell_selector = repository_rule(
    doc = """\
Generates a repository with a select()-based alias that resolves to either the
raw Chromium headless-shell browser or a sysroot-enhanced variant, based on the
experimental_embedded_linux_chrome_sys_libs flag.
""",
    implementation = _chromium_headless_shell_selector_impl,
    attrs = {
        "browser": attr.string(
            doc = "Label string for the raw Chromium headless-shell browser filegroup.",
            mandatory = True,
        ),
        "original_name": attr.string(
            doc = "The apparent repo name, used as the default target name in the BUILD file.",
            mandatory = True,
        ),
        "sysroot_libs": attr.string_list(
            doc = "Label strings for debian_archive filegroups providing system shared libraries.",
            default = [],
        ),
    },
)
