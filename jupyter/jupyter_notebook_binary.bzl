"""# jupyter_notebook_binary"""

load(
    "//jupyter/private:jupyter.bzl",
    _jupyter_notebook_binary = "jupyter_notebook_binary",
)

jupyter_notebook_binary = _jupyter_notebook_binary
