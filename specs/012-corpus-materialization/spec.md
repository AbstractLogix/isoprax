# Feature Specification: Reproducible Public Corpus Materialization

**Feature Branch**: `012-corpus-materialization`
**Status**: Draft

## Overview

Materialize a reviewable, public-only corpus artifact from accepted assembly
records and their safe evidence references. The artifact makes exact inputs,
withheld material, checksums, and deterministic ordering inspectable without
adding new labels, changing outcomes, or admitting the corpus.

## User Scenarios & Testing

### User Story 1 - Reproduce a public corpus artifact (Priority: P1)

A reviewer can reproduce the canonical artifact and confirm which evidence was
included, withheld, unavailable, or censored.

**Acceptance Scenarios**:

1. Equivalent accepted evidence yields identical artifact manifests and hashes.
2. Censored/unavailable inputs remain explicitly represented without invented
   outcome data.
3. Private, privileged, profile-mismatched, or unsafe payload material is
   rejected.

## Requirements

- **FR-001**: Consume only accepted assembly evidence and safe public capture
  references under one frozen profile.
- **FR-002**: Produce deterministic ordering, artifact hashes, inclusion and
  withholding inventories, and a fixed evidence-only claim boundary.
- **FR-003**: Preserve original score-time fields, outcome classes, censoring,
  split assignments, and change clustering without modification.
- **FR-004**: Reject scope, profile, lineage, provenance, and artifact-integrity
  mismatch; never substitute missing evidence.

## Success Criteria

- **SC-001**: Equivalent valid input yields byte-identical manifests in all
  deterministic tests.
- **SC-002**: Tested restricted or mismatched material never appears in output.

## Out of Scope

- Acquiring data, recalculating outcomes, granting admission, training models,
  external artifact hosting, and conformance claims.
