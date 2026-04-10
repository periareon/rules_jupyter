# %% [markdown]
# # Test Notebook without Command-Line Arguments
#
# This notebook verifies that when no `args` attribute is set,
# `sys.argv[1:]` is empty.

# %%
import sys

assert sys.argv[1:] == [], f"Expected sys.argv[1:] == [], got {sys.argv[1:]}"

print("No-args assertion passed!")
