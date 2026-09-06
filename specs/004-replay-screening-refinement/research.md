# Research Decisions: Replay Screening Refinement

## Decision: defer measured historical-build qualification

**Rationale**: A pre-environment build-rate result would measure dependency decay and build tooling rather than a candidate under the future hermetic replay method. Early screening therefore records only a reproducibility predictor.

**Alternative considered**: Require 003 to use the future hermetic method. Rejected because that method belongs to the replay-environment feature and does not yet exist.

## Decision: require governing source-build legal evidence

**Rationale**: Publication restrictions can be outside an OSS licence. The early screen records the instrument that governs the source-built artifact, rather than inferring it from a LICENSE file.

## Decision: use three accepted hermeticity classes

**Rationale**: Pinned distributions, hermetic build systems, and pinned container/toolchain methods are concrete, checkable indicators. A conventional or undocumented build is insufficient for early eligibility.
