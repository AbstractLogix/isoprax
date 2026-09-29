# Research: Strongly Typed Python Semantic Core

## Decision: Use mypy strict mode for a declared semantic file set

**Rationale**: The repository supports Python 3.10 through 3.14 and already runs all developer checks through `uv`. mypy is a development-only static checker; adding it to the `dev` group creates no runtime dependency. Strict mode checks signatures, generic use, return paths, and untyped definitions in the selected files, including closed admission gate/split/outcome identifiers.

**Alternatives considered**: Pyright/basedpyright would also provide strong checking, but maintaining multiple checkers adds setup without a demonstrated benefit. Whole-repository strict mode would pull unrelated ML, notebook, and legacy typing gaps into this focused change.

## Decision: Keep raw and normalized representations separate

**Rationale**: JSON and persistence inputs are dynamic and must be validated. The existing `OutcomeDefinition.__post_init__` normalizes values but its field annotations continue to advertise raw unions. Use a constructor whose inputs accept documented legacy forms while its stored fields are annotated only as `ObservationProcess`, `Window`, and `tuple[Threshold, ...]`. Use `object` at genuinely untrusted parser boundaries and narrow it with explicit checks.

**Alternatives considered**: `Any` keeps parsing convenient but lets unvalidated values leak through the semantic model. Requiring callers to pre-normalize all values would break supported constructors and persisted payloads.

## Decision: Use generic evidence tags plus runtime identity binding

**Rationale**: Generic marker types let statically declared outcome families express which calibration and commensurability evidence belongs together. Evidence factories also record and compare concrete definition IDs at runtime. Both layers are needed: Python's type system cannot establish equality of values loaded dynamically.

**Alternatives considered**: Runtime-only booleans are easy to misuse and do not create a type-checking boundary. Making every outcome ID a literal type is impractical for JSON/database-backed definitions and is not available from ordinary runtime parsing.

## Decision: Bind typed authorization to the calibrated sample

**Rationale**: Definition IDs alone do not bind a calibration result to the arrays evaluated later by `authorized_pooled_ece`. The factory now hashes the normalized score/outcome vectors into the sealed calibration evidence; authorization carries both digests, and the evaluator rejects different vectors. The digest establishes input identity, not external provenance.

**Compatibility boundary**: `cross_family_report` remains a high-level facade that computes its commensurability and calibration diagnostics from the same score/outcome vectors it reports. It labels failed calibration as uncalibrated. Direct typed pooled calls require explicit evidence and exact sample identity.

## Decision: Bind evidence to normalized definition semantics and ID

**Rationale**: Definition IDs are caller/persistence identities and can be reused outside `OutcomeDefinitionRegistry`. Evidence therefore records a canonical digest of `OutcomeDefinition.comparison_key()` as well as its ID. Calibration evidence and commensurability evidence must agree on both, and pooled authorization carries both definition digests. The comparison key excludes ID and descriptive text while including normalized event, observation process, window, and thresholds; this binds the semantics that commensurability actually compares.

**Alternatives considered**: Requiring every caller to use `OutcomeDefinitionRegistry` would leave direct typed-evidence callers unprotected. Hashing the full serialized definition would include the ID and description redundantly and could reject definitions that differ only in non-semantic display text.

## Decision: Bind pooled ECE to one calibration policy

**Rationale**: `CalibrationPolicy` records and hashes `min_events`, `n_bins`, and `max_ece`. Each calibration evidence value carries the policy used to qualify it. Authorization requires the same policy on both sides and carries that policy; `authorized_pooled_ece` uses its `n_bins` and does not accept a caller-supplied replacement.

**Alternatives considered**: Keeping an arbitrary `n_bins` argument makes the output metric differ from the metric used to qualify the calibration evidence. Requiring policy equality avoids a pooled claim with two incompatible qualification rules.

## Decision: Keep report pooling explicitly diagnostic

