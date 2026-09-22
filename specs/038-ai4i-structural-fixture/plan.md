# Implementation Plan: AI4I 2020 Structural Fixture

**Branch**: `038-ai4i-structural-fixture` | **Date**: 2026-09-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/038-ai4i-structural-fixture/spec.md`

## Summary

Add a small, offline-only verifier and provenance manifest for a locally supplied
AI4I 2020 CSV. The verifier validates the published schema and structural counts,
reports rather than repairs composite/mode-label disagreement, and exposes
explicit outcome definitions that exercise Isoprax's irreducible event-mismatch
boundary. The full external snapshot is not fetched or vendored by the repository.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.10-3.14

**Primary Dependencies**: Python standard library plus existing Isoprax commensurability types

**Storage**: Local CSV supplied by the operator; checked-in JSON provenance manifest

**Testing**: pytest, Ruff, offline CLI verification against a downloaded UCI artifact

**Target Platform**: Offline Linux/Python reference implementation

**Project Type**: Python library/reference PoC with a verification script

**Performance Goals**: Verify the 10,000-row snapshot in a bounded local run without network access

**Constraints**: No runtime data-science dependency, no automatic download, no label repair,
preserve source identity and explicit non-efficacy boundary

**Scale/Scope**: One 10,000-row synthetic milling-process snapshot, six outcome labels,
and structural/commensurability verification only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Design response |
|---|---|---|
| I. Specification Authority | PASS | The feature spec defines the offline verifier and claim boundary; UCI metadata is recorded as source evidence, not silently inferred. |
| II. Honest Conformance | PASS | Reports are structural/public-synthetic evidence only and preserve label discrepancies; no efficacy or Semantic/Full claim is emitted. |
| III. Contract-First Testing | PASS | Focused tests cover schema, checksum, malformed rows, label mismatch, and irreducible commensurability rejection. |
| IV. Deterministic Core, Explicit Effects | PASS | CSV parsing and summaries are deterministic; network retrieval is explicitly outside the verifier. |
| V. Minimal Reference Scope | PASS | The repository adds a small standard-library verifier and manifest, not a provider adapter or full external corpus. |

**Gate status**: PASS before research and after design.

## Project Structure

### Documentation (this feature)

```text
specs/038-ai4i-structural-fixture/
├── plan.md              # This file ($speckit-plan command output)
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/ai4i2020-verifier.md
└── tasks.md             # Phase 2 output ($speckit-tasks command - NOT created by $speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
isoprax/
├── ai4i2020.py              # schema, verifier, summary, outcome definitions
└── __init__.py              # public exports

scripts/
└── verify_ai4i2020.py       # offline JSON-reporting CLI

examples/ai4i2020/
├── README.md                # retrieval, verification, and claim boundary
└── manifest.json            # pinned source and expected summary; no data snapshot

tests/
└── test_ai4i2020.py         # parser, integrity, summary, and commensurability tests
```

**Structure Decision**: Keep the verifier as a dependency-light library module,
expose one script for reproducible operator verification, and keep external data
out of the repository. The manifest is the reviewable provenance boundary.

## Complexity Tracking

No constitution violations require justification.
