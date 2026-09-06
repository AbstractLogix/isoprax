# Research: Reproducible Public Corpus Materialization

## Decisions

### Deterministic identity is hash-first and payload-canonical

**Decision**: Compute materialization identity from canonical JSON payloads
(`sort_keys=True`, fixed separators) over frozen profile metadata and normalized
record projections.

**Rationale**: Existing modules (`corpus_assembly.py`, `corpus_manifest.py`) are
already hash- and ordering-driven; reusing this pattern keeps behavior stable
across Python/CI environments.

**Alternatives considered**:

- Database auto-increment or runtime UUIDs (rejected: not deterministic)
- File timestamp identity (rejected: environment-dependent)

### Public-only boundary is enforced as fail-closed filtering

**Decision**: Reject private, privileged, credential-bearing, scope-mismatched,
or lineage-incomplete evidence at normalization time; never backfill missing
evidence.

**Rationale**: Feature 012 explicitly forbids silent substitution and requires
inspectable withholding behavior.

**Alternatives considered**:

- Best-effort redaction after acceptance (rejected: too late, weak guarantees)
- Warning-only policy (rejected: violates fail-closed contract)

### Preserve upstream semantics without recomputation

**Decision**: Materialization copies outcome class, censor reason, split,
score-time lineage references, and change grouping exactly from accepted
assembly/public observation records.

**Rationale**: The spec requires reproducibility and forbids adding labels or
changing outcomes.

**Alternatives considered**:

- Derive new aggregate labels during materialization (rejected: out of scope)
- Re-evaluate threshold outcomes (rejected: violates claim and stage boundaries)

## Scope and integration boundaries

- Input boundaries: accepted assembly evidence and safe public references only.
- Output boundaries: deterministic manifest + inclusion/withholding inventory.
- Explicitly excluded: network retrieval, admission changes, semantic claims,
  model efficacy claims, or pooled cross-family evaluation.

## Phase 1 readiness

No unresolved technical clarifications remain for Phase 1 design:

- Language/tooling fixed (`uv`, Python, pytest).
- Deterministic strategy fixed (canonical JSON + sorted ordering).
- Public-only policy fixed (fail-closed rejection).
