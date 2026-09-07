# Isoprax Reference Implementation

Licensed under [Apache-2.0](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md)
and [AGENTS.md](AGENTS.md) before contributing.

This repository contains the runnable Stage 0 reference implementation of the
authoritative Isoprax v0.3 POC. It demonstrates shared event, signal,
knowledge-base, feedback, calibration, and commensurability mechanics for the
Change and Operational families.

The implementation declares **Cross-Family Conformance (Structural)** only.
Its baseline Outcome Definitions are deliberately non-commensurable, so it
withholds pooled scores and makes no Semantic or Full Conformance claim.

## Where the specification and POC are

- **Stage 0 feature spec (in this repo):**
  `specs/001-cross-family-kernel/spec.md`
- **Stage 1 admission extension spec (in this repo):**
  `specs/002-stage1-corpus-admission/spec.md`
- **Authoritative Isoprax v0.3 POC reference:**
  Vendored at [`docs/isoprax-v0.3-poc.md`](docs/isoprax-v0.3-poc.md), with
  source provenance recorded in
  [`docs/isoprax-v0.3-poc-provenance.md`](docs/isoprax-v0.3-poc-provenance.md).
  Normative implementation citations are checked against that document.

In this repository, the runnable POC-aligned implementation is the code under
`isoprax/` plus `examples/demo_cross_family.py` and
`tests/test_conformance.py`.

## Why Stage 1 matters

The repository's most defensible near-term contribution is its Stage 1
admission-before-acquisition discipline. The implementation does not claim a
new model or broader conformance class; it enforces the evidence-gate checks
that make real corpus work credible:

- lineage completeness from change → deployment → observation,
- prediction-time leakage rejection,
- single-system corpus boundaries with cross-system pooling rejected,
- no private third-party production data or privileged telemetry requirements,
- deterministic reporting that keeps admission as evidence infrastructure only.

This is materially more mature and immediately useful than speculative JEPA or
profile work, and it is the right near-term boundary for the project.

## What this proves

Running `examples/demo_cross_family.py` demonstrates, on synthetic data:

1. **Cross-Family Conformance (spec §3.3):** both families emit `Signal`
  objects through one interface and persist through one `KnowledgeBase`.
2. **Calibration keystone (spec §5.3):** both families' raw heuristic scores
  can be calibrated through the same mechanism; diagnostics include ECE,
  Brier score, reliability bins, and sample size.
3. **Commensurability keystone (spec §5.6):** calibrated probabilities are
  still not jointly comparable when Outcome Definitions differ in event,
  observation process, window, or thresholds.
4. **Evaluation discipline (spec §8):** time-sliced train/test handling and
  paired score-error comparison utilities are exercised in the demo flow.

The result is intentionally narrow: a reproducible structural contract proof
that rejects overclaiming.

## Run

```sh
make sync
make test
make demo
make hooks
```

Run `make help` to list quick developer actions. `make check` runs lint,
format verification, the coverage-enforced test suite, and the demo.

## Guardrails

- `AGENTS.md` makes the POC and its evidence boundaries authoritative.
- Spec Kit artifacts under `specs/` record intent, implementation planning,
  tasks, and convergence evidence.
- Pre-commit blocks malformed source, merge conflicts, oversized additions,
  private keys, lint/format drift, and runs contract tests before push.
- The project is offline by default; remote adapters and automatic remediation
  are outside this Stage 0 reference scope.

## What this is not

- Not a real-world performance claim: Stage 0 evidence is synthetic and
  structural.
- Not a Semantic cross-family claim: commensurability must be satisfied first;
  calibration alone cannot bridge non-commensurable definitions.
- Not Full Conformance: only a subset of strategy types is implemented in this
  reference slice.

## Next steps

1. Add adapters for real VCS/CI and operational telemetry backends.
2. Run Stage 1 per-family validation on public datasets with explicit,
   separately-scoped reporting.
3. Build a deterministic replay corpus with predeclared thresholds and shared
   observation semantics to enable Semantic conformance evaluation.
4. Expand the conformance suite and publish repeatable evidence artifacts.

## Stage 1 status (admission extension)

This repository now includes a Stage 1 admission-gate module
(`isoprax/admission.py`) and conformance tests (`tests/test_stage1_admission.py`)
that validate lineage integrity, censoring discipline, prediction-time leakage
controls, split freezing, adequacy checks, and deterministic evidence reports.

Passing Stage 1 admission gates is **not** a conformance-class upgrade by
itself; it is evidence infrastructure only.

The deterministic evidence-reporting module (`isoprax/evidence_reporting.py`)
can publish a bounded summary of assembled corpus, replay-capture, and
admission evidence. Its reports expose only safe identifiers, hashes, counts,
gate summaries, and explicit unavailable evidence; they do not expose replay
payloads or upgrade an admission result to Semantic or Full Conformance.

### Stage 1 independence constraints

- No private third-party production data is required by the admission layer.
- Cross-system pooling is rejected for a single admitted corpus.
- Release-scope and threshold-freeze metadata are required in admission
  manifests.
