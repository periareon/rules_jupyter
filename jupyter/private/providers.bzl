"""Providers"""

JupyterNotebookInfo = provider(
    doc = "Provider that carries information about a Jupyter notebook.",
    fields = {
        "data": "Depset[file]: Additional data files required by the notebook (e.g., input data files, images).",
        "kernel": "str: The name of the Jupyter kernel to use for executing the notebook (e.g., 'python3', 'rust').",
        "notebook": "File: The notebook file (.ipynb format).",
    },
)
