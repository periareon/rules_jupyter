# %% [markdown]
# # Test Notebook with Data Files
#
# This notebook demonstrates that data files can be accessed in notebooks
# via the `data` attribute in `jupyter_notebook`, `jupyter_report`, and `jupyter_notebook_test` rules.

# %%
import json
from pathlib import Path

# Data files are available in the runfiles directory
# We can access them using their relative paths from the notebook location
data_file = Path("jupyter/private/tests/with_data/data.txt")
config_file = Path("jupyter/private/tests/with_data/config.json")

print("Reading data files...")

# %%
# Read the text data file
if data_file.exists():
    with open(data_file, "r", encoding="utf-8") as f:
        data_content = f.read()
    print("Data file contents:")
    print(data_content)
    print(f"\nNumber of lines: {len(data_content.splitlines())}")
else:
    print(f"ERROR: {data_file} not found!")
    print(f"Current directory: {Path.cwd()}")
    print(f"Files in current directory: {list(Path('.').iterdir())}")

# %%
# Read the JSON config file
if config_file.exists():
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    print("Config file contents:")
    print(json.dumps(config, indent=2))
    print(f"\nConfig name: {config['name']}")
    print(f"Config version: {config['version']}")
    print(f"Value1: {config['settings']['value1']}")
    print(f"Value2: {config['settings']['value2']}")
    print(f"Enabled: {config['settings']['enabled']}")
else:
    print(f"ERROR: {config_file} not found!")

# %%
# Verify we can process the data
assert data_file.exists(), f"Data file {data_file} should exist"
assert config_file.exists(), f"Config file {config_file} should exist"

# Process the data
lines = data_content.splitlines()
assert len(lines) >= 4, "Data file should have at least 4 lines"
assert config["settings"]["value1"] == 42, "Config value1 should be 42"

print("\nAll data file assertions passed!")
