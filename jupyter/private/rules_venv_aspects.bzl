"""Utilities for interacting with rules_venv aspects"""

# buildifier: disable=bzl-visibility
load("@rules_venv//python/private:target_srcs.bzl", _PySourcesInfo = "PySourcesInfo")

PySourcesInfo = _PySourcesInfo

def aspects_provider(ctx, src):
    """Construct a provider to power rules_venv aspects.

    Args:
        ctx (ctx): The current rule's context object.
        src (File): The notebook source file

    Returns:
        Provider: A unique provider for rules_venv
    """
    workspace_name = ctx.workspace_name
    if not workspace_name:
        workspace_name = "_main"

    if ctx.label.workspace_root.startswith("external"):
        return PySourcesInfo(
            imports = depset([workspace_name]),
            srcs = depset(),
        )

    return PySourcesInfo(
        imports = depset([workspace_name]),
        srcs = depset([src] if src.basename.endswith(".py") else []),
    )
