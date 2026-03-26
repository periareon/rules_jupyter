"""Rules for downloading and extracing `.deb` archives for use in Bazel"""

load(
    "@bazel_tools//tools/build_defs/repo:utils.bzl",
    "patch",
    "read_netrc",
    "read_user_netrc",
    "update_attrs",
    "use_netrc",
    "workspace_and_buildfile",
)

def _get_auth(repository_ctx, urls):
    """Given the list of URLs obtain the correct auth dict."""
    if repository_ctx.attr.netrc:
        netrc = read_netrc(repository_ctx, repository_ctx.attr.netrc)
    else:
        netrc = read_user_netrc(repository_ctx)
    return use_netrc(netrc, urls, repository_ctx.attr.auth_patterns)

def download_and_extract(
        *,
        repository_ctx,
        urls,
        sha256,
        add_prefix = "",
        strip_prefix = "",
        auth = {},
        canonical_id = "",
        integrity = ""):
    """Download and extract debian archives

    Args:
        repository_ctx (repository_ctx): The repository rule's context object
        urls (list): A list of URLs to download the archive from.
        sha256 (str): The sha256 value of the archive.
        add_prefix (str, optional): A prefix to add to the extracted content.
        strip_prefix (str, optional): A prefix to strip form the extracted content.
        auth (dict, optional): See `debian_archive.auth`
        canonical_id (str, optional): See `debian_archive.canonical_id`
        integrity (str, optional): See `debian_archive.integrity`

    Returns:
        dict: The result of repository_ctx.download_and_extract
    """
    temp_path = repository_ctx.path(".debian_archives/")

    download_info = repository_ctx.download_and_extract(
        urls,
        output = temp_path,
        sha256 = sha256,
        type = "deb",
        canonical_id = canonical_id,
        auth = auth,
        integrity = integrity,
    )

    data_path = None
    for file_name in ["data.tar.gz", "data.tar.xz", "data.tar.zst"]:
        file_path = repository_ctx.path("{}/{}".format(temp_path, file_name))
        if file_path.exists:
            data_path = file_path
            break

    if not data_path:
        fail("No data file was found in the following artifact: {} -- {}".format(
            repository_ctx.name,
            urls,
        ))

    # Extract the data
    repository_ctx.extract(
        archive = data_path,
        output = add_prefix,
        stripPrefix = strip_prefix,
    )

    # Cleanup the intermediate download directory
    repository_ctx.delete(temp_path)

    return download_info

def _debian_archive_impl(repository_ctx):
    if repository_ctx.attr.build_file and repository_ctx.attr.build_file_content:
        fail("Only one of build_file and build_file_content can be provided.")

    if repository_ctx.attr.workspace_file and repository_ctx.attr.workspace_file_content:
        fail("Only one of workspace_file and workspace_file_content can be provided.")

    all_urls = repository_ctx.attr.urls
    auth = _get_auth(repository_ctx, all_urls)

    download_info = download_and_extract(
        repository_ctx = repository_ctx,
        urls = all_urls,
        sha256 = repository_ctx.attr.sha256,
        auth = auth,
        add_prefix = repository_ctx.attr.add_prefix,
        strip_prefix = repository_ctx.attr.strip_prefix,
        canonical_id = repository_ctx.attr.canonical_id,
        integrity = repository_ctx.attr.integrity,
    )

    workspace_and_buildfile(repository_ctx)
    patch(repository_ctx)

    override = {}
    if download_info.integrity:
        override = {"integrity": download_info.integrity}
    else:
        override = {"sha256": download_info.sha256}

    return update_attrs(
        orig = repository_ctx.attr,
        keys = _DEBIAN_ARCHIVE_ATTRS.keys(),
        override = override,
    )

