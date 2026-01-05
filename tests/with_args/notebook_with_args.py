# %% [markdown]
# # Test Notebook with Command-Line Arguments
#
# This notebook demonstrates that command-line arguments can be passed to notebooks
# via the `args` attribute in `jupyter_report` and `jupyter_notebook_test` rules.

# %%
# Parse command-line arguments
# Note: The first argument is the notebook path (injected by the execution framework)
# Additional arguments come after
import argparse

parser = argparse.ArgumentParser(
    description="Test notebook with command-line arguments"
)
parser.add_argument("--input", type=str, help="Input value")
parser.add_argument("--output", type=str, help="Output value")
parser.add_argument("--flag", action="store_true", help="Boolean flag")
parser.add_argument("--count", type=int, default=1, help="Count value")

# Parse args (skip the first element which is the notebook path)
args = parser.parse_args()
print("Parsed arguments:")
print(f"  input: {args.input}")
print(f"  output: {args.output}")
print(f"  flag: {args.flag}")
print(f"  count: {args.count}")

# %%
# Use the parsed arguments
result = f"Processed: input={args.input}, output={args.output}, flag={args.flag}, count={args.count}"
print(result)

# Assert that we got expected values (for testing)
assert args.input == "test_input", f"Expected input='test_input', got '{args.input}'"
assert (
    args.output == "test_output"
), f"Expected output='test_output', got '{args.output}'"
assert args.flag, "Expected flag to be True"
assert args.count == 42, f"Expected count=42, got {args.count}"

print("All argument assertions passed!")
