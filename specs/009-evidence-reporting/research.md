# Research: Stage 1 Evidence Reporting

## Decision: Reduce existing evidence instead of recomputing it

**Rationale**: `CorpusAssemblyReport` is the Feature 008 authority for accepted
rows/profile identity, and `AdmissionReport` is the Feature 002 authority for
gate decisions. Re-evaluating either would create divergent claims.

**Alternatives considered**:

- Re-run admission from rows: rejected because the caller's evaluated profile
  and gate results must be represented exactly.
- Use a generic report mapping: rejected because it would allow unvalidated
  raw material and hidden schema drift.

## Decision: Join replay captures through public row lineage

**Rationale**: An accepted assembled row retains `observation_id` as the
capture lane identity, `deployment_id` as the safe deployment reference, and
its profile identity. A reporter can require one matching
`ReplayCaptureRecord` per accepted row and publish only its existing identities,
qualification hash, execution identity, artifact states/hashes, and censoring
metadata.

**Alternatives considered**:

- Trust arbitrary build/runner reference strings: rejected because they are not
  derivable from the evidence being summarized.
- Publish capture payloads: rejected because they may contain restricted
  deployment/observation content.

## Decision: Use a frozen reporting profile for public-only metadata

**Rationale**: Predeclaration reference/hash and release-scope publication
policy are not all present in assembly output. A narrow profile supplies these
safe, frozen references and required evidence categories while the reporter
checks scope and provenance against the existing admission manifest.

**Alternatives considered**:

- Fetch predeclaration or artifact records externally: rejected because the
  deterministic core is offline.
- Treat missing references as successful evidence: rejected; they become
  unavailable entries and an inconclusive report.

## Decision: Derive a three-state reporting status

**Rationale**: `admission_evidence` is possible only with passing admission and
complete required report evidence. A failed gate is `blocked`; absent/incomplete
required evidence is `inconclusive`. None is a conformance class.

**Alternatives considered**:

- Boolean success: rejected because it collapses failed gates and unavailable
  evidence.
- Promote passing admission to conformance: rejected by the specification and
  constitution.
