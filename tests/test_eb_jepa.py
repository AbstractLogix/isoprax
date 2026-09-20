import numpy as np
import pytest

torch = pytest.importorskip("torch")

from isoprax import (  # noqa: E402
    AnomalySignal,
    CalibrationStatus,
    ChangeEvent,
    EBJEPAAnomalyStrategy,
    EBJEPAConfig,
    EBJEPARiskStrategy,
    EBJEPAWorldModel,
    EvidenceProvenance,
    JEPASemanticEvidence,
    JEPATrainingPair,
    RiskSignal,
    RunEvent,
)
from isoprax.identity import content_hash  # noqa: E402
from tests.provenance_helpers import verified_anchor  # noqa: E402


def _change(index=0):
    return ChangeEvent(
        id=f"gpu-change-{index}",
        repo="demo/repo",
        change_ref=f"commit-{index}",
        author="author",
        files_touched=[f"service/{index}.py"],
        loc_added=5 + index,
        loc_removed=2,
        features={"message": f"change {index}", "risk_factor": float(index % 3)},
    )


def _pair(index=0):
    pre = (
        (1.0 + index, 2.0 + index),
        (1.2 + index, 2.2 + index),
        (1.4 + index, 2.4 + index),
    )
    post = tuple(tuple(value + 0.1 + index * 0.02 for value in row) for row in pre)
    return JEPATrainingPair(_change(index), pre, post)


def _config(device="cpu"):
    return EBJEPAConfig(
        change_input_dim=12,
        hidden_dim=16,
        state_embedding_dim=6,
        epochs=4,
        batch_size=3,
        learning_rate=0.01,
        device=device,
        seed=17,
    )


def _provenance():
    payload = {
        "corpus_identity": "real-labeled-fixture-v1",
        "split_identity": "split-v1",
        "label_definition_identity": "labels-v1",
        "outcome_definition_ids": (
            "jepa.change_defect_risk.v1",
            "jepa.operational_failure.v1",
        ),
        "predeclaration_commit": "commit-fixture-v1",
    }
    verification = verified_anchor(payload)
    return EvidenceProvenance(payload, content_hash(payload), verification=verification)


def test_eb_jepa_cpu_fit_is_deterministic_and_reports_regularization():
    pairs = [_pair(index) for index in range(8)]
    left = EBJEPAWorldModel(_config())
    right = EBJEPAWorldModel(_config())

    left_report = left.fit(pairs)
    right_report = right.fit(pairs)

    assert left_report == right_report
    assert left.backend_identity == right.backend_identity
    assert left_report.actual_device == "cpu"
    assert left_report.completed
    assert np.isfinite(left_report.final_prediction_loss)
    assert np.isfinite(left_report.final_variance_loss)
    assert np.isfinite(left_report.final_covariance_loss)
    np.testing.assert_allclose(
        left.predict_post(_change(2), pairs[2].pre_state),
        right.predict_post(_change(2), pairs[2].pre_state),
        rtol=1e-5,
        atol=1e-6,
    )


def test_eb_jepa_regularization_weights_affect_trainable_predictions():
    pairs = [_pair(index) for index in range(8)]
    unregularized = EBJEPAWorldModel(
        EBJEPAConfig(
            **{**_config().__dict__, "variance_weight": 0.0, "covariance_weight": 0.0}
        )
    )
    regularized = EBJEPAWorldModel(
        EBJEPAConfig(
            **{**_config().__dict__, "variance_weight": 2.0, "covariance_weight": 2.0}
        )
    )

    unregularized.fit(pairs)
    regularized.fit(pairs)

    assert not np.allclose(
        unregularized.predict_post(_change(2), pairs[2].pre_state),
        regularized.predict_post(_change(2), pairs[2].pre_state),
    )


def test_eb_jepa_preserves_signal_contracts_and_shared_identity():
    model = EBJEPAWorldModel(_config())
    model.fit([_pair(index) for index in range(8)])
    risk = EBJEPARiskStrategy(model)
    anomaly = EBJEPAAnomalyStrategy(model)
    run = RunEvent(job_type="service", job_identifier="run-1", exit_status="ok")
    context = {
        "change": _change(2),
        "pre_state": _pair(2).pre_state,
        "post_state": _pair(2).post_state,
    }

    risk_signal = risk.score(_change(3), {})
    anomaly_signal = anomaly.evaluate(run, context)

    assert isinstance(risk_signal, RiskSignal)
    assert isinstance(anomaly_signal, AnomalySignal)
    assert risk_signal.calibration_status == CalibrationStatus.UNCALIBRATED
    assert anomaly_signal.calibration_status == CalibrationStatus.UNCALIBRATED
    assert 0.0 <= risk_signal.score <= 1.0
    assert 0.0 <= anomaly_signal.score <= 1.0
    assert risk.backend_identity == anomaly.backend_identity == model.backend_identity
    assert model.assess().tier == "Structural"


def test_eb_jepa_cuda_request_does_not_silently_downgrade():
    if torch.cuda.is_available():
        pytest.skip("CUDA is available; use the CUDA smoke test for this host")
    with pytest.raises(RuntimeError, match="CUDA"):
        EBJEPAWorldModel(_config("cuda")).fit([_pair(index) for index in range(4)])


