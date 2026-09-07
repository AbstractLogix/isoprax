from isoprax.evaluation import check_calibration_conformance


def test_constant_base_rate_is_not_qualified_calibration():
    result = check_calibration_conformance([0.5] * 500, [0, 1] * 250)

    assert result.ece == 0.0
    assert result.score_variance == 0.0
    assert not result.discrimination_passes
    assert not result.passes
    assert result.as_declaration() == "uncalibrated"


def test_informative_calibrated_scores_pass_both_gates():
    scores = [0.0] * 250 + [1.0] * 250
    outcomes = [0] * 250 + [1] * 250

    result = check_calibration_conformance(scores, outcomes)

    assert result.passes
    assert result.auc == 1.0
    assert result.discrimination_passes
    assert result.as_declaration() == "calibrated"


def test_missing_discrimination_is_explicit_for_one_class():
    result = check_calibration_conformance([0.1] * 500, [0] * 500)

    assert result.auc is None
    assert not result.discrimination_passes
    assert not result.passes
    assert "one observed outcome class" in result.reason
