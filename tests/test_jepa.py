import numpy as np
import pytest

from isoprax import (
    AnomalySignal,
    CalibrationStatus,
    Calibrator,
    ChangeEvent,
    EvidenceProvenance,
    JEPAAnomalyStrategy,
    JEPABackendConfig,
    JEPARiskStrategy,
    JEPASemanticEvidence,
    JEPATrainingPair,
    JEPAWorldModel,
    RiskSignal,
    RunEvent,
    SQLiteKB,
)
from isoprax.external_anchor import ExternalAnchorVerification, stage2_statement_payload
from isoprax.identity import content_hash
from isoprax.jepa import JEPA_DEFECT_RISK, JEPA_OPERATIONAL_FAILURE
from isoprax.stage2_corpus_evaluation import CORPUS_MIN_TEST_ROWS
from tests.provenance_helpers import verified_anchor


def _change(index: int = 0) -> ChangeEvent:
    return ChangeEvent(
        id=f"change-{index}",
        repo="demo/repo",
        change_ref=f"commit-{index}",
        author="author",
        files_touched=[f"service/{index}.py"],
        loc_added=5 + index,
        loc_removed=2,
        features={
            "message": f"change {index}",
            "diff": f"@@ -{index},2 +{index},3 @@ return {index}",
        },
    )


def _pair(index: int = 0, delta: float = 0.1) -> JEPATrainingPair:
    pre = (
        (1.0 + index, 2.0 + index),
        (1.2 + index, 2.2 + index),
        (1.4 + index, 2.4 + index),
    )
    post = tuple(tuple(value + delta for value in row) for row in pre)
    return JEPATrainingPair(_change(index), pre, post)


def _model() -> JEPAWorldModel:
    model = JEPAWorldModel(
        JEPABackendConfig(
            change_embedding_dim=12,
            state_embedding_dim=5,
            ridge_lambda=0.01,
        )
    )
    model.fit([_pair(i, 0.1 + i * 0.02) for i in range(6)])
    return model


def _provenance(verified: bool = True) -> EvidenceProvenance:
    payload = {
        "corpus_identity": "real-labeled-fixture-v1",
        "split_identity": "split-v1",
        "label_definition_identity": "labels-v1",
        "outcome_definition_ids": (
            JEPA_DEFECT_RISK.id,
            JEPA_OPERATIONAL_FAILURE.id,
        ),
        "predeclaration_commit": "commit-fixture-v1",
    }
    verification = (
        verified_anchor(payload)
        if verified
        else ExternalAnchorVerification(
            status="unverified",
            anchor_type="sigstore_rekor_dsse",
            anchor_reference="",
            bundle_path="fixture.json",
            signer_identity=None,
            issuer=None,
            reason="fixture verification",
        )
    )
    return EvidenceProvenance(payload, content_hash(payload), verification=verification)


def test_jepa_fit_is_deterministic_and_self_supervised():
    pairs = [_pair(i, 0.1 + i * 0.02) for i in range(6)]
    left = JEPAWorldModel(JEPABackendConfig(change_embedding_dim=12))
    right = JEPAWorldModel(JEPABackendConfig(change_embedding_dim=12))

    left_report = left.fit(pairs)
    right_report = right.fit(pairs)

    assert left_report == right_report
    assert left.backend_identity == right.backend_identity
    assert left.state_representation_identity == right.state_representation_identity
    np.testing.assert_allclose(
        left.predict_post(_change(2), pairs[2].pre_state),
        right.predict_post(_change(2), pairs[2].pre_state),
    )
    assert left_report.pair_count == 6
    assert np.isfinite(left_report.mean_latent_prediction_error)


@pytest.mark.parametrize(
    "pre_state,post_state",
    [
        pytest.param(
            ((1.0, 2.0),),
            ((1.0, 2.0, 3.0),),
            id="inconsistent-state-width",
        ),
        pytest.param(
            ((1.0, float("nan")),),
            ((1.0, 2.0),),
            id="non-finite-state",
        ),
    ],
)
def test_jepa_rejects_invalid_training_pairs(pre_state, post_state):
    with pytest.raises(ValueError):
        JEPATrainingPair(_change(), pre_state, post_state)


def test_jepa_requires_training_before_prediction():
    model = JEPAWorldModel()
    with pytest.raises(ValueError, match="fit"):
        model.predict_post(_change(), ((1.0, 2.0),))
    with pytest.raises(ValueError, match="fit"):
        JEPARiskStrategy(model).score(_change(), {})


