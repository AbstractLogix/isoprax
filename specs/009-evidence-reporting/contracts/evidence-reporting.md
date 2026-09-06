# Evidence Reporting Contract

## Public API

`build_evidence_report(profile, assembly, captures, admission_profile, admission)`
returns an immutable `EvidenceReport`.

## Preconditions

- `assembly.claim_scope` is `corpus_assembly_evidence_only`.
- Every accepted assembly row has exactly one replay capture with matching lane
  identity, system, deployment reference, and outcome class.
- Capture claim scope is `replay_observation_evidence_only`.
- Profile identity, release scope, and published artifacts agree across the
  reporting profile, assembly manifest, and admission manifest.
- Admission provenance exists and does not allow private production data or
  privileged telemetry.

## Output guarantees

- Canonical public representations and report identity are deterministic.
- Gate summaries include no failed row identifiers.
- Capture summaries contain only safe identifiers, artifact metadata/state, and
  outcome/censoring metadata; they omit prediction fields and payloads.
- The claim boundary is fixed to admission evidence only and explicitly
  withholds Semantic/Full, efficacy, and pooling claims.
- Missing required evidence is explicit; it never becomes inferred success.

## Failure behavior

Raise `ValueError` for invalid profile values, mismatched inputs, duplicate or
missing accepted-row captures, unsupported claim scopes, scope/artifact
mismatch, or disallowed provenance. No partial report is returned.
