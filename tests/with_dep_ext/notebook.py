# %% [markdown]
# # Test Notebook with Dependencies (Jupytext format)
#
# This notebook demonstrates that dependencies (specifically pytest) propagate correctly
# into notebooks when using Jupytext format (.py files).

# %%
# Import pytest to verify it's available
import pytest

print(f"pytest version: {pytest.__version__}")
print("pytest is available!")

# %%


# Create a simple test function to demonstrate pytest works
def test_simple() -> None:
    assert 1 + 1 == 2


# Run the test
test_simple()
print("Test passed!")


# %%
# Use pytest's assert rewriting feature
# This demonstrates that pytest is properly loaded and available
def test_with_pytest() -> None:
    # pytest's assert rewriting makes better error messages
    x = 2
    y = 2
    assert x == y, "Values should be equal"
    print("pytest assertion rewriting works!")
