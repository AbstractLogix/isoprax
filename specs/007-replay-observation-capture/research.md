# Research: Replay Observation Capture

## Decision: use one injected replay-capture backend

**Rationale**: Deployment and telemetry are external effects, while the feature must remain deterministic, offline by default, and independent of a deployment platform. A backend can report deployment and observation facts; the core independently validates them against the frozen lane definition and creates the terminal record.

**Alternatives considered**:

- Select a container, orchestration, or telemetry product: rejected because the specification expressly leaves infrastructure selection out of scope.
- Let callers provide a pre-reduced outcome without deployment facts: rejected because it cannot prove the required execution-to-deployment-to-observation lineage.

## Decision: bind capture eligibility to successful execution plus qualified preparation

**Rationale**: Feature 005 owns prepared-sample and qualification evidence, and feature 006 owns containment and execution evidence. A captured observed outcome is valid only when the execution record is successful, its commit/preparation match the frozen lane, and the associated qualification report is qualified. Other upstream states remain retained censored lanes.

**Alternatives considered**:

- Accept every execution record: rejected because build failure or censored execution cannot support attributable deployment.
- Re-run or substitute another revision: rejected because substitution violates the frozen one-revision lane.

## Decision: classify every terminal lane as observed-positive, observed-negative, or censored

**Rationale**: This is the exact Stage 1 outcome vocabulary. A complete attributable window is necessary before applying the predeclared threshold; build/deployment failures, attribution loss, unavailable/incomplete/invalid telemetry, and scope violations are censored, never observed-negative.

**Alternatives considered**:

- Add a fourth blocked status: rejected for the terminal capture record because feature 002 accepts the three outcome classes. Pre-observation blockers are preserved as censored records with explicit reasons.
- Drop unusable lanes: rejected because missingness would bias later evidence and violates the one-terminal-record requirement.

## Decision: content-identify retained observation artifacts and record unavailable states

**Rationale**: SHA-256 and byte counts provide storage-agnostic immutable references. Explicit `missing` and `unreadable` states preserve the difference between unavailable evidence and a negative outcome.

**Alternatives considered**:

- Retain raw telemetry by default: rejected because it risks private/privileged data exposure and is not necessary to establish an evidence identity.
- Retain only artifact paths: rejected because a path does not identify content or prove collection.

## Decision: make all material definition and lineage fields part of lane identity

**Rationale**: The lane must not silently merge an altered revision, service, workload, horizon, threshold, schema, release scope, qualification report, or execution evidence. Canonical serialization and SHA-256 match the project’s existing deterministic evidence pattern.

**Alternatives considered**:

- Use generated identifiers or timestamps: rejected because they cannot demonstrate reproducibility for equivalent frozen inputs.
