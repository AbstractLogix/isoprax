# Research Decisions: Hermetic Replay Build Qualification

## Decision: content-address the preparation artifact

**Rationale**: The PCFA build-screen pattern bound an exact sample, licence review, and runner identity before compilation. 005 adopts that deterministic provenance mechanic so changed inputs cannot be presented as one measurement.

**Boundary**: No PCFA candidate, sample, container digest, or result is reused as Isoprax evidence.

## Decision: fail closed before compilation on incomplete legal coverage

**Rationale**: Missing historical licence evidence is inconclusive, not permission to compile or proof of an unlicensed revision. Rows remain visible as blocked rather than being dropped.

## Decision: use an injected runner contract

**Rationale**: An immutable image, non-root execution, and writable work storage are runner preconditions. Keeping execution behind an injected boundary makes the evidence reduction deterministic and testable without Docker or network availability.

## Decision: preserve terminal rows and incomplete state

**Rationale**: Build failures and environmental interruptions are evidence. The report cannot calculate a qualification rate until every predeclared revision has a terminal outcome.
