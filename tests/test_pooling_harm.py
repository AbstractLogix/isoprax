from isoprax.evidence import build_pooling_harm_evidence


def test_pooled_calibration_masks_top_k_definition_harm():
    evidence = build_pooling_harm_evidence()

    assert evidence.left_ece < 0.05
    assert evidence.right_ece < 0.05
    assert evidence.pooled_ece < 0.05
    assert evidence.per_family_macro_recall == 1.0
    assert evidence.pooled_macro_recall == 0.5
    assert evidence.degradation == 0.5
    assert "not Semantic/Full" in evidence.claim_boundary
