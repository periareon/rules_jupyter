# %% [markdown]
# # Test Notebook with Command-Line Arguments
#
# This notebook verifies that the `args` attribute on `jupyter_notebook_test`
# (and related rules) is forwarded to the notebook as `sys.argv[1:]`.

# %%
import sys

EXPECTED = ["--input=test_input", "--output=test_output", "--flag", "--count=42"]
assert (
    sys.argv[1:] == EXPECTED
), f"Expected sys.argv[1:] == {EXPECTED}, got {sys.argv[1:]}"

print("All argument assertions passed!")
