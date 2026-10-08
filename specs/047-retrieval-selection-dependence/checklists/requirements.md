# Specification Quality Checklist: Retrieval and Interpretation Dependence

**Purpose**: Check specification completeness before planning
**Created**: 2026-10-08
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details in the user-facing requirement
- [x] Focused on research value and evidence boundaries
- [x] Written for technical and research readers
- [x] All required sections are complete

## Requirement Completeness

- [x] No clarification markers remain
- [x] Requirements are testable and clear
- [x] Success criteria are measurable by artifact review
- [x] Success criteria do not depend on a specific implementation
- [x] Acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is bounded
- [x] Dependencies and assumptions are identified
- [x] The benchmark tests held-out score calibration against source status
- [x] The benchmark tests paired-selector corroboration against realized-budget-matched controls
- [x] The initial model-role set names all six requested models and permits only a documented runtime-compatible precision tag for EmbeddingGemma 2
- [x] Tev1 calibration is reported per predeclared question family
- [x] Similarity, probability, confidence, and categorical judgments retain their score types and named targets
- [x] Qwen, Gemma, and Guardian pooling is tested only on the same target and held-out cases
- [x] Shared base or architecture lineage is separate from exact model identity
- [x] User-supplied Bouleusis outcomes are labeled as unverified source data
- [x] Evidence recall, task success, and epistemic measures remain distinct
- [x] Seed variants of one defect are not counted as independent bugs
- [x] The iterative retrieval protocol includes equal-budget and extra-reasoning controls
- [x] No selector-identity-only independence rule is handed off to Semadmit

## Feature Readiness

- [x] Each requirement has an acceptance criterion
- [x] User stories cover the research note, protocol, and next-slice handoff
- [x] Success criteria can be checked from the artifacts
- [x] The specification does not require runtime or product behavior

## Notes

The original two-model attempt was interrupted after the model set changed. It wrote no result file and is excluded. The role experiment has no scored results. The active Linux Ollama service rejected both the requested EmbeddingGemma 2 default tag and the proposed 740M BF16 tag; pinning remains pending a compatible build. No alternate embedding model is substituted without a dated amendment.
