# Haskell Reference Semantics Kernel

## Purpose

`haskell/isoprax-kernel/` is a small, offline reference implementation for selected deterministic Isoprax rules. Python remains the application and research runtime. Python owns acquisition, corpus construction, NumPy/PyTorch and JEPA work, training, experiments, visualization, notebooks, evaluation orchestration, and external adapters.

The kernel owns only the selected semantic boundary:

- structured Outcome Definition validation and normalized commensurability;
- endpoint-bound attestation and retained-observation bridge records;
- calibration qualification and equal-width expected calibration error;
- calibration fit/gate split separation and provenance/predeclaration checks;
- the existing Stage 0 Structural conformance projection;
- RFC 8785 canonical JSON and SHA-256 content identity.

It does not implement full corpus admission, Stage 1/2 evaluation, model work, bridge execution, or a network service. Python does not depend on the Haskell package at runtime.

## Boundary and invocation

The executable accepts one versioned JSON request per input line and writes one canonical JSON response per line. Version 1 supports `commensurability`, `calibration`, `admission`, `conformance`, and `identity`. Duplicate object keys and unsupported versions fail closed. See [the CLI contract](../specs/042-haskell-semantics-kernel/contracts/kernel-cli-v1.md) for request fields and response projections.

For a local build:

```sh
cd haskell/isoprax-kernel
cabal build all --enable-tests
cabal test all --enable-tests
bash test/compile-fail.sh
```

The Python differential harness runs all requests in `tests/reference/` against the existing Python semantic functions and compares normalized results. It can use `ISOPRAX_KERNEL_BIN` for a built executable or `ISOPRAX_KERNEL_COMMAND` for a wrapper. The Haskell CI workflow builds the package, runs QuickCheck and compile-fail checks, then runs differential fixtures and the benchmark.

## Evidence in the Haskell API

`OutcomeDefinition`, `AttestationEvidence`, `BridgeEvidence`, `PoolingEvidence`, and `CalibratedEvidence` have hidden constructors in the exposed `Isoprax.Kernel` module. Callers create validated definitions/evidence through `parseOutcomeDefinition`, `parseAttestationEvidence`, and `parseBridgeEvidence`. `checkCommensurabilityWithEvidence` accepts the opaque evidence types.

`authorizePooledComparison` requires a `PoolingEvidence` plus calibrated evidence for the two definition IDs named by that proof. Its return type is an authorization value. Compile-fail examples verify that callers cannot omit the pooling proof, either calibration value, or construct the opaque evidence directly.

The CLI starts from JSON, so its boundary necessarily performs runtime validation. The proof types apply inside Haskell and do not cross into Python. The compatibility `checkCommensurability` function is also available to Haskell callers that need the complete raw-JSON validation path.

Bridge evidence contains a transformation identifier, retained-observation manifest reference, and provenance reference bound to both definitions. The kernel checks that these fields are present and non-empty. It does not inspect the referenced records, establish that a transformation ran, or prove that transformation correct. This deliberately mirrors the existing Python `retained_observations` policy without strengthening its evidence claim.

The Stage 0 projection remains `Cross-Family Conformance (Structural)`, including when calibration and commensurability pass. The selected admission operation reports only two existing gates and never represents full corpus admission.

## Independent verification

The shared fixtures cover direct and attested matches, bridgeable mismatches, irreducible event/process differences, missing or mismatched evidence, calibration boundaries, selected admission gates, Structural-only reports, duplicate keys, and canonical identity vectors. The QuickCheck suite generates 1,000 examples for each configured property, including reflexivity, symmetry, fail-closed incompatible and malformed definitions, typed evidence, bridge omission, canonical key-order identity, serialization round trips, and the Stage 0 ceiling.

The Haskell package pins GHC 9.14.1 and Cabal 3.16.1.0 in CI, constrains the corresponding `base` version, and commits the resolved Cabal freeze file. RFC 8785 output is compared byte-for-byte with Python fixtures before hashing.

## Keep Python as the system runtime

The kernel is a semantic reference and type-checked library, not a replacement application. Keep numerical experimentation and data paths in Python. Consider production subprocess calls only if a later use case has a clear correctness requirement, an explicit evidence contract, and measured latency acceptable to that workflow. Do not add FFI or a service solely to reduce the benchmarked one-shot CLI cost.
