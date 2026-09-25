from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from isoprax.admission import (
    AdmissionProfile,
    CalibrationEvidence,
    CorpusProvenance,
    CorpusRow,
    PredeclarationEvidence,
    SplitDefinition,
    _gate_calibration_evidence,
    _gate_provenance_and_predeclaration,
)
from isoprax.commensurability import (
    Attestation,
    OutcomeDefinition,
    check_commensurable,
)
from isoprax.evaluation import check_calibration_conformance, cross_family_report
from isoprax.identity import canonical_json, content_hash


@dataclass(frozen=True)
class OracleError(Exception):
    category: str


def _strict_definition(raw: Any) -> OutcomeDefinition:
    if not isinstance(raw, dict):
        raise OracleError("invalid_outcome_definition")
    if set(raw) - {
        "id",
        "event",
        "observation_process",
        "window",
        "thresholds",
        "description",
    }:
        raise OracleError("invalid_outcome_definition")
    for field in ("id", "event"):
        if not isinstance(raw.get(field), str) or not raw[field].strip():
            raise OracleError("invalid_outcome_definition")
    process = raw.get("observation_process")
    window = raw.get("window")
    if not isinstance(process, dict) or set(process) - {"kind", "parameters", "raw"}:
        raise OracleError("invalid_outcome_definition")
    if not isinstance(process.get("kind"), str) or not process["kind"].strip():
        raise OracleError("invalid_outcome_definition")
    params = process.get("parameters", {})
    if not isinstance(params, dict) or any(
        not isinstance(k, str) or not isinstance(v, str) for k, v in params.items()
    ):
        raise OracleError("invalid_outcome_definition")
    if "raw" in process and not isinstance(process["raw"], str):
        raise OracleError("invalid_outcome_definition")
    if not isinstance(window, dict) or set(window) - {
        "duration",
        "unit",
        "anchor",
        "raw",
    }:
        raise OracleError("invalid_outcome_definition")
    if not all(
        isinstance(window.get(k), str) and window[k].strip() for k in ("unit", "anchor")
    ):
        raise OracleError("invalid_outcome_definition")
    duration = window.get("duration")
    if duration is not None and (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(float(duration))
        or duration < 0
    ):
        raise OracleError("invalid_outcome_definition")
    if "raw" in window and not isinstance(window["raw"], str):
        raise OracleError("invalid_outcome_definition")
    thresholds = raw.get("thresholds", [])
    if not isinstance(thresholds, list):
        raise OracleError("invalid_outcome_definition")
    for item in thresholds:
        if not isinstance(item, dict) or set(item) - {
            "metric",
            "operator",
            "value",
            "sustain",
            "sustain_unit",
            "raw",
        }:
            raise OracleError("invalid_outcome_definition")
        if not isinstance(item.get("metric"), str) or not item["metric"].strip():
            raise OracleError("invalid_outcome_definition")
        if not isinstance(item.get("operator"), str) or not item["operator"].strip():
            raise OracleError("invalid_outcome_definition")
        value = item.get("value")
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (str, int, float))
            or (isinstance(value, float) and not math.isfinite(value))
        ):
            raise OracleError("invalid_outcome_definition")
        sustain = item.get("sustain")
        if sustain is not None and (
            isinstance(sustain, bool)
            or not isinstance(sustain, (int, float))
            or not math.isfinite(float(sustain))
            or sustain < 0
        ):
            raise OracleError("invalid_outcome_definition")
    return OutcomeDefinition(
        id=raw["id"],
        event=raw["event"],
        observation_process=process,
        window=window,
        thresholds=thresholds,
        description=raw.get("description", ""),
    )


def _attestation(raw: Any) -> Attestation | None:
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) != {
        "attestor",
        "justification",
        "left_definition_id",
        "right_definition_id",
        "provenance",
    }:
        raise OracleError("invalid_evidence")
    if any(not isinstance(value, str) or not value.strip() for value in raw.values()):
        raise OracleError("invalid_evidence")
    return Attestation(**raw)


