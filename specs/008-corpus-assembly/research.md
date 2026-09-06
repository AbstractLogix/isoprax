# Research: Replay Corpus Assembly

## Decision: retain the existing admission gate as the sole admission authority

**Rationale**: Feature 002 owns admission decisions and reports. Assembly must prepare compatible rows and rejection evidence without duplicating or weakening those gates.

**Alternatives considered**:

- Run admission automatically: rejected because assembly must not emit an admission decision.
- Copy admission rules into a second module: rejected because duplicated governance can drift.

## Decision: require a frozen explicit assembly profile

**Rationale**: System boundary, splits, field allowlists, score-time timestamps, horizon, threshold, and release scope must be fixed before rows are reduced.

**Alternatives considered**:

- Infer metadata from capture records: rejected because inference cannot establish predeclaration.
- Permit profile changes while assembling: rejected because it enables post-outcome tuning.

## Decision: return explicit rejections rather than dropping bad captures

**Rationale**: A corpus report must distinguish accepted rows from invalid or unavailable evidence and preserve censoring honestly.

**Alternatives considered**:

- Silently skip invalid inputs: rejected because it conceals selection bias.
- Turn rejected inputs into censored rows: rejected because a rejected input is not a valid corpus row.

## Decision: derive rows from capture identities and change groups

**Rationale**: Capture records already bind source execution, deployment, and observation. The source change becomes the required change group, preserving downstream clustering controls.

**Alternatives considered**:

- Generate unrelated row IDs: rejected because lineage would not be independently reproducible.