def test_eb_jepa_cuda_initialization_error_keeps_runtime_category(monkeypatch):
    model = EBJEPAWorldModel(_config("cuda"))
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)

    def fail_capability(_device):
        raise RuntimeError("driver init failed")

    monkeypatch.setattr(
        torch.cuda,
        "get_device_capability",
        fail_capability,
    )
    with pytest.raises(RuntimeError, match="CUDA device initialization failed"):
        model._resolve_device()


def test_eb_jepa_cuda_smoke_uses_actual_device_when_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA-enabled PyTorch is unavailable")
    capability = torch.cuda.get_device_capability()
    architecture = f"sm_{capability[0]}{capability[1]}"
    if architecture not in torch.cuda.get_arch_list():
        pytest.skip(f"installed PyTorch wheel lacks {architecture} kernels")
    model = EBJEPAWorldModel(
        EBJEPAConfig(
            **{
                **_config("cuda").__dict__,
                "epochs": 1,
            }
        )
    )
    report = model.fit([_pair(index) for index in range(4)])
    assert report.actual_device.startswith("cuda")
    assert report.cuda_available


@pytest.mark.parametrize(
    "kwargs",
    [
        {"change_input_dim": 1},
        {"hidden_dim": 1},
        {"state_embedding_dim": 1},
        {"epochs": 0},
        {"batch_size": 0},
        {"learning_rate": 0.0},
        {"ema_decay": 1.0},
        {"seed": True},
        {"device": ""},
        {"hash_seed": ""},
    ],
)
def test_eb_jepa_config_rejects_invalid_values(kwargs):
    with pytest.raises(ValueError):
        EBJEPAConfig(**kwargs)


def test_eb_jepa_rejects_invalid_fit_and_inference_inputs():
    model = EBJEPAWorldModel(_config())
    with pytest.raises(ValueError, match="at least two"):
        model.fit([_pair()])
    with pytest.raises(ValueError, match="JEPATrainingPair"):
        model.fit([_pair(), object()])
    with pytest.raises(ValueError, match="fit"):
        model.predict_post(_change(), _pair().pre_state)

    model.fit([_pair(index) for index in range(4)])
    with pytest.raises(ValueError, match="state width"):
        model.encode_state(((1.0, 2.0, 3.0),))
    with pytest.raises(ValueError, match="ChangeEvent"):
        model.encode_change(object())


def test_eb_jepa_reports_structural_default_and_calibrates_both_readouts():
    model = EBJEPAWorldModel(_config())
    model.fit([_pair(index) for index in range(8)])
    risk = EBJEPARiskStrategy(model)
    anomaly = EBJEPAAnomalyStrategy(model)
    run = RunEvent(job_type="service", job_identifier="run-1", exit_status="ok")
    cases = [
        (
            run,
            {
                "change": _change(index),
                "pre_state": _pair(index).pre_state,
                "post_state": _pair(index).post_state,
            },
        )
        for index in range(4)
    ]
    risk.fit_calibrator([_change(index) for index in range(4)], [0, 1, 0, 1])
    anomaly.fit_calibrator(cases, [0, 1, 0, 1])
    assert risk.score(_change(1), {}).calibration_status == CalibrationStatus.CALIBRATED
    assert (
        anomaly.evaluate(run, cases[1][1]).calibration_status
        == CalibrationStatus.CALIBRATED
    )
    predicted = model.predict_post(_change(1), cases[1][1]["pre_state"])
    observed = np.asarray(model.encode_state(cases[1][1]["post_state"]), dtype=float)
    assert model.prediction_error(
        _change(1), cases[1][1]["pre_state"], cases[1][1]["post_state"]
    ) == pytest.approx(float(np.mean((predicted - observed) ** 2)))

    synthetic = JEPASemanticEvidence(
        backend_identity=model.backend_identity,
        state_representation_identity=model.state_representation_identity,
        non_decomposable=True,
        jit_scores=(0.1, 0.4, 0.8),
        aiops_scores=(0.2, 0.5, 0.9),
        sample_count=3,
        shared_representation_proof=model.shared_representation_proof,
    )
    assert model.assess(synthetic).tier == "Structural"

    evidence = JEPASemanticEvidence(
        backend_identity=model.backend_identity,
        state_representation_identity=model.state_representation_identity,
        non_decomposable=True,
        jit_scores=(0.1, 0.4, 0.8),
        aiops_scores=(0.2, 0.5, 0.9),
        sample_count=3,
        shared_representation_proof=model.shared_representation_proof,
        evidence_class="real_labeled",
        provenance=_provenance(),
    )
    assert model.assess(evidence).tier == "Semantic"


def test_eb_jepa_rejects_unsupported_device_and_bad_anomaly_context():
    with pytest.raises(RuntimeError, match="supports explicit"):
        EBJEPAWorldModel(_config("meta")).fit([_pair(index) for index in range(2)])
    model = EBJEPAWorldModel(_config())
    model.fit([_pair(index) for index in range(4)])
    strategy = EBJEPAAnomalyStrategy(model)
    run = RunEvent(job_type="service", job_identifier="run-1", exit_status="ok")
    with pytest.raises(ValueError, match="mapping"):
        strategy.evaluate(run, [])
    with pytest.raises(ValueError, match="ChangeEvent"):
        strategy.evaluate(run, {"change": object(), "pre_state": (), "post_state": ()})
