# Feature Specification: Stage 1 Evidence Reporting

**Feature Branch**: `009-evidence-reporting`
**Status**: Draft

## Overview

Publish reproducible, claim-bounded Stage 1 evidence reports from qualified build, replay, corpus, and admission records.

## User Scenarios & Testing

### User Story 1 - Read a bounded evidence report (Priority: P1)

A reader can retrieve hashes, provenance, censoring counts, admission results, and explicit claim limits without raw restricted inputs.

**Acceptance Scenarios**:

1. **Given** admitted corpus evidence, **When** a report is generated, **Then** it identifies published artifacts and withheld inputs.
2. **Given** incomplete or failed gates, **When** a report is generated, **Then** it states blocked/inconclusive rather than a conformance upgrade.

## Requirements

- **FR-001**: MUST report input hashes, predeclaration anchor, runner evidence, censoring, and admission gates.
- **FR-002**: MUST record provenance, freshness, completeness, and unavailable evidence explicitly.
- **FR-003**: MUST publish only the predeclared release scope and exclude private/privileged data.
- **FR-004**: MUST state that build qualification and Stage 1 admission do not alone establish Semantic or Full Conformance.

## Success Criteria

- **SC-001**: Every generated report has a deterministic manifest and explicit claim boundary.

## Out of Scope

- Model claims, cross-family score pooling, or automated remediation.
