"""Providers"""

JupyterNotebookInfo = provider(
    doc = "Provider that carries information about a Jupyter notebook.",
    fields = {
        "data": "Depset[file]: Additional data files required by the notebook (e.g., input data files, images).",
        "kernel": "str: The name of the Jupyter kernel to use for executing the notebook (e.g., 'python3', 'rust').",
        "notebook": "File: The notebook file (.ipynb format).",
        "src": "File: The original source file (.py or .ipynb) provided to the jupyter_notebook rule.",
    },
)

JupyterKernelspecInfo = provider(
    doc = "Provider describing a Jupyter kernel that notebooks can be executed with.",
    fields = {
        "args_template": "File: A code cell template used to forward notebook `args` to the kernel, or `None` when the kernel does not support args.",
        "argv": "List[str]: The kernel launch command. File references are rlocationpaths which are resolved at runtime.",
        "display_name": "str: The human readable kernel name.",
        "env": "Dict[str, str]: Environment variables set for the kernel process.",
        "files": "Depset[File]: All files required by the kernel at runtime.",
        "interrupt_mode": "str: The Jupyter interrupt mode (`signal` or `message`) or an empty string for the Jupyter default.",
        "kernel_name": "str: The kernel name used by `jupyter_notebook.kernel` and notebook metadata.",
        "language": "str: The language of the kernel (e.g. `python`, `julia`, `rust`).",
        "path_tools": "List[str]: rlocationpaths of the `path_tools` executables. The directory of each resolved file is prepended to `PATH` for the kernel process.",
        "rlocations": "Dict[str, File]: Every file referenced by `argv`, `env` or `path_tools`, keyed by rlocationpath.",
        "runfiles": "runfiles: The runfiles of the kernel.",
        "spec": "File: A json file describing the kernelspec, consumed by the rules_jupyter process wrappers.",
        "tools": "List[FilesToRunProvider]: Executables used by the kernel. Passed as tools to build actions so their runfiles are available.",
        "transport": "str: The ZeroMQ transport (`ipc` or `tcp`) used to talk to the kernel, or an empty string for the platform default.",
    },
)
