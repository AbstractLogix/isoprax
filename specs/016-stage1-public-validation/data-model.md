# Data Model: Complete Stage 1 Public-Data Validation

## SourceArtifact

- `source_id`, `source_reference`, `license`, `published_checksum`, `sha256`,
  `local_filename`

## Stage1FamilyEvidence

- source artifact and adapter version
- frozen split definitions and predeclaration identity
- admission report summary
- per-family evaluation report summary
- outcome definition identity

## Stage1PublicValidationReport

- report identity
- ordered source artifacts
- ordered family evidence records
- explicit claim boundary
- no pooled score or pooled metric
