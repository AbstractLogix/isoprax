"""Deterministic action-conditioned latent predictor for the Isoprax PoC.

This module implements the smallest offline reference slice of the attached JEPA
feature.  It has two deterministic encoders and one predictor in representation
space.  The implementation is deliberately dependency-light: it proves the
strategy and provenance contracts, not neural-model efficacy or Semantic/Full
Conformance.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from .commensurability import OutcomeDefinition
from .events import ChangeEvent, RunEvent
from .external_anchor import ExternalAnchorVerification, stage2_statement_payload
from .identity import content_hash
from .signals import AnomalySignal, CalibrationStatus, RiskSignal
from .strategies import AnomalyStrategy, Calibrator, RiskStrategy

_TOKEN_RE = re.compile(r"[a-z0-9_./-]+")
_CLAIM_BOUNDARY = (
    "JEPA reference evidence only; Structural conformance is the default. "
    "Calibration, shared code, and synthetic latent-loss evidence do not establish "
    "Semantic or Full Conformance or predictive efficacy."
)

JEPA_DEFECT_RISK = OutcomeDefinition(
    id="jepa.change_defect_risk.v1",
    event="change is followed by a defect-inducing operational state transition",
    observation_process="deterministic replay telemetry threshold process",
    window="predeclared post-change observation window",
    thresholds="declared operational failure threshold",
    description="JEPA change-family readout; PoC evidence only.",
)

JEPA_OPERATIONAL_FAILURE = OutcomeDefinition(
    id="jepa.operational_failure.v1",
    event="operational run crosses the declared failure threshold",
    observation_process="deterministic replay telemetry threshold process",
    window="predeclared operational observation window",
    thresholds="declared operational failure threshold",
    description="JEPA operational-family readout; PoC evidence only.",
)


def _copy_evidence_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _copy_evidence_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(_copy_evidence_value(item) for item in value)
    return value


def _freeze_evidence_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_evidence_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_evidence_value(item) for item in value)
    return value


def _thaw_evidence_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_evidence_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_evidence_value(item) for item in value]
    return value


def _state_array(value: Sequence[Sequence[float]], name: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a rectangular numeric window") from error
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] == 0:
        raise ValueError(f"{name} must be a non-empty two-dimensional window")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def _window_tuple(
    value: Sequence[Sequence[float]], name: str
) -> tuple[tuple[float, ...], ...]:
    array = _state_array(value, name)
    return tuple(tuple(float(item) for item in row) for row in array)


def state_feature_vector(window: Sequence[Sequence[float]]) -> np.ndarray:
    """Return the deterministic summary consumed by JEPA state encoders."""
    array = _state_array(window, "state")
    first = array[0]
    last = array[-1]
    mean = array.mean(axis=0)
    spread = array.std(axis=0)
    slope = (last - first) / max(array.shape[0] - 1, 1)
    return np.concatenate((mean, spread, first, last, slope))


def _stable_seed(seed: str, suffix: str) -> int:
    digest = hashlib.sha256(f"{seed}:{suffix}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False) % (2**32)


def _projection(seed: str, rows: int, columns: int) -> np.ndarray:
    generator = np.random.default_rng(
        _stable_seed(seed, f"projection:{rows}:{columns}")
    )
    matrix = generator.standard_normal((rows, columns))
    return matrix / math.sqrt(float(rows))


@dataclass(frozen=True)
class JEPABackendConfig:
    """Configuration included in the deterministic backend identity."""

    change_embedding_dim: int = 32
    state_embedding_dim: int = 8
    ridge_lambda: float = 1e-3
    hash_seed: str = "isoprax-jepa-v1"

    def __post_init__(self) -> None:
        if self.change_embedding_dim < 2 or self.state_embedding_dim < 2:
            raise ValueError("embedding dimensions must be at least 2")
        if not math.isfinite(self.ridge_lambda) or self.ridge_lambda <= 0:
            raise ValueError("ridge_lambda must be finite and greater than zero")
        if not self.hash_seed.strip():
            raise ValueError("hash_seed must be non-empty")


@dataclass(frozen=True)
class JEPATrainingPair:
    """One unlabeled change and pre/post state trajectory pair."""

    change: ChangeEvent
    pre_state: tuple[tuple[float, ...], ...] | Sequence[Sequence[float]]
    post_state: tuple[tuple[float, ...], ...] | Sequence[Sequence[float]]

    def __post_init__(self) -> None:
        if not isinstance(self.change, ChangeEvent):
            raise ValueError("change must be a ChangeEvent")
        pre = _state_array(self.pre_state, "pre_state")
        post = _state_array(self.post_state, "post_state")
        if pre.shape[1] != post.shape[1]:
            raise ValueError("pre_state and post_state must have the same width")
        object.__setattr__(self, "pre_state", _window_tuple(pre, "pre_state"))
        object.__setattr__(self, "post_state", _window_tuple(post, "post_state"))


@dataclass(frozen=True)
class JEPATrainingReport:
    pair_count: int
    state_input_dim: int
    change_embedding_dim: int
    state_embedding_dim: int
    mean_latent_prediction_error: float
    backend_identity: str
    state_representation_identity: str
    claim_boundary: str = _CLAIM_BOUNDARY

    def __post_init__(self) -> None:
        if self.pair_count < 2:
            raise ValueError("pair_count must be at least 2")
        if not math.isfinite(self.mean_latent_prediction_error):
            raise ValueError("mean_latent_prediction_error must be finite")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceProvenance:
    """Digest-backed provenance bound to an externally verified anchor."""

    payload: Mapping[str, Any]
    digest: str
    verification: ExternalAnchorVerification | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.payload, Mapping) or not self.payload:
            raise ValueError("evidence provenance payload is required")
        payload = _copy_evidence_value(self.payload)
        if any(not isinstance(key, str) or not key.strip() for key in payload):
            raise ValueError("evidence provenance keys must be non-empty strings")
        required_keys = {
            "corpus_identity",
            "split_identity",
            "label_definition_identity",
            "outcome_definition_ids",
            "predeclaration_commit",
        }
        if not required_keys.issubset(payload):
            raise ValueError(
                "evidence provenance must identify corpus, split, labels, outcomes, "
                "and predeclaration"
            )
        for key in (
            "corpus_identity",
            "split_identity",
            "label_definition_identity",
            "predeclaration_commit",
        ):
            value = payload[key]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"evidence provenance {key} must be a non-empty string"
                )
        outcome_ids = payload["outcome_definition_ids"]
        if isinstance(outcome_ids, (str, bytes)) or not isinstance(
            outcome_ids, Sequence
        ):
            raise ValueError(
                "evidence provenance outcome_definition_ids must be a sequence"
            )
        normalized_outcome_ids = tuple(outcome_ids)
        if not normalized_outcome_ids or any(
            not isinstance(value, str) or not value.strip()
            for value in normalized_outcome_ids
        ):
            raise ValueError(
                "evidence provenance outcome_definition_ids must contain non-empty strings"
            )
        if len(set(normalized_outcome_ids)) != len(normalized_outcome_ids):
            raise ValueError(
                "evidence provenance outcome_definition_ids must be unique"
            )
        payload["outcome_definition_ids"] = normalized_outcome_ids
        if not isinstance(self.digest, str) or not self.digest.strip():
            raise ValueError("evidence provenance digest is required")
        if content_hash(payload) != self.digest:
            raise ValueError("evidence provenance digest does not match its payload")
        if self.verification is not None and not isinstance(
            self.verification, ExternalAnchorVerification
        ):
            raise ValueError(
                "evidence provenance verification must be an external anchor result"
            )
        if (
            self.verification is not None
            and self.verification.status == "verified"
            and not self.verification.verifier_authenticated
        ):
            raise ValueError(
                "verified evidence provenance must come from the external verifier"
            )
        if (
            self.verification is not None
            and self.verification.status == "verified"
            and not self.verification.verified
        ):
            raise ValueError(
                "verified evidence provenance anchor does not bind its statement"
            )
        if self.verification is not None and self.verification.verified:
            if (
                not isinstance(self.verification.anchor_type, str)
                or not self.verification.anchor_type.strip()
            ):
                raise ValueError("verified evidence provenance requires an anchor type")
            if self.verification.anchor_type != "sigstore_rekor_dsse":
                raise ValueError("evidence provenance anchor type is not supported")
            if (
                not isinstance(self.verification.anchor_reference, str)
                or not self.verification.anchor_reference.strip()
            ):
                raise ValueError(
                    "verified evidence provenance requires an anchor reference"
                )
            if (
                not isinstance(self.verification.signer_identity, str)
                or not self.verification.signer_identity.strip()
            ):
                raise ValueError(
                    "verified evidence provenance requires a signer identity"
                )
            expected_statement = stage2_statement_payload(
                self.digest, payload["predeclaration_commit"]
            )
            if (
                not isinstance(self.verification.verified_statement, Mapping)
                or dict(self.verification.verified_statement) != expected_statement
            ):
                raise ValueError(
                    "verified evidence provenance anchor does not bind its digest"
                )
        object.__setattr__(self, "payload", _freeze_evidence_value(payload))

    @property
    def verified(self) -> bool:
        """Whether an external verifier supplied a binding verified anchor."""
        if self.verification is None or not self.verification.verified:
            return False
        statement = self.verification.verified_statement
        return isinstance(statement, Mapping) and dict(
            statement
        ) == stage2_statement_payload(
            self.digest, self.payload["predeclaration_commit"]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload": _thaw_evidence_value(self.payload),
            "digest": self.digest,
            "verification": (
                self.verification.to_dict() if self.verification is not None else None
            ),
        }


@dataclass(frozen=True)
class JEPASemanticEvidence:
    """Evaluation evidence required before a Semantic status can be reported."""

    backend_identity: str
    state_representation_identity: str
    non_decomposable: bool
    jit_scores: tuple[float, ...]
    aiops_scores: tuple[float, ...]
    sample_count: int
    shared_representation_proof: str = ""
    evidence_class: str = "synthetic"
    provenance: EvidenceProvenance | None = None

    def __post_init__(self) -> None:
        if (
            not self.backend_identity.strip()
            or not self.state_representation_identity.strip()
        ):
            raise ValueError(
                "semantic evidence must identify the backend and representation"
            )
        if not self.shared_representation_proof.strip():
            raise ValueError(
                "semantic evidence must include a shared representation proof"
            )
        if self.evidence_class not in {"synthetic", "real_labeled"}:
            raise ValueError("evidence_class must be synthetic or real_labeled")
        if self.provenance is not None and not isinstance(
            self.provenance, EvidenceProvenance
        ):
            raise ValueError("provenance must be an EvidenceProvenance")
        if not isinstance(self.non_decomposable, bool):
            raise ValueError("non_decomposable must be boolean evidence")
        jit = tuple(float(value) for value in self.jit_scores)
        aiops = tuple(float(value) for value in self.aiops_scores)
        object.__setattr__(self, "jit_scores", jit)
        object.__setattr__(self, "aiops_scores", aiops)
        if (
            self.sample_count < 2
            or len(jit) != self.sample_count
            or len(aiops) != self.sample_count
        ):
            raise ValueError(
                "semantic evidence sample_count must match at least two scores per readout"
            )
        if any(
            not math.isfinite(value) or not 0.0 <= value <= 1.0
            for value in (*jit, *aiops)
        ):
            raise ValueError("semantic evidence scores must be finite probabilities")


@dataclass(frozen=True)
class JEPAAssessment:
    tier: str
    backend_identity: str
    state_representation_identity: str
    reasons: tuple[str, ...]
    claim_boundary: str = _CLAIM_BOUNDARY
    families: tuple[str, ...] = ("change", "operational")
    event_types: tuple[str, ...] = ("ChangeEvent", "RunEvent")
    strategy_types: tuple[str, ...] = ("RiskStrategy", "AnomalyStrategy")
    outcome_definition_ids: tuple[str, ...] = (
        JEPA_DEFECT_RISK.id,
        JEPA_OPERATIONAL_FAILURE.id,
    )
    commensurability: str = "non-commensurable; pooled score withheld"
    calibration_qualifier: str = (
        "readouts may be independently calibrated; calibration does not upgrade tier"
    )

    @property
    def declarable_class(self) -> str:
        return f"Cross-Family Conformance ({self.tier})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "backend_identity": self.backend_identity,
            "state_representation_identity": self.state_representation_identity,
            "reasons": list(self.reasons),
            "declarable_class": self.declarable_class,
            "claim_boundary": self.claim_boundary,
            "families": list(self.families),
            "event_types": list(self.event_types),
            "strategy_types": list(self.strategy_types),
            "outcome_definition_ids": list(self.outcome_definition_ids),
            "commensurability": self.commensurability,
            "calibration_qualifier": self.calibration_qualifier,
        }


def _semantic_evidence_gate_reasons(
    evidence: JEPASemanticEvidence,
) -> list[str]:
    reasons: list[str] = []
    if evidence.evidence_class != "real_labeled":
        reasons.append(
            "semantic evidence is synthetic; real labeled evidence is required"
        )
    elif evidence.provenance is None:
        reasons.append("semantic evidence lacks a provenance artifact")
    elif not evidence.provenance.verified:
        reasons.append("semantic evidence provenance is not externally verified")
    elif set(evidence.provenance.payload["outcome_definition_ids"]) != {
        JEPA_DEFECT_RISK.id,
        JEPA_OPERATIONAL_FAILURE.id,
    }:
        reasons.append("semantic evidence provenance outcome definitions do not match")
    return reasons


class _ChangeEncoder:
    def __init__(self, config: JEPABackendConfig) -> None:
        self._config = config

    def encode(self, event: ChangeEvent) -> np.ndarray:
        tokens: list[tuple[str, float]] = [
            (f"repo:{event.repo}", 1.0),
            (f"ref:{event.change_ref}", 1.0),
            (f"author:{event.author or ''}", 0.5),
            (f"files:{len(event.files_touched)}", 0.75),
            (f"added:{event.loc_added}", 0.5),
            (f"removed:{event.loc_removed}", 0.5),
        ]
        for path in event.files_touched:
            tokens.append((f"path:{path}", 1.0))
        for key, value in sorted(event.features.items()):
            if isinstance(value, str):
                for token in _TOKEN_RE.findall(value.lower()):
                    tokens.append((f"feature:{key}:{token}", 0.75))
            elif isinstance(value, bool):
                tokens.append((f"feature:{key}:{value}", 0.5))
            elif isinstance(value, int | float) and math.isfinite(float(value)):
                tokens.append((f"feature:{key}", float(value)))

        vector = np.zeros(self._config.change_embedding_dim, dtype=float)
        for token, weight in tokens:
            digest = hashlib.sha256(
                f"{self._config.hash_seed}:{token}".encode("utf-8")
            ).digest()
            index = int.from_bytes(digest[:8], "big") % vector.size
            sign = -1.0 if digest[8] & 1 else 1.0
            vector[index] += sign * weight
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            vector[0] = 1.0
            norm = 1.0
        return vector / norm


class _StateEncoder:
    def __init__(self, config: JEPABackendConfig, input_width: int) -> None:
        self.input_width = input_width
        self._config = config
        self._projection = _projection(
            config.hash_seed,
            input_width * 5,
            config.state_embedding_dim,
        )
        self.identity = content_hash(
            {
                "kind": "isoprax.jepa.state-encoder",
                "hash_seed": config.hash_seed,
                "input_width": input_width,
                "embedding_dim": config.state_embedding_dim,
            }
        )

    def encode(self, window: Sequence[Sequence[float]]) -> np.ndarray:
        array = _state_array(window, "state")
        if array.shape[1] != self.input_width:
            raise ValueError(
                f"state width {array.shape[1]} does not match fitted width {self.input_width}"
            )
        features = state_feature_vector(window)
        return features @ self._projection


class JEPAWorldModel:
    """Shared two-encoder, one-predictor reference backend."""

    def __init__(self, config: JEPABackendConfig | None = None) -> None:
        self.config = config or JEPABackendConfig()
        self._change_encoder = _ChangeEncoder(self.config)
        self._state_encoder: _StateEncoder | None = None
        self._predictor: np.ndarray | None = None
        self._anomaly_scale: float | None = None
        self._report: JEPATrainingReport | None = None
        self._backend_identity = ""

    @property
    def is_fitted(self) -> bool:
        return self._predictor is not None and self._state_encoder is not None

    @property
    def backend_identity(self) -> str:
        return self._backend_identity

    @property
    def state_representation_identity(self) -> str:
        return self._state_encoder.identity if self._state_encoder is not None else ""

    @property
    def shared_representation_proof(self) -> str:
        if not self.is_fitted:
            return ""
        return content_hash(
            {
                "kind": "isoprax.jepa.shared-readout-proof",
                "backend_identity": self.backend_identity,
                "state_representation_identity": self.state_representation_identity,
                "readouts": (
                    "change_embedding",
                    "prediction_error_against_post_state_embedding",
                ),
                "non_decomposable": True,
            }
        )

    @property
    def training_report(self) -> JEPATrainingReport:
        if self._report is None:
            raise ValueError(
                "JEPA model must be fit before reading its training report"
            )
        return self._report

    def _require_fitted(self) -> tuple[_StateEncoder, np.ndarray, float]:
        if not self.is_fitted or self._state_encoder is None or self._predictor is None:
            raise ValueError("JEPA model must be fit before prediction")
        return self._state_encoder, self._predictor, self._anomaly_scale or 1e-9

    def _features(
        self, change: ChangeEvent, pre_state: Sequence[Sequence[float]]
    ) -> np.ndarray:
        state_encoder, _, _ = self._require_fitted()
        return np.concatenate(
            (
                state_encoder.encode(pre_state),
                self._change_encoder.encode(change),
                [1.0],
            )
        )

    def fit(self, pairs: Sequence[JEPATrainingPair]) -> JEPATrainingReport:
        ordered = tuple(pairs)
        if len(ordered) < 2:
            raise ValueError("at least two JEPA training pairs are required")
        if any(not isinstance(pair, JEPATrainingPair) for pair in ordered):
            raise ValueError("training pairs must be JEPATrainingPair instances")
        input_width = len(ordered[0].pre_state[0])
        if any(
            len(pair.pre_state[0]) != input_width
            or len(pair.post_state[0]) != input_width
            for pair in ordered
        ):
            raise ValueError("all training pairs must use the same state width")

        self._state_encoder = _StateEncoder(self.config, input_width)
        rows: list[np.ndarray] = []
        targets: list[np.ndarray] = []
        for pair in ordered:
            rows.append(
                np.concatenate(
                    (
                        self._state_encoder.encode(pair.pre_state),
                        self._change_encoder.encode(pair.change),
                        [1.0],
                    )
                )
            )
            targets.append(self._state_encoder.encode(pair.post_state))
        design = np.vstack(rows)
        target = np.vstack(targets)
        regularizer = np.eye(design.shape[1], dtype=float) * self.config.ridge_lambda
        self._predictor = np.linalg.solve(
            design.T @ design + regularizer,
            design.T @ target,
        )
        predictions = design @ self._predictor
        errors = np.mean((predictions - target) ** 2, axis=1)
        self._anomaly_scale = max(float(np.mean(errors)), 1e-9)
        identity_payload = {
            "kind": "isoprax.jepa.world-model",
            "config": asdict(self.config),
            "state_representation_identity": self.state_representation_identity,
            "predictor": self._predictor.tolist(),
            "anomaly_scale": self._anomaly_scale,
        }
        self._backend_identity = content_hash(identity_payload)
        self._report = JEPATrainingReport(
            pair_count=len(ordered),
            state_input_dim=input_width,
            change_embedding_dim=self.config.change_embedding_dim,
            state_embedding_dim=self.config.state_embedding_dim,
            mean_latent_prediction_error=float(np.mean(errors)),
            backend_identity=self.backend_identity,
            state_representation_identity=self.state_representation_identity,
        )
        return self._report

    def encode_change(self, change: ChangeEvent) -> tuple[float, ...]:
        if not isinstance(change, ChangeEvent):
            raise ValueError("change must be a ChangeEvent")
        return tuple(float(value) for value in self._change_encoder.encode(change))

    def encode_state(self, state: Sequence[Sequence[float]]) -> tuple[float, ...]:
        encoder, _, _ = self._require_fitted()
        return tuple(float(value) for value in encoder.encode(state))

    def predict_post(
        self, change: ChangeEvent, pre_state: Sequence[Sequence[float]]
    ) -> np.ndarray:
        _, predictor, _ = self._require_fitted()
        return self._features(change, pre_state) @ predictor

    def raw_change_risk(self, change: ChangeEvent) -> float:
        self._require_fitted()
        embedding = np.asarray(self.encode_change(change), dtype=float)
        basis = _projection(
            self.config.hash_seed + ":risk",
            self.config.change_embedding_dim,
            1,
        )[:, 0]
        return float(1.0 / (1.0 + math.exp(-float(embedding @ basis))))

    def prediction_error(
        self,
        change: ChangeEvent,
        pre_state: Sequence[Sequence[float]],
        post_state: Sequence[Sequence[float]],
    ) -> float:
        encoder, _, _ = self._require_fitted()
        predicted = self.predict_post(change, pre_state)
        observed = encoder.encode(post_state)
        return float(np.mean((predicted - observed) ** 2))

    def raw_anomaly_score(
        self,
        change: ChangeEvent,
        pre_state: Sequence[Sequence[float]],
        post_state: Sequence[Sequence[float]],
    ) -> float:
        error = self.prediction_error(change, pre_state, post_state)
        _, _, scale = self._require_fitted()
        return float(error / (error + scale))

    def assess(self, evidence: JEPASemanticEvidence | None = None) -> JEPAAssessment:
        reasons: list[str] = []
        if not self.is_fitted:
            reasons.append("model is not fitted; no predictive evidence is available")
        if evidence is None:
            reasons.append("semantic evidence was not supplied")
        else:
            if evidence.backend_identity != self.backend_identity:
                reasons.append("semantic evidence backend identity does not match")
            if (
                evidence.state_representation_identity
                != self.state_representation_identity
            ):
                reasons.append(
                    "semantic evidence representation identity does not match"
                )
            if evidence.shared_representation_proof != self.shared_representation_proof:
                reasons.append(
                    "semantic evidence shared representation proof does not match"
                )
            reasons.extend(_semantic_evidence_gate_reasons(evidence))
            if not evidence.non_decomposable:
                reasons.append(
                    "semantic evidence marks the representation decomposable"
                )
            if len(set(evidence.jit_scores)) < 2:
                reasons.append("JIT evidence is constant")
            if len(set(evidence.aiops_scores)) < 2:
                reasons.append("AIOps evidence is constant")
        tier = "Semantic" if not reasons else "Structural"
        return JEPAAssessment(
            tier=tier,
            backend_identity=self.backend_identity,
            state_representation_identity=self.state_representation_identity,
            reasons=tuple(reasons),
        )


def _calibrated_value(
    raw: float, calibrator: Calibrator | None
) -> tuple[float, CalibrationStatus, str | None]:
    if calibrator is None or not calibrator.is_fitted:
        return raw, CalibrationStatus.UNCALIBRATED, None
    return (
        max(0.0, min(1.0, float(calibrator.transform(raw)))),
        CalibrationStatus.CALIBRATED,
        calibrator.method_name,
    )


class JEPARiskStrategy(RiskStrategy):
    """JIT readout from the change encoder of one shared JEPA backend."""

    strategy_id = "jepa.unified.risk"
    strategy_version = "0.1"
    outcome_definition = JEPA_DEFECT_RISK

    def __init__(
        self,
        model: JEPAWorldModel,
        calibrator: Calibrator | None = None,
        outcome_definition: OutcomeDefinition | None = None,
    ) -> None:
        if not isinstance(model, JEPAWorldModel):
            raise ValueError("model must be a JEPAWorldModel")
        self.model = model
        self.calibrator = calibrator or Calibrator()
        if outcome_definition is not None:
            self.outcome_definition = outcome_definition

    @property
    def backend_identity(self) -> str:
        return self.model.backend_identity

    def fit_calibrator(
        self, events: Sequence[ChangeEvent], outcomes: Sequence[int]
    ) -> "JEPARiskStrategy":
        raw = [self.model.raw_change_risk(event) for event in events]
        if not raw or len(raw) != len(outcomes):
            raise ValueError(
                "calibration events and outcomes must be non-empty and aligned"
            )
        self.calibrator.fit(raw, list(outcomes))
        return self

    def score(self, event: ChangeEvent, context: dict[str, Any]) -> RiskSignal:
        raw = self.model.raw_change_risk(event)
        score, status, method = _calibrated_value(raw, self.calibrator)
        return RiskSignal(
            score=score,
            explanation=(
                f"JEPA change embedding risk={raw:.6f}; backend={self.backend_identity}"
            ),
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            family=event.family,
            outcome_definition_id=self.outcome_definition.id,
            calibration_status=status,
            calibration_method=method,
        )


class JEPAAnomalyStrategy(AnomalyStrategy):
    """AIOps readout from shared latent prediction error."""

    strategy_id = "jepa.unified.anomaly"
    strategy_version = "0.1"
    outcome_definition = JEPA_OPERATIONAL_FAILURE

    def __init__(
        self,
        model: JEPAWorldModel,
        calibrator: Calibrator | None = None,
        outcome_definition: OutcomeDefinition | None = None,
    ) -> None:
        if not isinstance(model, JEPAWorldModel):
            raise ValueError("model must be a JEPAWorldModel")
        self.model = model
        self.calibrator = calibrator or Calibrator()
        if outcome_definition is not None:
            self.outcome_definition = outcome_definition

    @property
    def backend_identity(self) -> str:
        return self.model.backend_identity

    @staticmethod
    def _context(context: Mapping[str, Any]) -> tuple[ChangeEvent, Any, Any]:
        if not isinstance(context, Mapping):
            raise ValueError("anomaly context must be a mapping")
        change = context.get("change")
        if not isinstance(change, ChangeEvent):
            raise ValueError("anomaly context requires a ChangeEvent under 'change'")
        if "pre_state" not in context or "post_state" not in context:
            raise ValueError(
                "anomaly context requires pre_state and post_state windows"
            )
        return change, context["pre_state"], context["post_state"]

    def fit_calibrator(
        self,
        cases: Sequence[tuple[RunEvent, Mapping[str, Any]]],
        outcomes: Sequence[int],
    ) -> "JEPAAnomalyStrategy":
        raw = [
            self.model.raw_anomaly_score(*self._context(context))
            for _, context in cases
        ]
        if not raw or len(raw) != len(outcomes):
            raise ValueError(
                "calibration cases and outcomes must be non-empty and aligned"
            )
        self.calibrator.fit(raw, list(outcomes))
        return self

    def evaluate(self, event: RunEvent, context: dict[str, Any]) -> AnomalySignal:
        change, pre_state, post_state = self._context(context)
        raw = self.model.raw_anomaly_score(change, pre_state, post_state)
        score, status, method = _calibrated_value(raw, self.calibrator)
        return AnomalySignal(
            score=score,
            explanation=(
                f"JEPA latent prediction error risk={raw:.6f}; "
                f"backend={self.backend_identity}"
            ),
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            family=event.family,
            outcome_definition_id=self.outcome_definition.id,
            calibration_status=status,
            calibration_method=method,
        )


__all__ = [
    "EvidenceProvenance",
    "JEPAAnomalyStrategy",
    "JEPAAssessment",
    "JEPABackendConfig",
    "JEPA_DEFECT_RISK",
    "JEPA_OPERATIONAL_FAILURE",
    "JEPARiskStrategy",
    "JEPASemanticEvidence",
    "JEPATrainingPair",
    "JEPATrainingReport",
    "JEPAWorldModel",
]
