"""# jupyter_notebook_test"""

load(
    "//jupyter/private:jupyter.bzl",
    _jupyter_notebook_test = "jupyter_notebook_test",
)

jupyter_notebook_test = _jupyter_notebook_test
