# Quickstart: Haskell Reference Semantics Kernel

## Prerequisites

- GHC 9.14.1 and Cabal 3.16.1.0.
- Repository Python environment installed with `uv sync --group dev`.
- Network access is needed only on the first Cabal dependency fetch; all decisions run locally after build.

## Build and test

From the repository root:

~~~sh
cd haskell/isoprax-kernel
cabal update
cabal build all --enable-tests
cabal test all --enable-tests
~~~

Run the public Haskell API negative compilation checks:

~~~sh
bash test/compile-fail.sh
~~~

Run Python/Haskell differential fixtures:

~~~sh
cd ../..
ISOPRAX_KERNEL_BIN="$(cd haskell/isoprax-kernel && cabal list-bin isoprax-kernel)" \
  uv run pytest --no-cov -q tests/test_haskell_differential.py
~~~

## CLI examples

~~~sh
python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1])), separators=(",", ":")))' \
  ../../tests/reference/commensurable/direct.json \
  | cabal run --offline -v0 isoprax-kernel
~~~

Each invocation consumes JSON Lines and returns canonical JSON Lines. A window mismatch without evidence is bridgeable but not poolable. A complete bridge record preserves the bridgeable label and unlocks only the policy's poolability flag.

## Properties and benchmark

~~~sh
cd haskell/isoprax-kernel && cabal test properties --enable-tests
cd ../..
ISOPRAX_KERNEL_BIN="$(cd haskell/isoprax-kernel && cabal list-bin isoprax-kernel)" \
  uv run python scripts/benchmark_haskell_kernel.py --iterations 100
~~~

The benchmark writes JSON to standard output with first-process timing, warm p50/p95, compiler/runtime versions, and Python in-process comparison. It measures a new Haskell process per invocation; it does not treat subprocess latency as a performance win.

## Expected claims

- All shared fixtures pass with identical decision projections.
- Canonical UTF-8 and SHA-256 bytes match Python RFC 8785 vectors.
- Haskell property and compile-fail checks pass.
- The architecture note keeps research/data/runtime work in Python.
