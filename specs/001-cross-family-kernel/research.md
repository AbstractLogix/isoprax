# Research: Cross-Family Reference Kernel

## Decisions

### Authoritative mechanics

**Decision**: Copy the Isoprax v0.3 POC's Stage 0 event, signal,
commensurability, SQLite KB, strategy, evaluation, demo, and conformance-test
mechanics.

**Rationale**: The POC is the authoritative specification and reference. The
workspace had no implementation.

### External archive reuse boundary

**Decision**: Reuse its `uv` packaging shape, Ruff and pre-commit checks,
Apache-2.0 contribution framing, and fail-closed evidence language only.

**Rationale**: External corpus admission and JEPA/profile implementation solve a later
research problem and are not a Stage 0 Isoprax dependency.

### AI workflow guardrails

**Decision**: Root `AGENTS.md`, Codex Spec Kit skills, the project constitution,
pre-commit secret/format/merge-conflict checks, and a pre-push contract-test
hook form the local guardrail baseline.

**Rationale**: They block mechanical regressions and require claim boundaries
to be explicit, without pretending static tooling can validate research claims.

## External archive reuse map (avoid reinventing the wheel)

The external archive path previously reviewed
is an archive-first reference (spec and decision records), not a drop-in Python
package. Reuse is therefore requirement/process-level, not direct module import.

| Archive artifact area | Reuse in Isoprax Stage 0 | Status |
| --- | --- | --- |
| Evidence/claim discipline (separate structural vs stronger claims) | Keep explicit claim boundary language in README/spec/converge | Adopted |
| Calibration reporting posture (diagnostics required, overclaim blocked) | Keep ECE/Brier/reliability reporting and qualifier language | Adopted |
| Corpus admission and replay topology decisions | Defer to Stage 1+ roadmap only | Deferred |
| Joint-latent / JEPA profile content | Out of Stage 0 scope per constitution | Excluded |
| Privacy/release governance for captured corpora | Defer to Stage 1 corpus acquisition spec | Deferred |

### Practical continuation rule

When adding new work, prefer this order:

1. Reuse Isoprax v0.3 POC mechanics first (authoritative for Stage 0).
2. Reuse external archive decision text for research hygiene and evidence framing.
3. Only implement new code if neither source already satisfies the requirement.

This keeps Stage 0 small, auditable, and aligned with the constitution's
"Minimal Reference Scope" principle.
