# %% [markdown]
# # Julia notebook
#
# This notebook is a plain Julia script in
# [Jupytext](https://jupytext.readthedocs.io/en/latest/) percent format and is
# executed by the `julia` kernel defined in `//kernel`.

# %%
using LinearAlgebra

A = [2.0 1.0; 1.0 3.0]
println("det(A) = ", det(A))
eigvals(A)

# %%
# `args` of the Bazel target are forwarded to `ARGS`.
println("ARGS = ", ARGS)
@assert ARGS == ["--trials=3"] "Unexpected ARGS: $(ARGS)"

# %%
fib(n) = n < 2 ? n : fib(n - 1) + fib(n - 2)
[fib(n) for n in 0:10]

# %% [markdown]
# ## Summary
#
# The kernel, Julia itself and every package are provided by Bazel; nothing
# is read from `~/.julia`.
