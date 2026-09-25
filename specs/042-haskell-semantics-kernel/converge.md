# Convergence Record: Haskell Reference Semantics Kernel

## Result

The implementation satisfies the feature specification, plan, task scope, and Isoprax constitution. No additional implementation tasks were identified. The only remaining gate is the hosted GitHub Actions run on the pull request; it was not available before PR creation.

The assessment covered 13 functional requirements, 7 success criteria, 17 acceptance scenarios, 8 plan decisions, and all 5 constitutional principles. The implementation preserves the current Python semantics, keeps Stage 0 Structural, and limits admission behavior to the two selected gates.

## Verification obtained

- A fresh copy of `haskell/isoprax-kernel/` with an empty Cabal cache fetched the pinned packages and passed `cabal build all --enable-tests`, `cabal test all --enable-tests`, and `bash test/compile-fail.sh` using GHC 9.14.1 and Cabal 3.16.1.0.
- The QuickCheck suite passed 10 properties with 1,000 generated examples each.
- Six compile-fail cases rejected missing or forged pooling, calibration, attestation, and bridge evidence.
- The Python/Haskell differential suite passed all 34 shared fixtures, including the decimal ECE bin-edge boundary and RFC 8785 numeric/Unicode vectors.
- The full Python suite passed: 566 passed, 1 skipped. The skipped test was the existing CUDA-specific EB-JEPA path because CUDA is available on this host.
- `uv run ruff check .` passed; `uv lock --check` confirmed 225 resolved packages.
- The 100-invocation-per-workload benchmark and exact environment are recorded in [assessment.md](assessment.md).

## Remaining external gate

The new hosted Haskell workflow has not run yet. Merge remains contingent on its build, QuickCheck, compile-fail, differential, benchmark steps and the repository's required PR checks passing.
