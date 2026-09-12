# Research Notes: Stage 2 Deterministic Replay Feasibility

**Feature**: [spec.md](spec.md)
**Date**: 2026-09-08

## Decision 1: Add a feasibility reducer above existing replay contracts

**Decision**: Implement the first Stage 2 slice as a deterministic report reducer
that consumes existing candidate/predeclaration metadata and
`ReplayCaptureRecord` values. Keep build, deployment, workload, and telemetry
execution behind the existing injected backend boundary.

**Rationale**: `replay_capture.py` already validates the frozen lane, upstream
build/execution lineage, deployment, observation completeness, artifact scope,
and censoring. `corpus_assembly.py` already preserves accepted rows and
rejections. A new feasibility layer can measure pilot yield and readiness
without coupling the reference implementation to a container runtime, cloud
provider, or telemetry system.

**Alternatives considered**:

- Add a concrete container/cloud runner: rejected because the Stage 2
  specification intentionally leaves infrastructure open and the constitution
  requires external effects to remain behind narrow interfaces.
- Rebuild replay capture inside the new feature: rejected because it would
  duplicate existing fail-closed behavior and increase the risk of diverging
  censoring semantics.

## Decision 2: Reuse structured Outcome Definitions and retain attestation

**Decision**: The feasibility profile references the existing structured
`OutcomeDefinition`, `Window`, `Threshold`, `ObservationProcess`, and
`Attestation` contracts. The plan does not create a second comparison format.

**Rationale**: `commensurability.py` already distinguishes direct equality,
attested equivalence, bridgeable window/threshold differences, and
irreducible event/observation-process differences. Reusing that result keeps
the Stage 2 gate aligned with the paper's claim boundary and preserves the
original definitions as evidence.

**Alternatives considered**:

- Compare the lane's prose rules: rejected because wording order and aliases
  create false negatives and are not a stable normative identity.
- Treat calibration or matching commit IDs as evidence of equivalence:
  rejected because neither repairs an event or observation-process mismatch.

## Decision 3: Use explicit terminal records and denominators

**Decision**: The report counts every selected revision exactly once, including
complete positive/negative outcomes, censored captures, and
blocked-before-compilation inputs. Missing evidence is represented by a status
and reason, never by dropping the revision.

**Rationale**: `capture_replay_lane` already maps failed upstream stages and
incomplete observations to censoring. The report must preserve those
denominators so a pilot cannot look feasible merely because unsuccessful
revisions disappeared.

**Alternatives considered**:

- Report only assembled, complete rows: rejected because that measures
  survivor quality rather than replay feasibility.
- Convert failed replay to negative labels: rejected because failure to observe
  an outcome is not an observed negative outcome.

## Decision 4: Make repeatability and release readiness separate gates

**Decision**: The report carries repeat-run discrepancies and public-release
checks as separate dimensions. A pilot can be technically executable but
`inconclusive` or `blocked` for repeatability or release reasons.

**Rationale**: Existing capture and evidence reporting already reject private or
privileged telemetry and preserve artifact hashes. Repeatability adds a
necessary feasibility question without turning one successful run into
evidence of reproducibility.

**Alternatives considered**:

- Treat a single successful run as sufficient: rejected because deterministic
  inputs do not prove a deterministic external environment.
- Collapse all failures into one boolean: rejected because reviewers need to
  distinguish insufficient yield, execution failure, provenance failure, and
  release blockage.

## Decision 5: Do not create an external contract directory

**Decision**: No `contracts/` artifact is required for this plan. The feature
is an internal Python reference-library/reporting slice; its public behavior
is specified by dataclasses, deterministic serialization, and focused pytest
conformance tests.

**Rationale**: There is no network API or external service contract in scope.
A quickstart and data model are sufficient for the implementation handoff.

## Decision 6: Establish repeatability before selecting an outcome threshold

**Decision**: Do not derive a threshold from the three one-run revision
measurements in `whoami-pilot-data-v2.json`. First repeat the same frozen lane
multiple times, beginning with one revision, so revision effect and run-to-run
noise are not treated as the same signal. Select a resolved scalar threshold
only after that baseline and place it in the structured threshold `value`.

The derivation rule and the baseline sample's content hash belong in the
predeclaration description and evidence manifest, respectively. They are
audit context, not a replacement for the machine-checked scalar. The v2
predeclaration and report remain unchanged historical evidence; a later
threshold requires a new predeclaration and a new external anchor.

**Rationale**: With one run per revision, the existing 35% spread cannot
distinguish revision effect from run-to-run noise. A quantile, midpoint, or
fitted constant over those same observations would move the labels after the
fact. A positive in the repeatability-baseline phase is explicitly a slow-run
signal, not yet a claim of revision regression; a future corpus threshold must
clear measured repeat noise.

## Decision 7: Use explicit evidence-scale corpus defaults

The corpus gate defaults are 800 labeled test rows per family with at least 50
positive and 50 negative outcomes. Small values remain available only through
explicit structural smoke-test overrides. This keeps the default contract
honest while preserving cheap reducer tests.

## Decision 8: Size the next feasibility pilot for acquisition, not evaluation

The next feasibility pilot targets 30-50 revisions, with three repeat runs on
three revisions and at least five positive and five negative events. This is
an acquisition decision, not a corpus-evaluation sample size. At an illustrative
20% observed positive rate, two-sided 95% Clopper-Pearson intervals are
`[0.077, 0.386]` for 30 revisions and `[0.100, 0.337]` for 50; the pilot must
not be treated as evidence-scale calibration.
