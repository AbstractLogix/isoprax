# Haskell Kernel Experiment Assessment

## Decision

Keep the kernel as a small CI-checked semantic reference and typed Haskell library. Do not wire it into Python's latency-sensitive or research execution paths. The experiment demonstrates a meaningful correctness benefit through opaque evidence values, compile-time rejection of invalid API calls, property coverage, and independent cross-runtime checks. The measured subprocess cost makes a default per-call Python boundary inappropriate for fast loops.

## Evidence obtained

- GHC 9.14.1 / Cabal 3.16.1.0: library, CLI, and property suite built successfully from the frozen package plan.
- A clean copy of the Haskell package, with an empty Cabal package cache, resolved the committed freeze and passed build, property, and compile-fail checks after fetching the pinned packages.
- QuickCheck: 10 properties passed with 1,000 generated examples each (10,000 generated checks total). Properties cover reflexivity, symmetry, event/process mismatch fail-closed behavior, typed attestation/bridge authorization, threshold ordering, missing bridge evidence, malformed windows, identity key ordering, canonical serialization round trips, and the Stage 0 ceiling.
- Compile-fail checks passed for omitted pooling proof, omitted calibrated evidence, omitted second calibration value, and attempts to construct pooling, attestation, or bridge evidence directly.
- Python/Haskell differential suite passed all 34 fixtures. It compares commensurability, bridge and attestation errors, calibration and admission gates, Stage 0 conformance labels, duplicate-key/version errors, and RFC 8785 canonical text and digests. ECE values use 1e-12 absolute tolerance; identity output is exact.
- The RFC 8785 fixture set includes Unicode, key order, negative zero, safe-integer boundary, unsafe integer rejection, exponent formatting, and `1e23`; all canonical strings and SHA-256 values matched Python.

## Subprocess benchmark

Each Haskell sample launches a new CLI process. “First process” is the first invocation after compilation in the measured run; the 100 warm samples are later one-shot processes on the same host. Python measurements call the matching oracle after imports have completed. Times are milliseconds.

| Workload | Haskell first | Haskell p50 | Haskell p95 | Python first call | Python p50 | Python p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Commensurability | 2.4343 | 1.9093 | 2.2195 | 0.1269 | 0.0233 | 0.0367 |
| Canonical identity | 2.0905 | 1.8102 | 2.2346 | 0.5261 | 0.0420 | 0.0846 |

Environment: GHC 9.14.1, Cabal 3.16.1.0, Python 3.11.2, NumPy 2.2.6, SciPy 1.15.3, scikit-learn 1.7.2, rfc8785 0.1.4; Linux 6.18.33.2 on WSL2, 24 logical CPUs. The Haskell CLI was built and timed inside the same Linux container. This is a small-request reference measurement, not a production workload or a throughput claim.

## What improved correctness

The exposed library makes validated `OutcomeDefinition`, `AttestationEvidence`, `BridgeEvidence`, `PoolingEvidence`, and `CalibratedEvidence` values impossible to forge through its public module. `authorizePooledComparison` cannot be called without poolability proof and calibration evidence for both compared definitions. Compile-fail checks lock down that boundary.

The independent test path found an implementation bug in the first Haskell parser pass (nested fields were looked up using their display paths), a fit/gate reason-code projection mismatch, and an ECE bin-edge mismatch at decimal boundaries between division-based Haskell edges and NumPy `linspace`. The adapter also initially mislabeled successful ECE results. These were corrected; the 34-fixture suite now includes the decimal boundary case. This demonstrates why a second implementation needs shared fixtures and must not be trusted solely because it compiles.

## Limits and follow-up boundary

- CLI input is JSON, so decisions at that boundary still require runtime validation. Haskell proof values do not cross into Python.
- Bridge records are endpoint-bound declarations only. The kernel does not verify retained rows, execute a transformation, or prove the transformation correct.
- The admission operation implements only calibration split separation and provenance/predeclaration checks; it is not full Stage 1 admission.
- The conformance evaluator mirrors Stage 0 and never produces Semantic or Full conformance.
- The benchmark confirms one-shot subprocess startup is materially slower than Python in-process calls for these small payloads. Keep the CLI for conformance testing, reproducible reference decisions, and offline verification; use the Haskell library directly for any future Haskell caller that needs compile-time evidence guarantees.
- One compiler version and Linux CI target are pinned. Broader compiler portability and production deployment were outside this experiment.
