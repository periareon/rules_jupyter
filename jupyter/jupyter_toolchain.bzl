"""# jupyter_toolchain"""

load(
    "//jupyter/private:toolchain.bzl",
    _jupyter_toolchain = "jupyter_toolchain",
)

jupyter_toolchain = _jupyter_toolchain
