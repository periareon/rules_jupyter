# %% [markdown]
# # Simple Example Notebook
#
# This is a simple example showing how to use a `.py` notebook file
# with `rules_jupyter` to generate a markdown report.
#
# The notebook uses Jupytext format with `# %%` cell markers.

# %%
import math

# Calculate some mathematical constants
pi = math.pi
e = math.e

print(f"Pi: {pi:.6f}")
print(f"Euler's number (e): {e:.6f}")

# %%
# Generate a simple data table
shapes = [
    ("Circle", "2πr", "πr²"),
    ("Square", "4s", "s²"),
    ("Rectangle", "2(l+w)", "lw"),
]

print("Shape Formulas")
print("-" * 50)
print(f"{'Shape':<15} {'Perimeter':<20} {'Area':<15}")
print("-" * 50)
for shape, perimeter, area in shapes:
    print(f"{shape:<15} {perimeter:<20} {area:<15}")

# %% [markdown]
# ## Summary
#
# This notebook demonstrates:
# - Using a `.py` file as a Jupyter notebook (via Jupytext)
# - Executing Python code cells
# - Generating output that can be converted to markdown format
#
# The markdown report will include both the code cells and their outputs.