**Rationale**: The report preserves pooled ECE when definitions are directly commensurable even if calibration fails, which supports diagnosis and existing output behavior. This result is not a `PooledComparisonAuthorization`; documentation labels it diagnostic, it uses the same-call input vectors and calibration parameters, and it withholds ECE when definitions are not commensurable. Remove the stale secondary poolability branch because the current result types only permit pooling for direct commensurability.

## Decision: Enforce direct observation parameter invariants

**Rationale**: `ObservationProcess.__post_init__` is the shared invariant boundary for mapping and direct constructors. It validates tuple shape and string members, sorts pairs, and rejects duplicate keys, so a directly constructed value cannot bypass the normalization used by comparison.

## Decision: Fail closed on bridgeable but unre-derived outcomes

**Rationale**: The previous `retained_observations=True` switch let a non-commensurable result set `pooling_allowed=True` without applying any transformation. The authoritative Isoprax v0.3 specification defines commensurability by matching event, observation process, window, and thresholds (§5.6.2) and forbids aggregation of non-commensurable scores (§5.6.3). Retained observations show that a bridge may be possible; they do not establish that both outcome sets have been re-derived under the same definition. Such results remain `bridgeable` and are non-poolable until a future bridge operation validates transformed outcomes against a shared definition.

**Compatibility correction**: The decision payload fields remain stable, but result levels change where prior behavior conflicts with the normative contract. A mismatch with retained observations or a free-text attestation remains non-commensurable and non-poolable; `require_commensurable`, typed authorization, and shared-label pilot construction reject it. These are documented corrections, not implicit conformance upgrades.

## Decision: Preserve the report shape and valid diagnostic behavior

**Rationale**: Keep the `CrossFamilyReport` fields and per-side calibration diagnostics. The report may show pooled ECE as a calibration diagnostic for directly commensurable definitions while separately marking failed calibration; only mechanically established commensurability authorizes aggregation of same-event scores. It withholds pooled ECE for every non-commensurable result.

**Alternatives considered**: Requiring successful calibration before computing ECE would suppress the diagnostic used to explain an uncalibrated result. The typed pooled-comparison API separately requires passing calibration evidence.

## Decision: Treat attestations as provenance, not semantic proof

**Rationale**: The authoritative v0.3 test defines commensurability if and only if event, observation process, window, and thresholds match (§5.6.2). A free-text attestation tied to definition IDs cannot change those fields or prove a transformation; §5.6.3 forbids pooling non-commensurable scores. The decision may retain attestation metadata, but every mismatched definition remains bridgeable or irreducible and non-poolable until outcomes are actually re-derived under one validated definition.

## Decision: Reject unknown semantic keys and lossy calibration labels

**Rationale**: Silently discarding an unknown process, window, or threshold key could make definitions compare equal while omitting part of the event semantics. These mapping boundaries now reject unrecognized keys. Calibration evidence also validates that each outcome is an exact binary integer before normalization and hashing, so fractional values cannot be truncated into apparently valid labels.

## Decision: Validate directly constructed threshold values

**Rationale**: Validating mapping inputs alone leaves a bypass when callers construct a `Threshold` directly; a non-finite value could then enter an `OutcomeDefinition` and be serialized. The threshold value now enforces its invariants at construction, so direct and mapping inputs share one checked representation.

## Decision: Keep a small Haskell oracle in CI only

**Rationale**: Python remains the only runtime implementation, while an independent Haskell oracle gives a separate implementation against which the semantic contract can be checked. The earlier experiment's opaque proof types, QuickCheck properties, compile-fail examples, and differential fixtures exposed real discrepancies. Retain only the small commensurability/calibration authorization seam, its shared fixtures, and generated properties; trigger the Haskell compiler job only for semantic source, contract, oracle, or fixture changes.

**Alternatives considered**: Python-only CI is simpler, while a production Haskell runtime or subprocess would add operational coupling and latency without improving runtime behavior. The selected boundary keeps the independent verification value and avoids runtime coupling, corpus/admission behavior, benchmarks, and unrelated proof types. The semantic workflow runs a lightweight path check on every main PR and performs compiler work only when the relevant paths change, so its check remains successful when skipped.
