# Feature Specification: Replay Observation Capture

**Feature Branch**: `007-replay-observation-capture`
**Status**: Draft

## Overview

For build-qualified revisions, produce deterministic deployment and observation records using a predeclared single-service workload and observation horizon. Failed builds, deployments, and incomplete windows remain censored.

## User Scenarios & Testing

### User Story 1 - Capture one replay lane (Priority: P1)

A reviewer runs one clean revision lane and receives linked change, deployment, and observation evidence.

**Acceptance Scenarios**:

1. **Given** a successful build and complete observation window, **When** the lane completes, **Then** linked source, deployment, and metric evidence is retained.
2. **Given** a build/deployment failure or telemetry gap, **When** the lane completes, **Then** the row is censored with its reason.

## Requirements

- **FR-001**: MUST use one system and one clean revision per lane.
- **FR-002**: MUST freeze workload, horizon, threshold rule, and capture schema before lane execution.
- **FR-003**: MUST record immutable change-to-deployment-to-observation lineage.
- **FR-004**: MUST censor failed builds, deployments, incomplete follow-up, and monitoring gaps.
- **FR-005**: MUST prevent private production data or privileged telemetry from entering capture.

## Success Criteria

- **SC-001**: Every lane produces a lineage-complete observed record or an explicit censor reason.

## Out of Scope

- Cross-system pooling, corpus admission, model fitting, or conformance claims.
