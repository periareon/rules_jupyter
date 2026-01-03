"""Rules for Playwright toolchain and actions"""

def playwright_install_action(ctx, output_dir, playwright_version, browsers):
    """Creates a PlaywrightInstall action.

    Args:
        ctx: Rule context (must have ctx.executable._installer)
        output_dir: Output directory for installed browsers
        playwright_version: Playwright version string
        browsers: Dict mapping browser type to (filegroup_label, version_string) tuple

    Returns:
        The output directory artifact
    """

    # Collect all browser files for inputs
    all_inputs = []
    manifest_files = []

    # Create a separate manifest file for each browser
    for browser_type, (filegroup, version) in browsers.items():
        if filegroup and version:
            # Get files from the filegroup
            browser_files = depset(transitive = [
                filegroup[DefaultInfo].files,
                filegroup[DefaultInfo].default_runfiles.files,
            ])
            all_inputs.append(browser_files)

            # Collect file paths for the manifest
            file_paths = [f.path for f in browser_files.to_list()]

            # Create manifest content for this browser
            manifest_content = {
                "browser_type": browser_type,
                "files": file_paths,
                "version": version,
            }

            # Write manifest file for this browser
            manifest_file = ctx.actions.declare_file("{}_browser_{}.json".format(ctx.label.name, browser_type))
            ctx.actions.write(
                output = manifest_file,
                content = json.encode_indent(manifest_content, indent = " " * 4),
            )
            manifest_files.append(manifest_file)

    # Build arguments for the installer script
    args = ctx.actions.args()
    args.add("--playwright-version", playwright_version)
    args.add("--output-dir", output_dir.path)

    # Add each manifest file with --manifest flag
    for manifest_file in manifest_files:
        args.add("--manifest", manifest_file)

    # Run the installer action using the executable directly
    ctx.actions.run(
        mnemonic = "PlaywrightInstall",
        progress_message = "PlaywrightInstall %{label}",
        executable = ctx.executable._installer,
        arguments = [args],
        inputs = depset(manifest_files, transitive = all_inputs),
        outputs = [output_dir],
        env = ctx.configuration.default_shell_env,
    )

    return output_dir

