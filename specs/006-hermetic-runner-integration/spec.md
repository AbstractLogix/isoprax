# Feature Specification: Hermetic Runner Integration

**Feature Branch**: `006-hermetic-runner-integration`
**Status**: Draft

## Overview

Connect an approved local/container runner to 005's injected-runner contract without weakening its immutable, non-root, writable-work preconditions. This feature creates execution evidence, not candidate qualification by itself.

## User Scenarios & Testing

### User Story 1 - Execute an approved recipe (Priority: P1)

A reviewer executes an approved build recipe and receives captured exit, timeout, image identity, and artifact evidence per revision.

**Acceptance Scenarios**:

1. **Given** an immutable runner and approved recipe, **When** a revision executes, **Then** all required execution evidence is retained.
2. **Given** an unpinned image, root execution, or non-writable work area, **When** execution is requested, **Then** it is blocked before compilation.

## Requirements

- **FR-001**: MUST verify the runner identity against a digest and record it with every row.
- **FR-002**: MUST execute non-root with an isolated writable work area and read-only source input.
- **FR-003**: MUST enforce predeclared command, timeout, and resource limits.
- **FR-004**: MUST map unavailable infrastructure to `blocked-before-compilation` and build/process failures to `censored`.
- **FR-005**: MUST not fetch mutable dependencies or alter the predeclared recipe during execution.

## Success Criteria

- **SC-001**: Every executed row records runner identity, command, exit disposition, and evidence reference.
- **SC-002**: Unsafe runner configurations cause zero compilation invocations in tests.

## Assumptions

- The candidate, recipe, legal coverage, and sample were qualified under 003–005.

## Out of Scope

- Workload execution, telemetry capture, corpus assembly, and conformance claims.
