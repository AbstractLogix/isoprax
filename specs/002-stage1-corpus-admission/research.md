# Research: Stage 1 Corpus Admission and Replay Evidence

## Decisions

### Reuse-first source policy

**Decision**: Reuse archived decisions for corpus admission, replay topology,
leakage control, and reproducibility language; do not import JEPA/profile
implementation obligations into Stage 1.

**Rationale**: Archived material is rich in settled admission constraints,
but this repository's constitution keeps Stage 1 focused on evidence integrity,
not model-profile expansion.

### Admission gate posture

**Decision**: Admission is a deterministic gate that reports evidence pass/fail
by requirement and never auto-upgrades conformance class.

**Rationale**: Passing an admission gate is necessary infrastructure, not
sufficient evidence for Semantic or Full conformance claims.

### Replay and independence posture

**Decision**: Stage 1 artifacts preserve independence constraints: no private
third-party production data, no privileged telemetry dependencies, and explicit
release-scope metadata in manifests.

**Rationale**: Independence and auditable release scope reduce legal and
reproducibility ambiguity before implementation work begins.

## Migrated insights from prior archive

| Source doc | Reused here | Adaptation applied |
| --- | --- | --- |
| `archive/spec.md` | Corpus admission gates and failure reporting shape | Renamed to Isoprax Stage 1 scope, removed profile claims |
| `archive/open-question-answers.md` | Leakage, censoring, split-freeze, and adequacy framing | Kept as requirements language; omitted JEPA backend decisions |
| `archive/corpus-source.md` | Horizon predeclaration and clustered-observation cautions | Generalized to replay-compatible rule without fixing a value yet |
| `archive/replay-topology.md` | Lane isolation and drift/replicate principles | Kept as follow-on plan constraints, not immediate implementation |
| `archive/release-and-independence.md` | Independence and release-scope governance | Converted into manifest metadata requirements |

## Non-reused archive content (intentionally excluded)

- JEPA and joint-latent profile conformance obligations.
- Backend/model training selection guidance.
- Profile-specific tests and implementation modules in archive Python files.

## Open decisions for planning phase

1. Fixed horizon value/rule for first admitted corpus profile.
2. Minimum per-split adequacy floors for first Isoprax Stage 1 run.
3. Release artifact scope baseline (manifest-only vs broader under replay).
4. Candidate corpus adapter boundary and ownership.
