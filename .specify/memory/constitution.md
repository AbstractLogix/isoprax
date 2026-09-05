<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles: template placeholders -> five project principles
- Added sections: Contract Boundaries; Development Workflow
- Removed sections: none
- Follow-up TODOs: none
-->
# Isoprax Constitution

## Core Principles

### I. Specification Authority

The published Isoprax specification is the normative source of truth. The implementation MUST reject or explicitly report behavior that contradicts a MUST/MUST NOT clause; examples and prior projects can inform a design but cannot silently redefine the contract.

### II. Honest Conformance

Conformance claims MUST name the supported class, families, event and strategy types, Outcome Definitions, commensurability result, and calibration qualifier. Synthetic or partial evidence MUST NOT be presented as real-data validation, Semantic/Full Conformance, or predictive efficacy.

### III. Contract-First Testing

Every implemented normative rule MUST have a focused automated conformance test traceable to its specification clause. Tests MUST cover rejection paths for malformed or semantically contradictory records, not only happy paths.

### IV. Deterministic Core, Explicit Effects

Event normalization, signal validation, Outcome-Definition commensurability, calibration diagnostics, and conformance decisions MUST be deterministic for explicit inputs. Persistence and external adapters MUST stay behind narrow interfaces; core ingestion and storage MUST NOT require network access.

### V. Minimal Reference Scope

The reference implementation MUST prefer a small, dependency-light slice that proves the cross-family contract. It MUST NOT absorb external replay, corpus-admission, or research-claim mechanisms unless the Isoprax spec later requires them.

## Contract Boundaries

The initial implementation supports the Change and Operational families with one strategy in each, declared Outcome Definitions, a mechanical commensurability check, a shared knowledge-base contract, recorded outcomes, and calibration diagnostics. It is a Stage 0 synthetic proof of Cross-Family Conformance (Structural), not Semantic conformance. Real-data adapters, real-world performance claims, joint reasoning over non-commensurable signals, and automatic action or remediation are out of scope.

## Development Workflow

Complex work MUST use the project-local Spec Kit sequence. Python dependency and execution workflows MUST use uv. Changes MUST preserve unrelated work and be verified with the cheapest focused checks that demonstrate their claim.

## Governance
<!-- Example: Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->

This constitution governs implementation and review. Amendments require a documented rationale, an impact assessment for existing conformance claims, and a semantic version increment: MAJOR for incompatible principle changes, MINOR for new or materially expanded principles, and PATCH for clarifications. Reviews MUST verify relevant principles and record only evidence actually obtained.

**Version**: 1.0.0 | **Ratified**: 2026-09-05 | **Last Amended**: 2026-09-05