def _bridge(raw: Any, left: OutcomeDefinition, right: OutcomeDefinition) -> bool:
    if raw is None:
        return False
    required = {
        "left_definition_id",
        "right_definition_id",
        "transformation_id",
        "retained_observation_manifest",
        "provenance_reference",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        raise OracleError("invalid_evidence")
    if any(not isinstance(value, str) or not value.strip() for value in raw.values()):
        raise OracleError("invalid_evidence")
    endpoints = {raw["left_definition_id"], raw["right_definition_id"]}
    if endpoints != {left.id, right.id}:
        raise OracleError("invalid_evidence")
    return True


def _decision_projection(
    left: OutcomeDefinition,
    right: OutcomeDefinition,
    attestation: Attestation | None,
    bridge: Any,
) -> dict[str, Any]:
    try:
        base = check_commensurable(left, right, attestation=attestation)
    except ValueError as error:
        if "attestation" in str(error):
            raise OracleError("invalid_evidence") from None
        raise
    retained = False
    if base.level == "bridgeable" and bridge is not None:
        retained = _bridge(bridge, left, right)
        base = check_commensurable(
            left, right, attestation=attestation, retained_observations=retained
        )
    if base.level == "direct":
        reason = "same_structured_definition"
    elif base.level == "attested":
        reason = "attested_equivalent_definitions"
    elif base.level == "bridgeable":
        reason = (
            "bridgeable_with_explicit_evidence"
            if base.pooling_allowed
            else "bridge_evidence_missing"
        )
    else:
        reason = "event_or_observation_process_mismatch"
    return {
        "level": base.level,
        "commensurable": base.commensurable,
        "pooling_allowed": base.pooling_allowed,
        "differing_fields": sorted(
            base.differing_fields,
            key=("event", "observation_process", "window", "thresholds").index,
        ),
        "reason_code": reason,
    }


def _calibration_json(
    definition_id: str,
    scores: list[float],
    outcomes: list[int],
    request: dict[str, Any],
) -> tuple[Any, dict[str, Any]]:
    result = check_calibration_conformance(
        scores,
        outcomes,
        min_events=request.get("min_events", 500),
        n_bins=request.get("n_bins", 10),
        max_ece=request.get("max_ece", 0.05),
    )
    reason = result.reason
    if result.passes:
        reason_code = "calibrated"
    elif reason.startswith("insufficient labeled events"):
        reason_code = "insufficient_labeled_events"
    elif reason.startswith("only one observed outcome class"):
        reason_code = "single_outcome_class"
    elif reason.startswith("ECE"):
        reason_code = "ece_exceeds_threshold"
    elif "degenerate or unavailable" in reason:
        reason_code = "degenerate_discrimination"
    else:
        reason_code = "calibrated"
    return result, {
        "calibrated": result.passes,
        "ece": result.ece,
        "sample_count": result.n_events,
        "reason_code": reason_code,
    }


def _gate_reason(message: str, passed: bool, kind: str) -> str:
    if passed:
        return (
            "calibration_split_separated"
            if kind == "calibration"
            else "provenance_predeclaration_passed"
        )
    if kind == "calibration":
        if "calibration-fit and calibration-gate evidence are required" in message:
            return "calibration_evidence_required"
        if "unknown rows" in message:
            return "unknown_calibration_rows"
        if "fitting must use" in message:
            return "calibration_fit_gate_overlap_or_split_mismatch"
    if "corpus provenance is required" in message:
        return "corpus_provenance_required"
    if "anchored predeclaration evidence is required" in message:
        return "anchored_predeclaration_required"
    if "forbidden" in message:
        return "private_or_privileged_provenance"
    if "hash and external anchor" in message:
        return "predeclaration_hash_and_anchor_required"
    if "must precede" in message:
        return "predeclaration_not_before_collection"
    if "timestamps must be valid" in message:
        return "invalid_predeclaration_timestamp"
    return "provenance_predeclaration_failed"


def _admission(request: dict[str, Any]) -> dict[str, Any]:
    rows: list[CorpusRow] = []
    for raw in request.get("rows", []):
        if not isinstance(raw, dict) or set(raw) != {"row_id", "split"}:
            raise OracleError("invalid_admission_input")
        rows.append(
            CorpusRow(
                row_id=raw["row_id"],
                system_id="fixture",
                change_id="change",
                deployment_id="deployment",
                observation_id="observation",
                split=raw["split"],
                score_time="2024-01-01T00:00:00Z",
                outcome_class="observed_positive",
                prediction_fields={},
                linkage_bases=("commit_hash",),
                outcome_window_complete=True,
                horizon_rule_used="fixture",
                threshold_version="v1",
            )
        )
    fit = request.get("fitted_row_ids", [])
    gate = request.get("gated_row_ids", [])
    if not isinstance(fit, list) or not isinstance(gate, list):
        raise OracleError("invalid_admission_input")
    calibration = (
        CalibrationEvidence(tuple(fit), tuple(gate))
        if "fitted_row_ids" in request or "gated_row_ids" in request
        else None
    )
    provenance_raw = request.get("provenance")
    provenance = None if provenance_raw is None else CorpusProvenance(**provenance_raw)
    predecl_raw = request.get("predeclaration")
    predeclaration = (
        None
        if predecl_raw is None
        else PredeclarationEvidence(
            artifact_hash=predecl_raw["artifact_hash"],
            external_anchor_reference=predecl_raw["external_anchor_reference"],
            predeclared_at=predecl_raw["predeclared_at"],
            corpus_collection_started_at=predecl_raw["corpus_collection_started_at"],
        )
    )
    splits = (
        SplitDefinition("train", "2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z"),
        SplitDefinition(
            "calibration_fit", "2021-01-01T00:00:00Z", "2022-01-01T00:00:00Z"
        ),
        SplitDefinition(
            "calibration_gate", "2022-01-01T00:00:00Z", "2023-01-01T00:00:00Z"
        ),
        SplitDefinition("test", "2023-01-01T00:00:00Z", "2024-01-01T00:00:00Z"),
    )
    profile = AdmissionProfile(
        allowed_prediction_fields=frozenset(),
        forbidden_prediction_fields=frozenset(),
        horizon_rule="fixture",
        horizon_frozen=True,
        adequacy_min_positives=0,
        adequacy_min_negatives=0,
        split_definitions=splits,
        release_scope="fixture",
        thresholds_frozen=True,
        calibration_evidence=calibration,
        predeclaration_evidence=predeclaration,
        corpus_provenance=provenance,
    )
    calibration_gate = _gate_calibration_evidence(rows, profile)
    provenance_gate = _gate_provenance_and_predeclaration(profile)
    return {
        "calibration_evidence": {
            "passed": calibration_gate.passed,
            "reason_code": _gate_reason(
                calibration_gate.message, calibration_gate.passed, "calibration"
            ),
        },
        "provenance_predeclaration": {
            "passed": provenance_gate.passed,
            "reason_code": _gate_reason(
                provenance_gate.message, provenance_gate.passed, "provenance"
            ),
        },
    }


def python_reference(request: dict[str, Any]) -> dict[str, Any]:
    operation = request.get("operation")
    try:
        if request.get("version") != 1:
            raise OracleError("unsupported_version")
        if operation == "identity":
            value = request["value"]
            return {"canonical": canonical_json(value), "sha256": content_hash(value)}
        if operation == "commensurability":
            left = _strict_definition(request["left"])
            right = _strict_definition(request["right"])
            return _decision_projection(
                left,
                right,
                _attestation(request.get("attestation")),
                request.get("bridge"),
            )
        if operation == "calibration":
            _, result = _calibration_json(
                request["definition_id"],
                request["scores"],
                request["outcomes"],
                request,
            )
            return {"calibration": result}
        if operation == "admission":
            return _admission(request)
        if operation == "conformance":
            left = _strict_definition(request["left"])
            right = _strict_definition(request["right"])
            attestation = _attestation(request.get("attestation"))
            decision = _decision_projection(
                left, right, attestation, request.get("bridge")
            )
            left_result, left_cal = _calibration_json(
                left.id, request["left_scores"], request["left_outcomes"], request
            )
            right_result, right_cal = _calibration_json(
                right.id, request["right_scores"], request["right_outcomes"], request
            )
            bridge_present = (
                decision["level"] == "bridgeable" and decision["pooling_allowed"]
            )
            report = cross_family_report(
                "left",
                left,
                request["left_scores"],
                request["left_outcomes"],
                "right",
                right,
                request["right_scores"],
                request["right_outcomes"],
                attestation=attestation,
                retained_observations=bridge_present,
                min_events=request.get("min_events", 500),
                n_bins=request.get("n_bins", 10),
                max_ece=request.get("max_ece", 0.05),
            )
            return {
                "commensurability": decision,
                "left_calibration": left_cal,
                "right_calibration": right_cal,
                "pooled_ece": report.pooled_ece,
                "declarable_class": report.declarable_class,
            }
        raise OracleError("unknown_operation")
    except OracleError:
        raise
    except (KeyError, TypeError, ValueError, OverflowError, IndexError):
        category = {
            "identity": "invalid_identity_value",
            "commensurability": "invalid_outcome_definition",
            "calibration": "invalid_calibration_input",
            "admission": "invalid_admission_input",
            "conformance": "invalid_calibration_input",
        }.get(operation, "unknown_operation")
        raise OracleError(category) from None