_DEBIAN_ARCHIVE_ATTRS = {
    "add_prefix": attr.string(
        default = "",
        doc = """Destination directory relative to the repository directory.
The archive will be unpacked into this directory, after applying `strip_prefix`
(if any) to the file paths within the archive. For example, file
`foo-1.2.3/src/foo.h` will be unpacked to `bar/src/foo.h` if `add_prefix = "bar"`
and `strip_prefix = "foo-1.2.3"`.""",
    ),
    "auth_patterns": attr.string_dict(
        doc = """An optional dict mapping host names to custom authorization patterns.
If a URL's host name is present in this dict the value will be used as a pattern when
generating the authorization header for the http request. This enables the use of custom
authorization schemes used in a lot of common cloud storage providers.
The pattern currently supports 2 tokens: <code>&lt;login&gt;</code> and
<code>&lt;password&gt;</code>, which are replaced with their equivalent value
in the netrc file for the same host name. After formatting, the result is set
as the value for the <code>Authorization</code> field of the HTTP request.
Example attribute and netrc for a http download to an oauth2 enabled API using a bearer token:
<pre>
auth_patterns = {
    "storage.cloudprovider.com": "Bearer &lt;password&gt;"
}
</pre>
netrc:
<pre>
machine storage.cloudprovider.com
        password RANDOM-TOKEN
</pre>
The final HTTP request would have the following header:
<pre>
Authorization: Bearer RANDOM-TOKEN
</pre>
""",
    ),
    "build_file": attr.label(
        allow_single_file = True,
        doc =
            "The file to use as the BUILD file for this repository." +
            "This attribute is an absolute label (use '@//' for the main " +
            "repo). The file does not need to be named BUILD, but can " +
            "be (something like BUILD.new-repo-name may work well for " +
            "distinguishing it from the repository's actual BUILD files. " +
            "Either build_file or build_file_content can be specified, but " +
            "not both.",
    ),
    "build_file_content": attr.string(
        doc =
            "The content for the BUILD file for this repository. " +
            "Either build_file or build_file_content can be specified, but " +
            "not both.",
    ),
    "canonical_id": attr.string(
        doc = """A canonical id of the archive downloaded.
If specified and non-empty, bazel will not take the archive from cache,
unless it was added to the cache by a request with the same canonical id.
""",
    ),
    "integrity": attr.string(
        doc = """Expected checksum in Subresource Integrity format of the file downloaded.
This must match the checksum of the file downloaded. _It is a security risk
to omit the checksum as remote files can change._ At best omitting this
field will make your build non-hermetic. It is optional to make development
easier but either this attribute or `sha256` should be set before shipping.""",
    ),
    "netrc": attr.string(
        doc = "Location of the .netrc file to use for authentication",
    ),
    "patch_args": attr.string_list(
        default = ["-p0"],
        doc =
            "The arguments given to the patch tool. Defaults to -p0, " +
            "however -p1 will usually be needed for patches generated by " +
            "git. If multiple -p arguments are specified, the last one will take effect." +
            "If arguments other than -p are specified, Bazel will fall back to use patch " +
            "command line tool instead of the Bazel-native patch implementation. When falling " +
            "back to patch command line tool and patch_tool attribute is not specified, " +
            "`patch` will be used. This only affects patch files in the `patches` attribute.",
    ),
    "patch_cmds": attr.string_list(
        default = [],
        doc = "Sequence of Bash commands to be applied on Linux/Macos after patches are applied.",
    ),
    "patch_cmds_win": attr.string_list(
        default = [],
        doc = "Sequence of Powershell commands to be applied on Windows after patches are " +
              "applied. If this attribute is not set, patch_cmds will be executed on Windows, " +
              "which requires Bash binary to exist.",
    ),
    "patch_tool": attr.string(
        default = "",
        doc = "The patch(1) utility to use. If this is specified, Bazel will use the specifed " +
              "patch tool instead of the Bazel-native patch implementation.",
    ),
    "patches": attr.label_list(
        default = [],
        doc =
            "A list of files that are to be applied as patches after " +
            "extracting the archive. By default, it uses the Bazel-native patch implementation " +
            "which doesn't support fuzz match and binary patch, but Bazel will fall back to use " +
            "patch command line tool if `patch_tool` attribute is specified or there are " +
            "arguments other than `-p` in `patch_args` attribute.",
    ),
    "sha256": attr.string(
        doc = """The expected SHA-256 of the file downloaded.
This must match the SHA-256 of the file downloaded. _It is a security risk
to omit the SHA-256 as remote files can change._ At best omitting this
field will make your build non-hermetic. It is optional to make development
easier but either this attribute or `integrity` should be set before shipping.""",
    ),
    "strip_prefix": attr.string(
        doc = "A directory prefix to strip from the extracted files.",
    ),
    "type": attr.string(
        doc = """The archive type of the downloaded file.
By default, the archive type is determined from the file extension of the
URL.""",
        values = [
            "deb",
        ],
    ),
    "urls": attr.string_list(
        doc = """A list of URLs to a file that will be made available to Bazel.
Each entry must be a file, http or https URL. Redirections are followed.
Authentication is not supported.
URLs are tried in order until one succeeds, so you should list local mirrors first.
If all downloads fail, the rule will fail.""",
        mandatory = True,
    ),
    "workspace_file": attr.label(
        doc =
            "The file to use as the `WORKSPACE` file for this repository. " +
            "Either `workspace_file` or `workspace_file_content` can be " +
            "specified, or neither, but not both.",
    ),
    "workspace_file_content": attr.string(
        doc =
            "The content for the WORKSPACE file for this repository. " +
            "Either `workspace_file` or `workspace_file_content` can be " +
            "specified, or neither, but not both.",
    ),
}

debian_archive = repository_rule(
    implementation = _debian_archive_impl,
    doc = """\
Downloads a Bazel repository as a debian archive file, decompresses it,
and makes its targets available for binding.
""",
    attrs = _DEBIAN_ARCHIVE_ATTRS,
)
