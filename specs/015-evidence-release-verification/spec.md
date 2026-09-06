# Feature Specification: Evidence Release Verification

**Feature Branch**: `015-evidence-release-verification`  
**Status**: Draft

## Overview

Verify a proposed public evidence release against its deterministic manifests,
artifact references, report identities, scope policy, and claim boundary before
publication. This is a local verification gate, not a publishing service and
not new empirical evidence.

## User Scenarios & Testing

### User Story 1 - Verify a bounded public release (Priority: P1)

A release reviewer can determine whether a proposed package is complete,
internally consistent, public-only, and honestly scoped before it is published.

**Acceptance Scenarios**:

1. Equivalent valid release inputs produce identical verification results.
2. Missing artifacts, hash mismatches, stale/mismatched manifests, private
   material, or claim-boundary edits fail closed with explicit reasons.
3. A passing verification result states release-integrity evidence only.

## Requirements

- **FR-001**: Validate deterministic linkage among corpus manifest, admission
  report, evidence report, declared public artifacts, and their safe hashes.
- **FR-002**: Require one frozen release scope and reject private, privileged,
  credential-bearing, or undeclared material.
- **FR-003**: Report missing, unreadable, or mismatched artifacts explicitly;
  never infer a valid release from partial inputs.
- **FR-004**: Preserve an immutable claim boundary: release verification does
  not establish corpus admission, model efficacy, Semantic/Full Conformance, or
  cross-family pooling.

## Success Criteria

- **SC-001**: All tested integrity and scope violations fail closed.
- **SC-002**: Equivalent valid releases receive identical verification identity
  and public result.

## Out of Scope

- Uploading/publishing artifacts, credential storage, release automation,
  acquiring evidence, evaluation, or conformance decisions.
