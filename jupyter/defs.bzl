"""# Jupyter rules"""

load(
    ":jupyter_notebook.bzl",
    _jupyter_notebook = "jupyter_notebook",
)
load(
    ":jupyter_notebook_test.bzl",
    _jupyter_notebook_test = "jupyter_notebook_test",
)
load(
    ":jupyter_report.bzl",
    _jupyter_report = "jupyter_report",
)
load(
    ":jupyter_toolchain.bzl",
    _jupyter_toolchain = "jupyter_toolchain",
)

jupyter_notebook = _jupyter_notebook
jupyter_notebook_test = _jupyter_notebook_test
jupyter_toolchain = _jupyter_toolchain
jupyter_report = _jupyter_report