def test_jepa_emits_both_existing_signal_contracts_from_one_backend():
    model = _model()
    risk = JEPARiskStrategy(model)
    anomaly = JEPAAnomalyStrategy(model)
    run = RunEvent(job_type="service", job_identifier="run-1", exit_status="ok")
    context = {
        "change": _change(2),
        "pre_state": _pair(2).pre_state,
        "post_state": _pair(2, 1.5).post_state,
    }

    risk_signal = risk.score(_change(3), {})
    anomaly_signal = anomaly.evaluate(run, context)

    assert isinstance(risk_signal, RiskSignal)
    assert isinstance(anomaly_signal, AnomalySignal)
    assert risk_signal.outcome_definition_id == JEPA_DEFECT_RISK.id
    assert anomaly_signal.outcome_definition_id == JEPA_OPERATIONAL_FAILURE.id
    assert risk_signal.calibration_status == CalibrationStatus.UNCALIBRATED
    assert anomaly_signal.calibration_status == CalibrationStatus.UNCALIBRATED
    assert 0.0 <= risk_signal.score <= 1.0
    assert 0.0 <= anomaly_signal.score <= 1.0
    assert risk.model is anomaly.model
    assert risk.backend_identity == anomaly.backend_identity


def test_jepa_anomaly_requires_complete_context():
    with pytest.raises(ValueError, match="pre_state and post_state"):
        JEPAAnomalyStrategy(_model()).evaluate(
            RunEvent(job_type="service", exit_status="ok"),
            {"change": _change()},
        )


def test_jepa_calibration_does_not_change_backend_or_conformance_tier():
    model = _model()
    strategy = JEPARiskStrategy(model, calibrator=Calibrator())
    identity = model.backend_identity

    strategy.fit_calibrator([_change(index) for index in range(6)], [0, 1, 0, 1, 0, 1])
    signal = strategy.score(_change(2), {})

    assert strategy.calibrator.is_fitted
    assert signal.calibration_status == CalibrationStatus.CALIBRATED
    assert model.backend_identity == identity
    assert model.assess().tier == "Structural"


def test_jepa_signals_round_trip_through_existing_sqlite_contract(tmp_path):
    model = _model()
    strategy = JEPARiskStrategy(model)
    event = _change(10)
    signal = strategy.score(event, {})

    with SQLiteKB(str(tmp_path / "jepa.db")) as kb:
        kb.store_outcome_definition(JEPA_DEFECT_RISK)
        kb.store_event(event)
        kb.store_signal(event.id, signal)
        restored = kb.get_signal(event.id, strategy.strategy_id)

    assert restored is not None
    assert restored.to_dict() == signal.to_dict()


def test_jepa_keeps_existing_admission_floor_unchanged():
    assert CORPUS_MIN_TEST_ROWS == 800


def test_jepa_semantic_assessment_is_fail_closed():
    model = _model()
    structural = model.assess()
    assert structural.tier == "Structural"
    assert "Semantic" in structural.claim_boundary
    structural_dict = structural.to_dict()
    assert structural_dict["families"] == ["change", "operational"]
    assert structural_dict["outcome_definition_ids"] == [
        JEPA_DEFECT_RISK.id,
        JEPA_OPERATIONAL_FAILURE.id,
    ]
    assert "commensurable" in structural_dict["commensurability"]
    assert "calibrated" in structural_dict["calibration_qualifier"]

    valid = JEPASemanticEvidence(
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
    assert model.assess(valid).tier == "Semantic"

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
    assert any("synthetic" in reason for reason in model.assess(synthetic).reasons)

    unverified = JEPASemanticEvidence(
        backend_identity=model.backend_identity,
        state_representation_identity=model.state_representation_identity,
        non_decomposable=True,
        jit_scores=(0.1, 0.4, 0.8),
        aiops_scores=(0.2, 0.5, 0.9),
        sample_count=3,
        shared_representation_proof=model.shared_representation_proof,
        evidence_class="real_labeled",
        provenance=_provenance(False),
    )
    assert model.assess(unverified).tier == "Structural"
    assert any("verified" in reason for reason in model.assess(unverified).reasons)

    wrong_backend = JEPASemanticEvidence(
        backend_identity="wrong",
        state_representation_identity=model.state_representation_identity,
        non_decomposable=True,
        jit_scores=(0.1, 0.4),
        aiops_scores=(0.2, 0.5),
        sample_count=2,
        shared_representation_proof=model.shared_representation_proof,
        evidence_class="real_labeled",
        provenance=_provenance(),
    )
    assert model.assess(wrong_backend).tier == "Structural"

    decomposable = JEPASemanticEvidence(
        backend_identity=model.backend_identity,
        state_representation_identity=model.state_representation_identity,
        non_decomposable=False,
        jit_scores=(0.1, 0.4),
        aiops_scores=(0.2, 0.5),
        sample_count=2,
        shared_representation_proof=model.shared_representation_proof,
        evidence_class="real_labeled",
        provenance=_provenance(),
    )
    assert model.assess(decomposable).tier == "Structural"


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"backend_identity": ""}, "backend"),
        ({"shared_representation_proof": ""}, "proof"),
        ({"evidence_class": "gpu_smoke"}, "evidence_class"),
        ({"non_decomposable": "yes"}, "boolean"),
        ({"sample_count": 1}, "sample_count"),
        ({"jit_scores": (float("nan"), 0.4, 0.8)}, "finite"),
    ],
)
def test_jepa_semantic_evidence_rejects_invalid_declarations(kwargs, match):
    model = _model()
    values = {
        "backend_identity": model.backend_identity,
        "state_representation_identity": model.state_representation_identity,
        "non_decomposable": True,
        "jit_scores": (0.1, 0.4, 0.8),
        "aiops_scores": (0.2, 0.5, 0.9),
        "sample_count": 3,
        "shared_representation_proof": model.shared_representation_proof,
        "evidence_class": "real_labeled",
    }
    values.update(kwargs)
    with pytest.raises(ValueError, match=match):
        JEPASemanticEvidence(**values)


