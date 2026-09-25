# Kernel CLI Contract v1

## Transport

The executable reads UTF-8 JSON Lines from standard input. Each non-empty line is one request and produces exactly one JSON Lines response on standard output. Diagnostics go to standard error. The process can handle multiple requests without retaining evidence between lines. Request-level errors are returned in the response and do not change process exit status.

Every request has version: 1 and an operation field. Unsupported versions/operations and malformed transport return a stable categorized error object; the line-oriented process continues to the next request.

## Operations

### identity

Request: {"version":1,"operation":"identity","value":<JSON>}

Response: {"version":1,"canonical":"<RFC 8785 JSON>","sha256":"<lowercase hex>"}. The digest is over the UTF-8 bytes of the canonical string.

### commensurability

Request includes left, right, and optional attestation or bridge records.

Response includes level, commensurable, pooling_allowed, differing_fields, and stable reason_code. Omitted evidence cannot promote a bridgeable result. A valid bridge permits the existing labeled bridgeable pooling path but never changes the level to direct/attested or commensurable=true.

Direct matches return before attestation validation, matching the existing Python short-circuit. For mismatches, attestation validation precedes bridge classification; valid attestation may upgrade window/threshold-only mismatch to attested, while event/process differences remain irreducible.

The library also exposes opaque `AttestationEvidence` and `BridgeEvidence` values through smart constructors. `checkCommensurabilityWithEvidence` accepts only those validated values. The CLI converts JSON into those types at the boundary. `authorizePooledComparison` requires opaque pooling evidence and calibrated evidence for both named definitions; compile-fail examples cover omitted and forged evidence.

### calibration

Request includes scores, outcomes, and optional min_events, n_bins, and max_ece. Response contains sample count, ECE, pass status, and a stable reason code. The thresholds are request parameters and are not repeated in the response. Defaults match Isoprax: 500 events, 10 equal-width bins, ECE <= 0.05, two outcome classes, non-zero score variance, and defined finite AUC.

### admission

Request includes only the two selected gates: rows, fitted_row_ids, gated_row_ids, provenance, and predeclaration. The response reports each gate separately. It does not claim full corpus admission.

### conformance

Request contains left, right, optional commensurability evidence, left/right score/outcome vectors, and calibration parameters. Response is the normalized subset of Python cross_family_report: commensurability, level, poolability, left/right calibration flags, and exact declarable_class. This is a Stage 0 Structural report only.

## Normalized differential projection

Differential tests compare operation status and all decision fields above. Calibration floating-point ECE values are compared within 1e-12; identity canonical bytes and digest compare exactly. Human-readable Python reason strings map to a fixed stable reason code by the adapter. Error responses compare by category. The typed API protects Haskell callers; the JSON CLI still validates every request at runtime, and Python receives no Haskell proof object.

## Stable errors

Categories: invalid_json, duplicate_key, unsupported_version, unknown_operation, invalid_outcome_definition, invalid_evidence, invalid_calibration_input, invalid_admission_input, invalid_identity_value. Error messages may add diagnostic detail but clients key on category.
