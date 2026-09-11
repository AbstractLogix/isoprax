# Research: Stage 2 Predeclaration Integrity

The Stage 2 script previously loaded `artifact_hash` without recomputing it,
overwrote the declared commit with a source constant, and never called
`evaluate_predeclaration_provenance`. The predeclaration already declared
family semantics but the script hardcoded the process, window, and thresholds.

The fix keeps the self-hash convention explicit: hash canonical JSON with only
`artifact_hash` omitted. The artifact's introducing commit is derived from Git
history and must match the recorded field.