def test_evidence_provenance_requires_matching_digest_and_identities():
    with pytest.raises(ValueError, match="corpus, split, labels, outcomes"):
        EvidenceProvenance({"corpus_identity": "only"}, "digest")
    payload = {
        "corpus_identity": "real-labeled-fixture-v1",
        "split_identity": "split-v1",
        "label_definition_identity": "labels-v1",
        "outcome_definition_ids": (JEPA_DEFECT_RISK.id, JEPA_OPERATIONAL_FAILURE.id),
        "predeclaration_commit": "commit-fixture-v1",
    }
    with pytest.raises(ValueError, match="digest"):
        EvidenceProvenance(payload, "wrong")
    with pytest.raises(ValueError, match="verification"):
        EvidenceProvenance(payload, content_hash(payload), verification="yes")
    manual_verified = ExternalAnchorVerification(
        status="verified",
        anchor_type="sigstore_rekor_dsse",
        anchor_reference="rekor://manual",
        bundle_path="missing.json",
        signer_identity="manual-signer",
        issuer="manual-issuer",
        reason="manually constructed",
        statement=stage2_statement_payload(
            content_hash(payload), payload["predeclaration_commit"]
        ),
    )
    assert manual_verified.verified is False
    assert manual_verified.to_dict()["status"] == "unverified"
    with pytest.raises(ValueError, match="external verifier"):
        EvidenceProvenance(payload, content_hash(payload), verification=manual_verified)


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("anchor_type", "other", "anchor type"),
        ("anchor_reference", "", "anchor reference"),
        ("signer_identity", "", "signer identity"),
        ("statement", {}, "does not bind"),
    ],
)
def test_evidence_provenance_requires_a_binding_verified_anchor(field, value, match):
    provenance = _provenance()
    verification = verified_anchor(provenance.payload)
    object.__setattr__(verification, field, value)
    with pytest.raises(ValueError, match=match):
        EvidenceProvenance(
            provenance.payload, provenance.digest, verification=verification
        )


def test_evidence_provenance_rejects_empty_identity_and_outcome_definitions():
    provenance = _provenance()
    empty_identity = dict(provenance.payload)
    empty_identity["corpus_identity"] = ""
    with pytest.raises(ValueError, match="non-empty string"):
        EvidenceProvenance(
            empty_identity,
            content_hash(empty_identity),
            verification=provenance.verification,
        )
    duplicate_outcomes = dict(provenance.payload)
    duplicate_outcomes["outcome_definition_ids"] = (JEPA_DEFECT_RISK.id,) * 2
    with pytest.raises(ValueError, match="unique"):
        EvidenceProvenance(
            duplicate_outcomes,
            content_hash(duplicate_outcomes),
            verification=provenance.verification,
        )


def test_evidence_provenance_deeply_freezes_payload_snapshot():
    source = dict(_provenance().payload)
    source["metadata"] = {"owner": {"team": "platform"}}
    verification = verified_anchor(source)
    provenance = EvidenceProvenance(
        source, content_hash(source), verification=verification
    )

    source["metadata"]["owner"]["team"] = "changed"
    assert provenance.payload["metadata"]["owner"]["team"] == "platform"
    with pytest.raises(TypeError):
        provenance.payload["metadata"]["owner"]["team"] = "changed"
    assert provenance.verified

    provenance.verification.statement["predicate"]["artifact_hash"] = "changed"
    assert provenance.verification.verified is False
    assert provenance.verified is False
    assert provenance.to_dict()["verification"]["status"] == "unverified"
