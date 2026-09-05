# Implementation Plan: Cross-Family Reference Kernel

**Branch**: `001-cross-family-kernel` | **Date**: 2026-09-05 | **Spec**: [spec.md](spec.md)

**Input**: Authoritative Isoprax v0.3 POC and the feature specification.

**Note**: This template is filled in by the `$speckit-plan` command; its definition describes the execution workflow.

## Summary

Implement the offline Stage 0 reference kernel: strict normalized events,
probability and forecast signals, Outcome Definitions, a mechanical
commensurability guard, SQLite event/signal/outcome persistence, calibration
diagnostics, two synthetic baseline strategies, and an executable demo. Copy
the authoritative POC mechanics; apply external archive guidance only for
auditable workflow and
evidence guardrails.

## Technical Context

**Language/Version**: Python >=3.10,<3.15

**Primary Dependencies**: NumPy, scikit-learn, SciPy

**Storage**: SQLite reference implementation; no network dependency

**Testing**: pytest, Ruff, pre-commit

**Target Platform**: Python-supported local developer environments

**Project Type**: Installable Python library with an executable demonstration

**Performance Goals**: Deterministic synthetic demo and focused suite complete locally without remote calls

**Constraints**: Stage 0 claims remain synthetic and Structural; no automatic action,
real-data claim, Semantic conformance, or external corpus/JEPA-profile code by
inference

**Scale/Scope**: Three event types, two baseline strategies, one local KB, and a 25+ test conformance suite

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Specification Authority: pass — authoritative POC v0.3 is copied for the Stage 0 mechanics.
- Honest Conformance: pass — declaration remains Cross-Family Conformance (Structural).
- Contract-First Testing: pass — tests are copied and extended for the feedback-definition guard.
- Deterministic Core: pass — all core operations are local and explicit.
- Minimal Reference Scope: pass — external archive reuse is limited to
  pre-commit, packaging, and contribution guardrails.

## Project Structure

### Documentation (this feature)

```text
specs/001-cross-family-kernel/
├── plan.md              # This file ($speckit-plan command output)
├── research.md          # Phase 0 output ($speckit-plan command)
├── data-model.md        # Phase 1 output ($speckit-plan command)
├── quickstart.md        # Phase 1 output ($speckit-plan command)
├── contracts/           # Phase 1 output ($speckit-plan command)
└── tasks.md             # Phase 2 output ($speckit-tasks command - NOT created by $speckit-plan)
```

### Source Code (repository root)

```text
isoprax/
├── events.py
├── signals.py
├── commensurability.py
├── kb.py
├── strategies.py
├── baseline_strategies.py
└── evaluation.py
examples/demo_cross_family.py
tests/test_conformance.py
pyproject.toml
.pre-commit-config.yaml
AGENTS.md
CONTRIBUTING.md
LICENSE
```

**Structure Decision**: A single library keeps the contract, persistence, and
evaluation seams explicit; the demo and conformance suite consume only its public API.

## Complexity Tracking

No constitution violations require justification.
