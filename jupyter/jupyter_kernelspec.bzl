"""# jupyter_kernelspec"""

load(
    "//jupyter/private:kernelspec.bzl",
    _jupyter_kernelspec = "jupyter_kernelspec",
)
load(
    "//jupyter/private:providers.bzl",
    _JupyterKernelspecInfo = "JupyterKernelspecInfo",
)

jupyter_kernelspec = _jupyter_kernelspec
JupyterKernelspecInfo = _JupyterKernelspecInfo
