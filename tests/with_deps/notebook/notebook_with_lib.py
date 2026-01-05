# %% [markdown]
# # Test Notebook with Library Dependency
#
# This notebook demonstrates that a notebook can import from a library
# in a separate subdirectory using import paths relative from the root of the repo.

# %%
# Import from the library using repo root-relative import path
from tests.with_deps.lib import add, greet, multiply

print("Successfully imported from library!")
print(f"greet('World'): {greet('World')}")
print(f"add(5, 3): {add(5, 3)}")
print(f"multiply(4, 7): {multiply(4, 7)}")

# %%
# Verify the imports work correctly
assert greet("Test") == "Hello, Test!", "greet function failed"
assert add(10, 20) == 30, "add function failed"
assert multiply(6, 7) == 42, "multiply function failed"

print("\nAll library function tests passed!")

# %%
# Test importing the module directly
from tests.with_deps.lib.utils import greet as greet_utils

print(f"Direct import from utils: {greet_utils('Direct Import')}")