def _playwright_toolchain_impl(ctx):
    """Implementation of the playwright_toolchain rule."""

    # Validate that if a browser is provided, its version is also provided
    if ctx.attr.chromium and not ctx.attr.chromium_version:
        fail("chromium_version is required when chromium is provided")
    if ctx.attr.chromium_headless_shell and not ctx.attr.chromium_headless_shell_version:
        fail("chromium_headless_shell_version is required when chromium_headless_shell is provided")
    if ctx.attr.ffmpeg and not ctx.attr.ffmpeg_version:
        fail("ffmpeg_version is required when ffmpeg is provided")
    if ctx.attr.firefox and not ctx.attr.firefox_version:
        fail("firefox_version is required when firefox is provided")
    if ctx.attr.webkit and not ctx.attr.webkit_version:
        fail("webkit_version is required when webkit is provided")

    # Create PlaywrightInstall target to generate browsers directory
    browsers_dir = ctx.actions.declare_directory(ctx.attr.name + "_browsers")

    # Build browsers dict: browser_type -> (filegroup, version)
    # Only include browsers that are provided
    browsers = {}
    if ctx.attr.chromium and ctx.attr.chromium_version:
        browsers["chromium"] = (ctx.attr.chromium, ctx.attr.chromium_version)
    if ctx.attr.chromium_headless_shell and ctx.attr.chromium_headless_shell_version:
        browsers["chromium-headless-shell"] = (ctx.attr.chromium_headless_shell, ctx.attr.chromium_headless_shell_version)
    if ctx.attr.ffmpeg and ctx.attr.ffmpeg_version:
        browsers["ffmpeg"] = (ctx.attr.ffmpeg, ctx.attr.ffmpeg_version)
    if ctx.attr.firefox and ctx.attr.firefox_version:
        browsers["firefox"] = (ctx.attr.firefox, ctx.attr.firefox_version)
    if ctx.attr.webkit and ctx.attr.webkit_version:
        browsers["webkit"] = (ctx.attr.webkit, ctx.attr.webkit_version)

    playwright_install_action(
        ctx = ctx,
        output_dir = browsers_dir,
        playwright_version = ctx.attr.version,
        browsers = browsers,
    )

    all_files = []

    # Collect browser targets and files (browsers are optional)
    if ctx.attr.chromium:
        all_files.append(ctx.attr.chromium[DefaultInfo].files)
        if ctx.attr.chromium[DefaultInfo].default_runfiles:
            all_files.append(ctx.attr.chromium[DefaultInfo].default_runfiles.files)

    if ctx.attr.chromium_headless_shell:
        all_files.append(ctx.attr.chromium_headless_shell[DefaultInfo].files)
        if ctx.attr.chromium_headless_shell[DefaultInfo].default_runfiles:
            all_files.append(ctx.attr.chromium_headless_shell[DefaultInfo].default_runfiles.files)

    if ctx.attr.firefox:
        all_files.append(ctx.attr.firefox[DefaultInfo].files)
        if ctx.attr.firefox[DefaultInfo].default_runfiles:
            all_files.append(ctx.attr.firefox[DefaultInfo].default_runfiles.files)

    if ctx.attr.webkit:
        all_files.append(ctx.attr.webkit[DefaultInfo].files)
        if ctx.attr.webkit[DefaultInfo].default_runfiles:
            all_files.append(ctx.attr.webkit[DefaultInfo].default_runfiles.files)

    if ctx.attr.ffmpeg:
        all_files.append(ctx.attr.ffmpeg[DefaultInfo].files)
        if ctx.attr.ffmpeg[DefaultInfo].default_runfiles:
            all_files.append(ctx.attr.ffmpeg[DefaultInfo].default_runfiles.files)

    # Include the browsers directory
    all_files.append(depset([browsers_dir]))

    return [
        platform_common.ToolchainInfo(
            version = ctx.attr.version,
            chromium = ctx.attr.chromium,
            chromium_version = ctx.attr.chromium_version,
            chromium_headless_shell = ctx.attr.chromium_headless_shell,
            chromium_headless_shell_version = ctx.attr.chromium_headless_shell_version,
            firefox = ctx.attr.firefox,
            firefox_version = ctx.attr.firefox_version,
            webkit = ctx.attr.webkit,
            webkit_version = ctx.attr.webkit_version,
            ffmpeg = ctx.attr.ffmpeg,
            ffmpeg_version = ctx.attr.ffmpeg_version,
            browsers_dir = browsers_dir,
            all_files = depset(transitive = all_files),
        ),
    ]

playwright_toolchain = rule(
    doc = "Playwright toolchain providing browser archives",
    implementation = _playwright_toolchain_impl,
    attrs = {
        "chromium": attr.label(
            doc = "Chromium browser filegroup",
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
        "chromium_headless_shell": attr.label(
            doc = "Chromium headless-shell browser filegroup",
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
        "chromium_headless_shell_version": attr.string(
            doc = "Chromium headless-shell browser revision",
        ),
        "chromium_version": attr.string(
            doc = "Chromium browser revision",
        ),
        "ffmpeg": attr.label(
            doc = "FFmpeg filegroup",
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
        "ffmpeg_version": attr.string(
            doc = "FFmpeg revision",
        ),
        "firefox": attr.label(
            doc = "Firefox browser filegroup",
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
        "firefox_version": attr.string(
            doc = "Firefox browser revision",
        ),
        "version": attr.string(
            doc = "Playwright version",
            mandatory = True,
        ),
        "webkit": attr.label(
            doc = "WebKit browser filegroup",
            allow_single_file = True,
            executable = True,
            cfg = "exec",
        ),
        "webkit_version": attr.string(
            doc = "WebKit browser revision",
        ),
        "_installer": attr.label(
            cfg = "exec",
            executable = True,
            default = Label("//tools/process_wrappers:playwright_install"),
        ),
    },
)

def _current_playwright_toolchain_browsers_dir_impl(ctx):
    toolchain = ctx.toolchains[str(Label("//jupyter/playwright:toolchain_type"))]

    return [DefaultInfo(
        files = depset([toolchain.browsers_dir]),
    )]

current_playwright_toolchain_browsers_dir = rule(
    doc = "Provides access to the browsers directory from the current Playwright toolchain. The browsers directory contains all installed browser binaries in a structure compatible with PLAYWRIGHT_BROWSERS_PATH.",
    implementation = _current_playwright_toolchain_browsers_dir_impl,
    toolchains = [str(Label("//jupyter/playwright:toolchain_type"))],
)
