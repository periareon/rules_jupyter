# %% [markdown]
# # Custom kernel notebook
#
# This notebook is executed by the `python_custom` kernel registered on the
# development `jupyter_toolchain` via `jupyter_kernelspec`.

# %%
import os
import sys

assert (
    os.environ.get("RULES_JUPYTER_CUSTOM_KERNEL") == "1"
), "Notebook was not executed by the custom kernel"

EXPECTED = ["--input=test_input", "--flag"]
assert sys.argv[1:] == EXPECTED, f"Expected {EXPECTED}, got {sys.argv[1:]}"

print("Executed by the custom kernel with", sys.argv[1:])
