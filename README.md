# Isoprax Reference Implementation

Licensed under [Apache-2.0](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md)
and [AGENTS.md](AGENTS.md) before contributing.

This repository contains the runnable Stage 0 reference implementation of the
authoritative Isoprax v0.3 POC, plus Stage 1 public-data evidence and a bounded
Stage 2 deterministic-replay feasibility reducer. It demonstrates shared
event, signal, knowledge-base, feedback, calibration, and commensurability
mechanics for the Change and Operational families.

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
- Not Full Conformance: the repository still withholds Semantic and Full
  Conformance claims; Stage 2 feasibility does not substitute for corpus and
  evaluation evidence.

## Next steps

1. Repeat one frozen lane before selecting a scalar outcome threshold.
2. Run a predeclared 30-50 revision pilot with repeated lanes and both outcome
   classes.
3. Publish a bootstrapped outcome-yield estimate with its implied corpus size.
4. Build the 800-row-per-family predeclared corpus with 50 outcomes of each
   class.
5. Run Stage 2 corpus evaluation with non-degenerate per-family scores.
6. Add adapters for real VCS/CI and operational telemetry backends.

These gates remain evidence work: passing them does not by itself establish
Semantic or Full Conformance.

## Stage 1 status (admission extension)

This repository includes a Stage 1 admission-gate module
(`isoprax/admission.py`), per-family evaluation, and a reproducible public-data
run over ApacheJIT Apache Ignite and Google Cluster Trace v1. The generated
aggregate evidence is checked in at
[`docs/stage1/stage1-public-validation.json`](docs/stage1/stage1-public-validation.json),
with the frozen inputs and rerun command documented in
[`specs/016-stage1-public-validation/quickstart.md`](specs/016-stage1-public-validation/quickstart.md).

The completed run passes admission for both single-system families and records
calibrated per-family gate results. Apache Ignite reports 1,750 calibration-gate
events with ECE 0.0443 and AUC 0.8434; Google Trace reports 556 events with ECE
0.0429 and AUC 0.7522. These are scoped evaluation diagnostics, not a pooled
metric or a cross-family efficacy claim.

Passing Stage 1 admission gates is **not** a conformance-class upgrade by
itself; it is evidence infrastructure only.

Stage 1 freezes split boundaries and change-group isolation, and the completed
public-data run records the calibration procedure and source identities. It
does not claim to capture adaptive model-retraining policy, model-version
lineage, or interpretation-stability evidence. Any future real-data
evaluation that adapts models over time must record those policies and versions
explicitly; adaptation and interpretability evidence do not establish outcome
commensurability.

The deterministic evidence-reporting module (`isoprax/evidence_reporting.py`)
can publish a bounded summary of assembled corpus, replay-capture, and
admission evidence. Its reports expose only safe identifiers, hashes, counts,
gate summaries, and explicit unavailable evidence; they do not expose replay
payloads or upgrade an admission result to Semantic or Full Conformance.

### Stage 2 status (replay feasibility)

`isoprax/stage2_feasibility.py` provides the next evidence gate. It validates a
predeclared pilot profile, normalizes every selected revision into one terminal
record, preserves censored and blocked-before-compilation outcomes, compares
repeat runs, and emits only `feasible`, `inconclusive`, or `blocked`.

Stage 2 feasibility is not a Semantic result. The reducer does not acquire a
full corpus, publish pooled cross-family metrics, or claim model efficacy. A
future corpus/evaluation stage must consume a feasible pilot and independently
establish those claims.

The pilot tooling also reports a deterministic bootstrap estimate of usable
positive/negative outcome yield and an implied planning size. The current
whoami measurements have no positive events, so the report publishes no finite
corpus-size estimate and remains unsuitable for corpus evaluation.

The feasibility acquisition target is at least five positive and five negative
events; the later evidence-scale corpus target is 800 test rows with 50 of
each class per family.

The injected end-to-end path is exercised by
`tests/test_stage2_pilot_integration.py`. It runs synthetic build qualification,
injected-runner evidence, replay capture, and feasibility reporting. This
verifies pipeline wiring only; the reference module does not launch a container
engine, and a real feasibility result still requires a public project adapter
and a predeclared pilot run.

The first bounded public pilot is recorded under `docs/stage2/` for
`traefik/whoami`: three immutable revisions were built locally and each was
observed with a 60-second, 120-request `/bench` workload. The checked-in
report is intentionally `inconclusive` until a Sigstore DSSE bundle with a
verified Rekor inclusion proof is supplied. All three observed outcomes were
negative, so even an anchored report would be replay-feasibility evidence
only; it would not establish positive-event yield, model efficacy, Semantic
conformance, or full-corpus adequacy. Its yield estimate is explicitly
`no_positive_events` with no finite implied corpus size.

Regenerate the report from the committed measurements with:

```bash
uv run python scripts/run_stage2_whoami_pilot.py \
  --output docs/stage2/whoami-pilot-report-v2.json
```

Pass `--attestation-bundle`, `--attestation-identity`, and
`--attestation-issuer` to enable the independently verified anchor path.

### Stage 2 corpus evaluation gate

The next reducer is `isoprax/stage2_corpus_evaluation.py`. It admits only a
predeclared corpus with complete replay lineage, usable positive and negative
label yield, time-safe rows, and non-degenerate per-family scores. Calibration
alone is insufficient: constant-score predictors remain inconclusive. Change
and Operational evaluation stays separate, and pooled/Semantic claims remain
withheld.

The production corpus defaults require 800 labeled test rows per family,
including at least 50 positive and 50 negative outcomes, with maximum ECE
`0.05`. Smaller values are permitted only when explicitly declared by a
structural smoke test; they are not evidence-scale defaults.

### Stage 1 independence constraints

- No private third-party production data is required by the admission layer.
- Cross-system pooling is rejected for a single admitted corpus.
- Release-scope and threshold-freeze metadata are required in admission
  manifests.
