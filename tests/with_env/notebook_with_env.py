# %% [markdown]
# # Test Notebook with Environment Variables
#
# This notebook demonstrates that environment variables can be set in notebooks
# via the `env` attribute in `jupyter_report` and `jupyter_notebook_test` rules.
#

# %%
import os

# Read environment variables set by the build rule
test_env_var = os.environ.get("TEST_ENV_VAR", "")
test_number = os.environ.get("TEST_NUMBER", "")
test_flag = os.environ.get("TEST_FLAG", "")

print("Environment variables:")
print(f"TEST_ENV_VAR: {test_env_var}")
print(f"TEST_NUMBER: {test_number}")
print(f"TEST_FLAG: {test_flag}")

# %%
# Verify expected values
assert (
    test_env_var == "test_value"
), f"Expected TEST_ENV_VAR='test_value', got '{test_env_var}'"
assert test_number == "42", f"Expected TEST_NUMBER='42', got '{test_number}'"
assert test_flag == "true", f"Expected TEST_FLAG='true', got '{test_flag}'"

print("\nAll environment variable assertions passed!")

# %%
# Show all environment variables (for debugging)
print("\nAll environment variables containing 'TEST':")
for key, value in sorted(os.environ.items()):
    if "TEST" in key.upper():
        print(f"{key}={value}")
