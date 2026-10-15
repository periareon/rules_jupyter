// %% [markdown]
// # Rust notebook
//
// This notebook is a Rust file in
// [Jupytext](https://jupytext.readthedocs.io/en/latest/) percent format and is
// executed by the `rust` kernel ([evcxr](https://github.com/evcxr/evcxr))
// defined in `//kernel`.

// %%
let x: u64 = (1..=10).product();
println!("10! = {x}");

// %%
// `args` of the Bazel target are available as `args`.
println!("args = {args:?}");
assert_eq!(args, ["--trials=3"]);

// %%
fn fib(n: u64) -> u64 {
    if n < 2 { n } else { fib(n - 1) + fib(n - 2) }
}

(0..=10).map(fib).collect::<Vec<_>>()

// %% [markdown]
// ## Summary
//
// Each cell is compiled with the `cargo` and `rustc` of the `rules_rust`
// toolchain; no Rust installation is required on the host.
