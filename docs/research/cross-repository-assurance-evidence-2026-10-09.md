# Cross-repository assurance evidence — 2026-10-09

## Purpose and scope

This note records bounded assurance evidence from Semadmit PR #10 and Bouleusis PR #4. These artifacts concern software behavior and replay invariants. They are not empirical JIT/AIOps forecasting results, construct validation, or evidence that two real-world outcome definitions are commensurable. The main paper does not use them to support its cross-family claim.

The source projects remain separate. This note includes no source code, model weights, or Bouleusis ledger data. The Bouleusis assurance documents are in a private repository; a public reader needs access to inspect their full contents. Their source commit and exact artifact hashes are recorded in the claim registry.

## Semadmit PR #10 — merged Core assurance oracle

PR [AbstractLogix/semadmit#10](https://github.com/AbstractLogix/semadmit/pull/10) merged to `main` at `e042aded9fd98d22aeb708337a26e9bbc9f2b7b8`. Its independent reference implementation was introduced at `47d55e1e7fa10348d4a39679add3590edfe8233b`; the machine certificate pins validation commit `40528b3ea6989cb9487c9c558fdb278b1567e9d9`.

The certificate records 57 exact Core result vectors, 68 raw parser cases, 9 identity vectors, one selected RFC 8785 vector, 96 seeded Python differential requests, and 7 of 7 selected Python Core mutations detected. Hosted Coverage passed on validation commit `40528b3ea6989cb9487c9c558fdb278b1567e9d9` in [run 37969409735](https://github.com/AbstractLogix/semadmit/actions/runs/37969409735). The reference covers a bounded test-only `fixture/0.1/check` operation and a common safe-integer JSON profile.

The separate `semadmit/claim/0.1` contract remains qualified Python-only semantics. The Haskell implementation does not provide claim-pack parity. A valid deterministic admission result means only that evidence may participate in the named operation under its declared policy. It does not establish source authenticity, evidence reliability, or claim truth. `selector-provenance/0.1` remains experimental, and its bounded independence cases remain `indeterminate`. The machine certificate reports no peer-reviewed status and no release approval.

## Bouleusis PR #4 — epistemic replay invariants

PR [AbstractLogix/Bouleusis#4](https://github.com/AbstractLogix/Bouleusis/pull/4) was open at the time of this check. Assurance evidence is recorded at commit `8f8394728f971d9393b51dbd6cbb56869ea3bc45`; the tested implementation source commit is `e5a01de546b8a2df8a8aec195ceeba039ba7d42b`, with Semadmit pinned at `de61aa87a5f4470fd64de33c926cff7f92cf8bd6`.

The machine report records fourteen tested invariants for run-scoped projection, event and evidence identity, finite confidence, terminal completion, deterministic replay, and isolation between external admission and claim state. It records 128 deterministic valid and 128 invalid generated streams, eight fixed valid state paths, eleven invalid stream kinds, and 9 of 9 selected source mutations detected. A duplicate run/sequence event identity counterexample was fixed by rejecting repeated event IDs after run scoping.

The recorded local Python 3.12 suite had 177 passes and 13 skips; hosted run [37965963858](https://github.com/AbstractLogix/bouleusis/actions/runs/37965963858) passed both the main job and the pinned Semadmit integration job. That job ran 44 Semadmit client tests and 14 Bouleusis integration tests. The report notes open limits, including Windows process-tree cleanup, concurrent writers, storage recovery, cross-claim evidence-content collision checks, and the rationale for some generic status updates.

These results verify selected state-projection and runtime behaviors against bounded test inputs. They do not establish that Bouleusis reasoning is generally accurate, that its beliefs are true, or that its forecasts have empirical predictive value. PR #4's own assurance report says independent human review is missing and recommends keeping the PR open.

## Evidence-class separation

| Evidence class | What the two assurance packages support | What they do not support |
|---|---|---|
| Behavioral verification | Selected exact outputs, error cases, and state transitions match bounded independent references or fixed expected vectors. | Complete implementation correctness, adversarial robustness, or all runtime behavior. |
| Deterministic evidence admission | Semadmit checks whether supplied evidence may enter a named operation under a declared policy. | Evidence authenticity, reliability, or the truth of an underlying claim. |
| Epistemic replay invariants | Bouleusis replay preserves selected run-scoped identity, state-transition, and completion rules. | General reasoning accuracy, calibrated belief, or accurate world models. |
| Empirical forecasting performance | Neither assurance package reports a field forecasting experiment for the IsoPrax targets. | JIT/AIOps predictive efficacy or forecast calibration on operational data. |
| Scientific validity | The artifacts provide bounded software assurance records for external assessment. | Independent scientific review, construct validity, or cross-dataset outcome commensurability. |

## Reproduction and access

Semadmit's merged assurance instructions and machine certificate are available at the immutable source commit. Bouleusis's assurance artifacts are identified by the exact PR commit and digests in `paper-claims-evidence.json`; the repository is private, so external reproduction requires authorized access. No result in this note is needed to regenerate the main paper's synthetic Benchmark A tables.
