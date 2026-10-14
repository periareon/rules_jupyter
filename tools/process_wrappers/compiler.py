"""The `JupyterCompiler` action runner.

Converts a Python file (.py) to a Jupyter notebook (.ipynb) without executing it.
Uses jupytext to support various formats including percent format (`# %%` markers).
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Optional, cast

import jupytext  # type: ignore[import-untyped]
import nbformat


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--notebook",
        type=Path,
        required=True,
        help="The Python file (.py) to convert to a notebook.",
    )
    parser.add_argument(
        "--out_notebook",
        type=Path,
        required=True,
        help="The output path for the notebook (.ipynb).",
    )
    parser.add_argument(
        "--kernel",
        type=str,
        help="The kernel name to set in the notebook metadata.",
    )
    parser.add_argument(
        "--kernel_display_name",
        type=str,
        help="The kernel display name to set in the notebook metadata.",
    )
    parser.add_argument(
        "--kernel_language",
        type=str,
        help="The kernel language to set in the notebook metadata.",
    )

    return parser.parse_args()


def convert_py_to_notebook(
    py_path: Path,
    kernel_name: Optional[str] = None,
    kernel_display_name: Optional[str] = None,
    kernel_language: Optional[str] = None,
) -> nbformat.NotebookNode:
    """Convert a script to a Jupyter notebook using jupytext.

    Supports various formats including:
    - Percent format (`# %%` cell markers)
    - Light format (implicit cells)
    - Sphinx-gallery format

    Any language jupytext understands (`.py`, `.jl`, `.rs`, ...) is accepted.

    Args:
        py_path: Path to the script.
        kernel_name: The kernel name to set in notebook metadata. Defaults to
            `python3` when the script carries no kernelspec metadata.
        kernel_display_name: The kernel display name to set in notebook metadata.
        kernel_language: The kernel language to set in notebook metadata.

    Returns:
        A NotebookNode object.
    """
    notebook = jupytext.read(py_path)

    # Cast to NotebookNode since jupytext.read returns Any
    notebook_node = cast(nbformat.NotebookNode, notebook)

    # Ensure kernel metadata is set
    if "kernelspec" not in notebook_node.metadata:
        name = kernel_name or "python3"
        if kernel_language is None:
            # jupytext records the script language when no kernel is known.
            kernel_language = notebook_node.metadata.get("jupytext", {}).get(
                "main_language", "python"
            )
        if kernel_display_name is None:
            kernel_display_name = "Python 3" if name == "python3" else name
        notebook_node.metadata.kernelspec = {
            "display_name": kernel_display_name,
            "language": kernel_language,
            "name": name,
        }
    elif kernel_name:
        # Override with specified kernel if explicitly provided
        notebook_node.metadata.kernelspec["name"] = kernel_name
        if kernel_display_name:
            notebook_node.metadata.kernelspec["display_name"] = kernel_display_name
        if kernel_language:
            notebook_node.metadata.kernelspec["language"] = kernel_language

    # Normalize the notebook to add missing cell IDs (required in nbformat 4.5+)
    # This prevents MissingIDFieldWarning when nbformat validates the notebook
    try:
        nbformat.normalize(notebook_node)  # type: ignore[attr-defined]
    except AttributeError:
        # normalize() was added in nbformat 5.1.4, fall back gracefully if not available
        pass

    return notebook_node


def save_notebook(notebook: nbformat.NotebookNode, output_path: Path) -> None:
    """Save a notebook to disk.

    Args:
        notebook: The notebook to save.
        output_path: Path to write the notebook.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(notebook, f)  # type: ignore[no-untyped-call]


def main() -> None:
    """The main entrypoint."""
    if "RULES_JUPYTER_DEBUG" in os.environ:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            level=logging.DEBUG,
        )

    args = parse_args()

    # Validate input file exists
    if not args.notebook.exists():
        logging.error("Input file not found: %s", args.notebook)
        raise FileNotFoundError(f"Input file not found: {args.notebook}")

    logging.debug("Converting %s to notebook", args.notebook)

    # Convert Python file to notebook
    notebook = convert_py_to_notebook(
        args.notebook,
        kernel_name=args.kernel,
        kernel_display_name=args.kernel_display_name,
        kernel_language=args.kernel_language,
    )

    logging.debug("Created notebook with %d cells", len(notebook.cells))

    # Save the notebook
    save_notebook(notebook, args.out_notebook)

    logging.debug("Saved notebook to %s", args.out_notebook)


if __name__ == "__main__":
    main()
