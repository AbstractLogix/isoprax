# Data Model: Stage 2 Predeclaration Integrity

The published JSON remains the source of truth for the pilot. Its
`artifact_hash` covers every field except itself. `predeclaration_commit` is
the introducing commit of the artifact, while the generated report separately
records the current corpus-data commit and the verified ancestry result.
