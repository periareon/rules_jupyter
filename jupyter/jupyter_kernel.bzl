"""# jupyter_kernel"""

load(
    "//jupyter/private:kernel.bzl",
    _jupyter_kernel = "jupyter_kernel",
)

jupyter_kernel = _jupyter_kernel
