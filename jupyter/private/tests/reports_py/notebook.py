# %%

import math

# Calculate some values
pi = math.pi
e = math.e
print(f"Pi: {pi:.6f}")
print(f"e: {e:.6f}")

# %%

# Generate a simple table
data = [
    ("Circle", "2πr", "πr²"),
    ("Square", "4s", "s²"),
    ("Rectangle", "2(l+w)", "lw"),
]

print("Shape Formulas")
print("-" * 40)
print(f"{'Shape':<12} {'Perimeter':<12} {'Area':<12}")
print("-" * 40)
for shape, perimeter, area in data:
    print(f"{shape:<12} {perimeter:<12} {area:<12}")
