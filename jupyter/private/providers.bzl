"""Providers"""

JupyterNotebookInfo = provider(
    doc = "Provider that carries information about a Jupyter notebook.",
    fields = {
        "data": "Depset[file]: Additional data files required by the notebook (e.g., input data files, images).",
        "kernel": "str: The name of the Jupyter kernel to use for executing the notebook (e.g., 'python3', 'rust').",
        "notebook": "File: The notebook file (.ipynb format).",
    },
)

JupyterKernelInfo = provider(
    doc = "Provider that carries information about a Jupyter kernel for use in sandboxed execution.",
    fields = {
        "binary": "File: The kernel binary executable (e.g., evcxr_jupyter).",
        "data": "Depset[File]: Additional data files required by the kernel.",
        "kernel_json": "File: A generated kernel.json template with __KERNEL_BINARY__ as a placeholder for the binary path.",
        "kernel_name": "str: The kernelspec directory name used for Jupyter kernel discovery (e.g., 'rust').",
    },
)
