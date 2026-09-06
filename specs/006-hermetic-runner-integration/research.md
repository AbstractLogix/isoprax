# Research: Hermetic Runner Integration

## Decision: retain an injected backend rather than select a container engine

**Rationale**: Feature 005 already defines an injected runner boundary and the feature specification explicitly excludes engine provisioning. An injected backend keeps subprocess/container effects outside the deterministic core while allowing a future approved adapter to report its effective controls.

**Alternatives considered**:

- Add Docker or Podman integration: rejected because it would select and depend on environment infrastructure not specified by the feature.
- Invoke a local shell directly: rejected because it cannot truthfully prove a digest-pinned image, non-root identity, read-only source, isolated work area, or disabled network.

## Decision: fail closed on asserted or unverifiable controls

**Rationale**: An evidence record is useful only when it identifies the effective controls. Configurations with missing, mutable, or unapplied controls must be blocked before command start rather than treated as best effort.

**Alternatives considered**:

- Record a warning and run: rejected because it would produce misleading build evidence and violate FR-002/FR-003.

## Decision: content-identify artifacts at collection time

**Rationale**: A SHA-256 over collected bytes gives a stable, storage-agnostic reference. Explicit collection states preserve missing/unreadable evidence.

**Alternatives considered**:

- Retain only paths: rejected because a path neither identifies contents nor proves collection.
- Treat missing declared artifacts as a build failure automatically: rejected because the observed process disposition and artifact-collection outcome are distinct facts.
