"""Optional PyTorch EB-JEPA-style backend for the Isoprax event contract.

The module is import-safe without PyTorch. It implements a small tabular adapter:
separate change/state encoders, an action-conditioned predictor, an EMA target
encoder, and variance/covariance anti-collapse diagnostics. It is runtime evidence
for a learned backend, not an efficacy claim.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from .commensurability import OutcomeDefinition
from .events import ChangeEvent, RunEvent
from .identity import content_hash
from .jepa import (
    JEPA_DEFECT_RISK,
    JEPA_OPERATIONAL_FAILURE,
    JEPAAssessment,
    JEPABackendConfig,
    JEPASemanticEvidence,
    JEPATrainingPair,
    _calibrated_value,
    _ChangeEncoder,
    _semantic_evidence_gate_reasons,
    state_feature_vector,
)
from .signals import AnomalySignal, RiskSignal
from .strategies import AnomalyStrategy, Calibrator, RiskStrategy

_CLAIM_BOUNDARY = (
    "EB-JEPA runtime evidence only; GPU execution, finite training loss, and a "
    "synthetic smoke test do not establish predictive efficacy or Semantic/Full "
    "Conformance."
)


def _load_torch():
    try:
        import torch
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "EB-JEPA requires optional PyTorch; install the gpu extra or a "
            "host-appropriate PyTorch build"
        ) from error
    return torch


@dataclass(frozen=True)
class EBJEPAConfig:
    """Explicit training/device configuration included in backend identity."""

    change_input_dim: int = 32
    hidden_dim: int = 64
    state_embedding_dim: int = 16
    epochs: int = 32
    batch_size: int = 32
    learning_rate: float = 1e-3
    ema_decay: float = 0.99
    prediction_weight: float = 1.0
    variance_weight: float = 1.0
    covariance_weight: float = 0.1
    seed: int = 7
    device: str = "cpu"
    hash_seed: str = "isoprax-eb-jepa-v1"

    def __post_init__(self) -> None:
        for name in ("change_input_dim", "hidden_dim", "state_embedding_dim"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                raise ValueError(f"{name} must be an integer of at least 2")
        for name in ("epochs", "batch_size"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in (
            "learning_rate",
            "ema_decay",
            "prediction_weight",
            "variance_weight",
            "covariance_weight",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError(f"{name} must be numeric")
            if not math.isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.learning_rate == 0.0:
            raise ValueError("learning_rate must be greater than zero")
        if not 0.0 <= self.ema_decay < 1.0:
            raise ValueError("ema_decay must be in [0, 1)")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ValueError("seed must be an integer")
        if not isinstance(self.device, str) or not self.device.strip():
            raise ValueError("device must be non-empty")
        if not isinstance(self.hash_seed, str) or not self.hash_seed.strip():
            raise ValueError("hash_seed must be non-empty")


@dataclass(frozen=True)
class EBJEPATrainingReport:
    pair_count: int
    state_input_dim: int
    change_input_dim: int
    state_embedding_dim: int
    requested_device: str
    actual_device: str
    torch_version: str
    cuda_available: bool
    seed: int
    epochs_completed: int
    final_prediction_loss: float
    final_variance_loss: float
    final_covariance_loss: float
    backend_identity: str
    state_representation_identity: str
    completed: bool = True
    claim_boundary: str = _CLAIM_BOUNDARY

    def __post_init__(self) -> None:
        if self.pair_count < 2:
            raise ValueError("pair_count must be at least 2")
        if self.epochs_completed < 1 or not self.completed:
            raise ValueError("training report must describe a completed run")
        for name in (
            "final_prediction_loss",
            "final_variance_loss",
            "final_covariance_loss",
        ):
            if not math.isfinite(float(getattr(self, name))):
                raise ValueError(f"{name} must be finite")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EBJEPAWorldModel:
    """Shared learned predictor with explicit CPU/CUDA execution."""

    def __init__(self, config: EBJEPAConfig | None = None) -> None:
        self.config = config or EBJEPAConfig()
        self._torch = _load_torch()
        self._device = None
        self._change_net = None
        self._state_net = None
        self._target_state_net = None
        self._predictor = None
        self._change_encoder = _ChangeEncoder(
            JEPABackendConfig(
                change_embedding_dim=self.config.change_input_dim,
                state_embedding_dim=2,
                hash_seed=self.config.hash_seed,
            )
        )
        self._state_input_dim = 0
        self._state_representation_identity = ""
        self._backend_identity = ""
        self._anomaly_scale = 0.0
        self._report: EBJEPATrainingReport | None = None

    @property
    def is_fitted(self) -> bool:
        return self._report is not None

    @property
    def backend_identity(self) -> str:
        return self._backend_identity

    @property
    def state_representation_identity(self) -> str:
        return self._state_representation_identity

    @property
    def shared_representation_proof(self) -> str:
        if not self.is_fitted:
            return ""
        return content_hash(
            {
                "kind": "isoprax.eb-jepa.shared-readout-proof",
                "backend_identity": self.backend_identity,
                "state_representation_identity": self.state_representation_identity,
                "readouts": (
                    "change_embedding",
                    "prediction_error_against_online_post_state_embedding",
                ),
                "non_decomposable": True,
            }
        )

    @property
    def training_report(self) -> EBJEPATrainingReport:
        if self._report is None:
            raise ValueError("EB-JEPA model must be fit before reading its report")
        return self._report

    def _resolve_device(self):
        torch = self._torch
        requested = self.config.device.strip()
        if requested.startswith("cuda"):
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA was requested but CUDA-enabled PyTorch is unavailable"
                )
            try:
                device = torch.device(requested)
                capability = torch.cuda.get_device_capability(device)
                architecture = f"sm_{capability[0]}{capability[1]}"
                supported_architectures = torch.cuda.get_arch_list()
            except Exception as error:
                raise RuntimeError(
                    f"CUDA device initialization failed for {requested}: {error}"
                ) from error
            if architecture not in supported_architectures:
                raise RuntimeError(
                    f"PyTorch wheel does not include {architecture} kernels; install "
                    "a compatible CUDA 12.8+ build"
                )
            try:
                torch.empty(1, device=device)
                torch.zeros(1, device=device).add_(1.0)
            except Exception as error:
                raise RuntimeError(
                    f"CUDA runtime initialization failed for {requested}: {error}"
                ) from error
            return device
        try:
            device = torch.device(requested)
        except Exception as error:
            raise RuntimeError(f"unsupported EB-JEPA device: {requested}") from error
        if device.type != "cpu":
            raise RuntimeError(
                f"EB-JEPA supports explicit cpu or cuda devices, got {requested}"
            )
        return device

    def _seed(self) -> None:
        torch = self._torch
        torch.manual_seed(self.config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.config.seed)
        torch.use_deterministic_algorithms(True, warn_only=True)
        if torch.backends.cudnn.is_available():
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def _validate_pairs(
        self, pairs: Sequence[JEPATrainingPair]
    ) -> tuple[tuple[JEPATrainingPair, ...], int]:
        ordered = tuple(pairs)
        if len(ordered) < 2:
            raise ValueError("at least two EB-JEPA training pairs are required")
        if any(not isinstance(pair, JEPATrainingPair) for pair in ordered):
            raise ValueError("training pairs must be JEPATrainingPair instances")
        input_width = len(ordered[0].pre_state[0])
        for pair in ordered:
            if (
                len(pair.pre_state[0]) != input_width
                or len(pair.post_state[0]) != input_width
            ):
                raise ValueError("all training pairs must use the same state width")
        return ordered, input_width * 5

    def _build_networks(self, state_input_dim: int) -> None:
        torch = self._torch
        nn = torch.nn
        self._change_net = nn.Sequential(
            nn.Linear(self.config.change_input_dim, self.config.hidden_dim),
            nn.GELU(),
            nn.Linear(self.config.hidden_dim, self.config.state_embedding_dim),
        ).to(self._device)
        self._state_net = nn.Sequential(
            nn.Linear(state_input_dim, self.config.hidden_dim),
            nn.GELU(),
            nn.Linear(self.config.hidden_dim, self.config.state_embedding_dim),
        ).to(self._device)
        self._target_state_net = nn.Sequential(
            nn.Linear(state_input_dim, self.config.hidden_dim),
            nn.GELU(),
            nn.Linear(self.config.hidden_dim, self.config.state_embedding_dim),
        ).to(self._device)
        self._target_state_net.load_state_dict(self._state_net.state_dict())
        for parameter in self._target_state_net.parameters():
            parameter.requires_grad_(False)
        self._predictor = nn.Sequential(
            nn.Linear(self.config.state_embedding_dim * 2, self.config.hidden_dim),
            nn.GELU(),
            nn.Linear(self.config.hidden_dim, self.config.state_embedding_dim),
        ).to(self._device)

    def _regularizers(self, values):
        torch = self._torch
        if values.shape[0] < 2:
            return values.new_zeros(()), values.new_zeros(())
        std = torch.sqrt(values.var(dim=0, unbiased=False) + 1e-4)
        variance = torch.relu(1.0 - std).mean()
        centered = values - values.mean(dim=0, keepdim=True)
        covariance = centered.T @ centered / float(values.shape[0])
        off_diagonal = covariance - torch.diag(torch.diagonal(covariance))
        return variance, off_diagonal.pow(2).mean()

    def _ema_update(self) -> None:
        torch = self._torch
        with torch.no_grad():
            for target, source in zip(
                self._target_state_net.parameters(), self._state_net.parameters()
            ):
                target.mul_(self.config.ema_decay).add_(
                    source, alpha=1.0 - self.config.ema_decay
                )

    def fit(self, pairs: Sequence[JEPATrainingPair]) -> EBJEPATrainingReport:
        ordered, state_input_dim = self._validate_pairs(pairs)
        self._device = self._resolve_device()
        self._seed()
        self._state_input_dim = state_input_dim
        self._build_networks(state_input_dim)
        changes = np.vstack(
            [self._change_encoder.encode(pair.change) for pair in ordered]
        )
        pre_states = np.vstack(
            [state_feature_vector(pair.pre_state) for pair in ordered]
        )
        post_states = np.vstack(
            [state_feature_vector(pair.post_state) for pair in ordered]
        )
        torch = self._torch
        change_tensor = torch.as_tensor(
            changes, dtype=torch.float32, device=self._device
        )
        pre_tensor = torch.as_tensor(
            pre_states, dtype=torch.float32, device=self._device
        )
        post_tensor = torch.as_tensor(
            post_states, dtype=torch.float32, device=self._device
        )
        optimizer = torch.optim.Adam(
            list(self._change_net.parameters())
            + list(self._state_net.parameters())
            + list(self._predictor.parameters()),
            lr=self.config.learning_rate,
        )
        final_losses = None
        for _epoch in range(self.config.epochs):
            for start in range(0, len(ordered), self.config.batch_size):
                stop = min(start + self.config.batch_size, len(ordered))
                change_z = self._change_net(change_tensor[start:stop])
                pre_z = self._state_net(pre_tensor[start:stop])
                target_z = self._target_state_net(post_tensor[start:stop]).detach()
                predicted_z = self._predictor(torch.cat((pre_z, change_z), dim=1))
                prediction_loss = torch.nn.functional.mse_loss(predicted_z, target_z)
                variance_loss, covariance_loss = self._regularizers(predicted_z)
                loss = (
                    self.config.prediction_weight * prediction_loss
                    + self.config.variance_weight * variance_loss
                    + self.config.covariance_weight * covariance_loss
                )
                if not torch.isfinite(loss):
                    raise ValueError("EB-JEPA training produced a non-finite loss")
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
                self._ema_update()
        with torch.no_grad():
            change_z = self._change_net(change_tensor)
            pre_z = self._state_net(pre_tensor)
            target_z = self._target_state_net(post_tensor)
            predicted_z = self._predictor(torch.cat((pre_z, change_z), dim=1))
            prediction_loss = torch.nn.functional.mse_loss(predicted_z, target_z)
            variance_loss, covariance_loss = self._regularizers(predicted_z)
            errors = torch.mean((predicted_z - target_z) ** 2, dim=1)
        final_losses = (
            prediction_loss,
            variance_loss,
            covariance_loss,
            errors.mean(),
        )
        if not all(bool(torch.isfinite(value)) for value in final_losses):
            raise ValueError("EB-JEPA training diagnostics are non-finite")
        self._anomaly_scale = max(float(final_losses[3].item()), 1e-9)
        self._state_representation_identity = content_hash(
            {
                "kind": "isoprax.eb-jepa.state-encoder",
                "input_dim": state_input_dim,
                "embedding_dim": self.config.state_embedding_dim,
                "hash_seed": self.config.hash_seed,
            }
        )
        state_payload = {}
        for prefix, network in (
            ("change", self._change_net),
            ("state", self._state_net),
            ("predictor", self._predictor),
        ):
            state_payload.update(
                {
                    f"{prefix}.{name}": value.detach().cpu().tolist()
                    for name, value in network.named_parameters()
                }
            )
        self._backend_identity = content_hash(
            {
                "kind": "isoprax.eb-jepa.world-model",
                "config": asdict(self.config),
                "actual_device": str(self._device),
                "state_representation_identity": self.state_representation_identity,
                "parameters": state_payload,
                "anomaly_scale": self._anomaly_scale,
            }
        )
        self._report = EBJEPATrainingReport(
            pair_count=len(ordered),
            state_input_dim=state_input_dim,
            change_input_dim=self.config.change_input_dim,
            state_embedding_dim=self.config.state_embedding_dim,
            requested_device=self.config.device,
            actual_device=str(self._device),
            torch_version=str(torch.__version__),
            cuda_available=bool(torch.cuda.is_available()),
            seed=self.config.seed,
            epochs_completed=self.config.epochs,
            final_prediction_loss=float(final_losses[0].item()),
            final_variance_loss=float(final_losses[1].item()),
            final_covariance_loss=float(final_losses[2].item()),
            backend_identity=self.backend_identity,
            state_representation_identity=self.state_representation_identity,
        )
        return self._report

    def _require_fitted(self):
        if not self.is_fitted:
            raise ValueError("EB-JEPA model must be fit before prediction")
        return self._device

    def _state_tensor(self, state: Sequence[Sequence[float]]):
        array = state_feature_vector(state)
        if array.shape[0] != self._state_input_dim:
            raise ValueError("state width does not match fitted EB-JEPA model")
        return self._torch.as_tensor(
            array, dtype=self._torch.float32, device=self._device
        ).unsqueeze(0)

    def encode_change(self, change: ChangeEvent) -> tuple[float, ...]:
        self._require_fitted()
        if not isinstance(change, ChangeEvent):
            raise ValueError("change must be a ChangeEvent")
        with self._torch.no_grad():
            value = self._change_net(
                self._torch.as_tensor(
                    self._change_encoder.encode(change),
                    dtype=self._torch.float32,
                    device=self._device,
                ).unsqueeze(0)
            )
        return tuple(float(item) for item in value.squeeze(0).detach().cpu().tolist())

    def encode_state(self, state: Sequence[Sequence[float]]) -> tuple[float, ...]:
        self._require_fitted()
        with self._torch.no_grad():
            value = self._state_net(self._state_tensor(state))
        return tuple(float(item) for item in value.squeeze(0).detach().cpu().tolist())

    def predict_post(
        self, change: ChangeEvent, pre_state: Sequence[Sequence[float]]
    ) -> np.ndarray:
        self._require_fitted()
        change_z = self._torch.as_tensor(
            self.encode_change(change), dtype=self._torch.float32, device=self._device
        ).unsqueeze(0)
        pre_z = self._torch.as_tensor(
            self.encode_state(pre_state), dtype=self._torch.float32, device=self._device
        ).unsqueeze(0)
        with self._torch.no_grad():
            value = self._predictor(self._torch.cat((pre_z, change_z), dim=1))
        return value.squeeze(0).detach().cpu().numpy()

    def raw_change_risk(self, change: ChangeEvent) -> float:
        values = np.asarray(self.encode_change(change), dtype=float)
        raw = 1.0 / (1.0 + math.exp(-float(values.mean())))
        return float(max(0.0, min(1.0, raw)))

    def prediction_error(
        self,
        change: ChangeEvent,
        pre_state: Sequence[Sequence[float]],
        post_state: Sequence[Sequence[float]],
    ) -> float:
        predicted = self.predict_post(change, pre_state)
        observed = np.asarray(self.encode_state(post_state), dtype=float)
        return float(np.mean((predicted - observed) ** 2))

    def raw_anomaly_score(
        self,
        change: ChangeEvent,
        pre_state: Sequence[Sequence[float]],
        post_state: Sequence[Sequence[float]],
    ) -> float:
        self._require_fitted()
        error = self.prediction_error(change, pre_state, post_state)
        return float(error / (error + self._anomaly_scale))

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
            if not evidence.non_decomposable:
                reasons.append(
                    "semantic evidence marks the representation decomposable"
                )
            reasons.extend(_semantic_evidence_gate_reasons(evidence))
            if len(set(evidence.jit_scores)) < 2:
                reasons.append("JIT evidence is constant")
            if len(set(evidence.aiops_scores)) < 2:
                reasons.append("AIOps evidence is constant")
        return JEPAAssessment(
            tier="Semantic" if not reasons else "Structural",
            backend_identity=self.backend_identity,
            state_representation_identity=self.state_representation_identity,
            reasons=tuple(reasons),
            claim_boundary=_CLAIM_BOUNDARY,
        )


class EBJEPARiskStrategy(RiskStrategy):
    """JIT readout from the learned change representation."""

    strategy_id = "eb-jepa.unified.risk"
    strategy_version = "0.1"
    outcome_definition = JEPA_DEFECT_RISK

    def __init__(
        self,
        model: EBJEPAWorldModel,
        calibrator: Calibrator | None = None,
        outcome_definition: OutcomeDefinition | None = None,
    ) -> None:
        if not isinstance(model, EBJEPAWorldModel):
            raise ValueError("model must be an EBJEPAWorldModel")
        self.model = model
        self.calibrator = calibrator or Calibrator()
        if outcome_definition is not None:
            self.outcome_definition = outcome_definition

    @property
    def backend_identity(self) -> str:
        return self.model.backend_identity

    def fit_calibrator(
        self, events: Sequence[ChangeEvent], outcomes: Sequence[int]
    ) -> "EBJEPARiskStrategy":
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
            explanation=f"EB-JEPA change embedding risk={raw:.6f}; backend={self.backend_identity}",
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            family=event.family,
            outcome_definition_id=self.outcome_definition.id,
            calibration_status=status,
            calibration_method=method,
        )


class EBJEPAAnomalyStrategy(AnomalyStrategy):
    """AIOps readout from learned latent prediction error."""

    strategy_id = "eb-jepa.unified.anomaly"
    strategy_version = "0.1"
    outcome_definition = JEPA_OPERATIONAL_FAILURE

    def __init__(
        self,
        model: EBJEPAWorldModel,
        calibrator: Calibrator | None = None,
        outcome_definition: OutcomeDefinition | None = None,
    ) -> None:
        if not isinstance(model, EBJEPAWorldModel):
            raise ValueError("model must be an EBJEPAWorldModel")
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
    ) -> "EBJEPAAnomalyStrategy":
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
            explanation=f"EB-JEPA latent prediction error risk={raw:.6f}; backend={self.backend_identity}",
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            family=event.family,
            outcome_definition_id=self.outcome_definition.id,
            calibration_status=status,
            calibration_method=method,
        )


__all__ = [
    "EBJEPAAnomalyStrategy",
    "EBJEPAConfig",
    "EBJEPARiskStrategy",
    "EBJEPATrainingReport",
    "EBJEPAWorldModel",
]
