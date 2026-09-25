# Data Model: Haskell Reference Semantics Kernel

## KernelRequest

A versioned JSON object with version 1 and one operation. Parsing rejects duplicate keys and malformed wire types before domain evaluation.

Operations: commensurability, calibration, admission, conformance, and identity.

## RawOutcomeDefinition

Fields: id, event, structured observation_process, structured window, thresholds, optional description.

Validation requires non-empty ID/event/process kind/window unit/window anchor, finite non-negative duration when present, well-typed threshold terms, and finite numeric threshold values. Semantic normalization follows Python: event, process kind/raw, window unit/anchor, threshold metric, and sustain unit are trimmed/lowercased where Python does so; parameters are sorted; thresholds are compared unordered. Definition IDs and descriptions are excluded from semantic equality.

## ValidatedOutcomeDefinition

Opaque value created only by the validator. It stores the normalized comparison key and stable definition ID used to bind evidence.

## AttestationEvidence

Fields: attestor, justification, left_definition_id, right_definition_id, and provenance. Every field must be non-empty after trimming, and the endpoint set must match the compared definitions. As in Python, event/process differences remain irreducible.

The public Haskell type is opaque. `parseAttestationEvidence` is its smart constructor.

## BridgeEvidence

Fields: left_definition_id, right_definition_id, transformation_id, retained_observation_manifest, and provenance_reference. Every value must be non-empty and endpoint IDs must bind the compared pair (either orientation).

This is an explicit declared bridge record that maps to Python's retained_observations=True. It does not prove the transformation was executed, correct, or independently reproducible. Missing or mismatched bridge evidence fails closed.

The public Haskell type is opaque. `parseBridgeEvidence` is its smart constructor.

## CommensurabilityDecision

- level: direct, attested, bridgeable, or irreducible.
- commensurable: true only for direct/attested semantics, matching Python.
- pooling_allowed: true for direct/attested and for bridgeable only with a validated bridge record; false for irreducible.
- differing_fields: stable ordered list: event, observation_process, window, thresholds.
- reason_code: stable category, separate from human-readable prose.
- pooling_evidence: optional opaque proof available only when pooling_allowed is true.

## CalibrationInput and CalibratedEvidence

Input contains score values and binary outcomes, optional thresholds (min_events=500, n_bins=10, max_ece=0.05). Validation requires equal lengths, finite scores in [0,1], binary outcomes, and a positive bin count. Calibration passes only when minimum support, both classes, ECE threshold, finite AUC availability (both classes), and non-zero score variance all pass. The Haskell package exposes the qualified result as an opaque value.

## AdmissionEvidence

Contains rows with IDs/split assignments, fitted and gated row IDs, corpus source/private/privileged flags, artifact hash, external anchor reference, predeclaration timestamp, and collection-start timestamp. Only the existing calibration evidence gate and provenance/predeclaration gate are evaluated. Results are independent booleans/messages; they do not imply full Stage 1 admission.

## Stage0ConformanceProjection

Contains the commensurability decision and per-family calibration results and emits the same Stage 0 declarable_class projection as Python cross_family_report. Stage 0 remains Structural. Semantic/Full evaluation is not implemented in this kernel.

## CanonicalIdentity

An arbitrary valid I-JSON value, exact RFC 8785 canonical UTF-8 bytes, and SHA-256 lowercase hexadecimal digest over those bytes. Duplicate object keys, invalid Unicode, unsupported numbers, and non-finite values fail closed.
