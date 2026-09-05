# Migration Map: Prior Archive → Isoprax Stage 1 Spec

This map records what we moved over, what we adapted, and what we intentionally
left out to avoid wheel reinvention and scope drift.

## Adopted (adapted into Stage 1)

- `archive/spec.md`
  - Adopted admission-gate framing, failure-report posture, and manifest
    reproducibility concepts.
- `archive/open-question-answers.md`
  - Adopted leakage guardrails, censoring semantics, split-freeze discipline,
    and adequacy framing.
- `archive/corpus-source.md`
  - Adopted predeclared horizon rule and clustered-observation caution.
- `archive/replay-topology.md`
  - Adopted lane-isolation and drift/replicate principles as planning
    constraints.
- `archive/release-and-independence.md`
  - Adopted independence and release-scope governance language.

## Deferred (for implementation or later features)

- Concrete horizon value and candidate-project feasibility pilot parameters.
- Replay orchestration details and infrastructure provisioning.
- Expanded release artifact policy beyond Stage 1 admission metadata.

## Excluded (out of current feature scope)

- JEPA/profile-specific algorithm and claim obligations.
- Joint-latent archive modules (`joint latent.py`) and profile-specific tests.
- Any private-data dependent workflow.
