"""
Conformance-flavored tests: each maps to a MUST clause in Isoprax.
This is the seed of the conformance test suite (spec Appendix E, issue #2).
Run with: PYTHONPATH=. python3 -m pytest tests/ -q
"""

import pytest

from isoprax import (
    AnomalySignal,
    CalibrationStatus,
    Calibrator,
    ChangeEvent,
    DistributionAnomalyStrategy,
    Event,
    Family,
    ForecastSignal,
    HeuristicRiskStrategy,
    IncommensurableError,
    MetricSample,
    Outcome,
    OutcomeDefinition,
    OutcomeDefinitionRegistry,
    RiskSignal,
    RunEvent,
    SQLiteKB,
    check_commensurable,
    require_commensurable,
)
from isoprax.baseline_strategies import DEFECT_LINKED_FIX, JOB_RUN_FAILURE
from isoprax.evaluation import (
    CrossFamilyReport,
    brier_score,
    check_calibration_conformance,
    expected_calibration_error,
    paired_comparison,
    reliability_curve,
    time_sliced_split,
)

# --- Section 4: event model MUSTs ---


def test_change_event_requires_mandatory_fields():
    with pytest.raises(ValueError):
        ChangeEvent(source="git")  # missing repo/change_ref


def test_events_have_unique_ids():
    a = ChangeEvent(repo="r", change_ref="x")
    b = ChangeEvent(repo="r", change_ref="x")
    assert a.id != b.id  # spec 4.1: distinct ids even if otherwise identical


def test_family_discriminator_set():
    assert ChangeEvent(repo="r", change_ref="x").family == Family.CHANGE
    assert RunEvent(job_type="j", exit_status="ok").family == Family.OPERATIONAL


@pytest.mark.parametrize(
    "timestamp",
    ["not-a-timestamp", "2026-01-01T00:00:00", "2026-01-01T00:00:00+02:00"],
)
def test_event_rejects_non_rfc3339_or_non_utc_timestamp(timestamp):
    with pytest.raises(ValueError):
        ChangeEvent(repo="r", change_ref="x", timestamp=timestamp)


def test_event_rejects_missing_id_or_source():
    with pytest.raises(ValueError):
        ChangeEvent(repo="r", change_ref="x", id="")
    with pytest.raises(ValueError):
        ChangeEvent(repo="r", change_ref="x", source="")


def test_event_base_and_subtype_guards_are_fail_closed():
    with pytest.raises(ValueError, match="must be a"):
        Event()
    with pytest.raises(ValueError, match="timestamp"):
        ChangeEvent(repo="r", change_ref="x", timestamp=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timestamp"):
        ChangeEvent(repo="r", change_ref="x", timestamp="2026-01-01Tnope+00:00")
    with pytest.raises(ValueError, match="job_type"):
        RunEvent(exit_status="ok")
    with pytest.raises(ValueError, match="resource_id"):
        MetricSample(resource_type="cpu")


def test_extension_field_preserved(tmp_path):
    kb = SQLiteKB(str(tmp_path / "t.db"))
    e = ChangeEvent(repo="r", change_ref="x", features={"vendor_key": 42})
    kb.store_event(e)
    got = kb.get_event(e.id)
    assert got["features"]["vendor_key"] == 42  # spec 4.4 no silent loss


# --- Section 5: Signal MUSTs ---


def test_signal_score_bounds():
    with pytest.raises(ValueError):
        RiskSignal(
            score=1.5,
            explanation="x",
            strategy_id="s",
            strategy_version="0",
            family=Family.CHANGE,
            outcome_definition_id="test.definition",
        )


def test_signal_requires_nonempty_explanation():
    with pytest.raises(ValueError):
        RiskSignal(
            score=0.5,
            explanation="  ",
            strategy_id="s",
            strategy_version="0",
            family=Family.CHANGE,
        )


@pytest.mark.parametrize("field", ["strategy_id", "strategy_version"])
def test_signal_requires_strategy_provenance(field):
    kwargs = {
        "score": 0.5,
        "explanation": "x",
        "strategy_id": "s",
        "strategy_version": "1",
        "family": Family.CHANGE,
        "outcome_definition_id": "d",
    }
    kwargs[field] = ""
    with pytest.raises(ValueError, match=field):
        RiskSignal(**kwargs)


def test_forecast_signal_requires_technique():
    with pytest.raises(ValueError):
        ForecastSignal(
            explanation="x",
            strategy_id="s",
            strategy_version="0",
            family=Family.OPERATIONAL,
            interval_confidence=0.9,
            technique="",
        )  # spec 5.4


def test_forecast_signal_must_not_carry_score():
    """spec 5.2: coverage != outcome probability; they share no axis."""
    with pytest.raises(TypeError):
        ForecastSignal(
            score=0.5,
            explanation="x",
            strategy_id="s",
            strategy_version="0",
            family=Family.OPERATIONAL,
            interval_confidence=0.9,
            technique="arima",
        )
    ok = ForecastSignal(
        explanation="x",
        strategy_id="s",
        strategy_version="0",
        family=Family.OPERATIONAL,
        interval_confidence=0.9,
        technique="arima",
    )
    with pytest.raises(AttributeError):
        ok.score = 0.5  # cannot be bolted on after construction either


def test_forecast_interval_confidence_bounds():
    with pytest.raises(ValueError):
        ForecastSignal(
            explanation="x",
            strategy_id="s",
            strategy_version="0",
            family=Family.OPERATIONAL,
            interval_confidence=1.4,
            technique="arima",
        )


def test_family_mismatch_rejected():
    """spec 4.1: family is derived from type; mismatches MUST be rejected."""
    with pytest.raises(ValueError):
        ChangeEvent(repo="r", change_ref="x", family=Family.OPERATIONAL)
    with pytest.raises(ValueError):
        RunEvent(job_type="j", exit_status="ok", family=Family.CHANGE)
    with pytest.raises(ValueError):
        MetricSample(
            resource_id="d", resource_type="disk", value=1.0, family=Family.CHANGE
        )


def test_uncalibrated_declared_by_default():
    # spec 5.3: an unfitted strategy MUST declare scores uncalibrated
    s = HeuristicRiskStrategy()
    sig = s.score(
        ChangeEvent(repo="r", change_ref="x", loc_added=300, files_touched=["a", "b"]),
        {},
    )
    assert sig.calibration_status == CalibrationStatus.UNCALIBRATED


def test_calibrator_is_honest_when_unfitted_and_transforms_after_fit():
    calibrator = Calibrator().fit([0.2, 0.8], [1, 1])
    assert not calibrator.is_fitted
    assert calibrator.transform(0.3) == 0.3

    fitted = Calibrator().fit([0.1, 0.9], [0, 1])
    assert fitted.is_fitted
    assert 0.0 <= fitted.transform(0.5) <= 1.0


def test_outcome_definition_registry_rejects_conflicts_and_unknown_ids():
    registry = OutcomeDefinitionRegistry()
    definition = _defn(id="registered")
    assert registry.register(definition) == definition
    assert registry.resolve("registered") == definition
    assert "registered" in registry and registry.ids() == ["registered"]
    with pytest.raises(ValueError, match="different content"):
        registry.register(_defn(id="registered", event="different"))
    with pytest.raises(KeyError, match="unresolvable"):
        registry.resolve("missing")


def test_baseline_strategies_cover_risk_factors_and_sparse_anomaly_history():
    risk = HeuristicRiskStrategy(fragile_paths=("core/",))
    event = ChangeEvent(
        repo="r",
        change_ref="x",
        timestamp="2026-01-01T23:00:00+00:00",
        loc_added=600,
        loc_removed=500,
        files_touched=["core/a.py"] * 9,
    )
    assert risk.score(event, {}).score == 1.0
    anomaly = DistributionAnomalyStrategy(history_by_jobtype={})
    assert (
        "no duration"
        in anomaly.evaluate(RunEvent(job_type="x", exit_status="ok"), {}).explanation
    )
    assert (
        "insufficient history"
        in anomaly.evaluate(
            RunEvent(job_type="x", exit_status="ok", duration=1), {}
        ).explanation
    )


def test_baseline_strategies_cover_calibration_and_distribution_history():
    calibrator = Calibrator().fit([0.1, 0.9], [0, 1])
    risk = HeuristicRiskStrategy(
        calibrator=calibrator, outcome_definition=_defn(id="risk")
    )
    assert (
        risk.score(
            ChangeEvent(
                repo="r",
                change_ref="x",
                loc_added=60,
                timestamp="2026-01-01T12:00:00+00:00",
            ),
            {},
        ).calibration_status
        == CalibrationStatus.CALIBRATED
    )
    malformed = ChangeEvent(repo="r", change_ref="x")
    malformed.timestamp = "bad"
    assert HeuristicRiskStrategy()._raw_score(malformed)[0] == 0.0
    assert (
        DistributionAnomalyStrategy(
            outcome_definition=_defn(id="override")
        ).outcome_definition.id
        == "override"
    )
    anomaly = DistributionAnomalyStrategy(
        history_by_jobtype={"job": [1, 2, 3, 4, 5]}, calibrator=calibrator
    )
    assert (
        anomaly.evaluate(
            RunEvent(job_type="job", exit_status="ok", duration=20), {}
        ).calibration_status
        == CalibrationStatus.CALIBRATED
    )


def test_signal_family_interval_and_serialization_guards():
    with pytest.raises(ValueError, match="RiskSignal family"):
        RiskSignal(
            score=0.5,
            explanation="x",
            strategy_id="s",
            strategy_version="1",
            family=Family.OPERATIONAL,
            outcome_definition_id="d",
        )
    with pytest.raises(ValueError, match="AnomalySignal family"):
        AnomalySignal(
            score=0.5,
            explanation="x",
            strategy_id="s",
            strategy_version="1",
            family=Family.CHANGE,
            outcome_definition_id="d",
        )
    with pytest.raises(ValueError, match="interval_low"):
        ForecastSignal(
            explanation="x",
            strategy_id="s",
            strategy_version="1",
            family=Family.OPERATIONAL,
            interval_confidence=0.5,
            interval_low=2,
            interval_high=1,
            technique="arima",
        )
    assert (
        RiskSignal(
            score=0.5,
            explanation="x",
            strategy_id="s",
            strategy_version="1",
            family=Family.CHANGE,
            outcome_definition_id="d",
            calibration_status=CalibrationStatus.CALIBRATED,
        ).to_dict()["calibration_status"]
        == "calibrated"
    )
    raw_status = RiskSignal(
        score=0.5,
        explanation="x",
        strategy_id="s",
        strategy_version="1",
        family=Family.CHANGE,
        outcome_definition_id="d",
    )
    raw_status.calibration_status = "declared"  # type: ignore[assignment]
    assert raw_status.to_dict()["calibration_status"] == "declared"
    with pytest.raises(ValueError, match="ForecastSignal family"):
        ForecastSignal(
            explanation="x",
            strategy_id="s",
            strategy_version="1",
            family=Family.CHANGE,
            interval_confidence=0.5,
            technique="arima",
        )


# --- Section 6/7: KB + feedback linkage MUSTs ---


def test_event_signal_outcome_linkage(tmp_path):
    kb = SQLiteKB(str(tmp_path / "t.db"))
    kb.store_outcome_definition(JOB_RUN_FAILURE)
    s = DistributionAnomalyStrategy(history_by_jobtype={"j": [10.0] * 10})
    e = RunEvent(job_type="j", exit_status="failed", duration=40.0)
    sig = s.evaluate(e, {})
    kb.store_event(e)
    kb.store_signal(e.id, sig)
    kb.store_outcome(
        Outcome(
            event_id=e.id,
            signal_strategy_id=s.strategy_id,
            predicted_condition_occurred=True,
            outcome_definition_id=s.outcome_definition.id,
        )
    )
    pairs = kb.get_labeled_pairs(s.strategy_id)  # spec 6: linkage preserved
    assert len(pairs) == 1
    assert pairs[0][1] == 1


def test_outcome_definition_must_match_stored_signal(tmp_path):
    """specs 5.6.1 and 7: a differently-labelled outcome cannot train a signal."""
    kb = SQLiteKB(str(tmp_path / "t.db"))
    kb.store_outcome_definition(DEFECT_LINKED_FIX)
    kb.store_outcome_definition(JOB_RUN_FAILURE)
    event = ChangeEvent(repo="r", change_ref="x")
    signal = HeuristicRiskStrategy().score(event, {})
    kb.store_event(event)
    kb.store_signal(event.id, signal)

    with pytest.raises(ValueError, match="does not match"):
        kb.store_outcome(
            Outcome(
                event_id=event.id,
                signal_strategy_id=signal.strategy_id,
                predicted_condition_occurred=True,
                outcome_definition_id=JOB_RUN_FAILURE.id,
            )
        )


def test_time_ordered_retrieval(tmp_path):
    kb = SQLiteKB(str(tmp_path / "t.db"))
    kb.store_event(
        MetricSample(
            timestamp="2026-06-02T00:00:00+00:00",
            resource_id="d",
            resource_type="disk",
            value=1,
        )
    )
    kb.store_event(
        MetricSample(
            timestamp="2026-06-01T00:00:00+00:00",
            resource_id="d",
            resource_type="disk",
            value=2,
        )
    )
    got = kb.query_events(family=Family.OPERATIONAL)
    ts = [g["timestamp"] for g in got]
    assert ts == sorted(ts)  # spec 6: time-ordered


def test_sqlite_kb_lifecycle_and_query_filters_fail_closed(tmp_path):
    path = str(tmp_path / "lifecycle.db")
    with SQLiteKB(path) as kb:
        event = ChangeEvent(
            repo="r", change_ref="x", timestamp="2026-01-02T00:00:00+00:00"
        )
        kb.store_event(event)
        assert kb.query_events(
            event_type="ChangeEvent", start="2026-01-01", end="2026-01-03"
        )
        with pytest.raises(KeyError, match="unknown event"):
            kb.store_signal("missing", HeuristicRiskStrategy().score(event, {}))
        with pytest.raises(KeyError, match="originating event signal"):
            kb.store_outcome(Outcome("missing", "s", True, DEFECT_LINKED_FIX.id))
    assert kb.conn is None
    kb.close()


# --- Section 3.3: cross-family conformance ---


def test_both_families_same_contract(tmp_path):
    """The distinguishing property: one KB, both families, same Signal type."""
    kb = SQLiteKB(str(tmp_path / "t.db"))
    kb.store_outcome_definition(DEFECT_LINKED_FIX)
    kb.store_outcome_definition(JOB_RUN_FAILURE)
    risk = HeuristicRiskStrategy()
    anom = DistributionAnomalyStrategy(history_by_jobtype={"j": [10.0] * 10})

    ce = ChangeEvent(repo="r", change_ref="x", loc_added=300)
    re_ = RunEvent(job_type="j", exit_status="failed", duration=40.0)
    rs = risk.score(ce, {})
    as_ = anom.evaluate(re_, {})

    # both are Signals with the same interface / score semantics
    assert 0.0 <= rs.score <= 1.0 and 0.0 <= as_.score <= 1.0
    assert rs.family == Family.CHANGE and as_.family == Family.OPERATIONAL

    for e, sig, strat in [(ce, rs, risk), (re_, as_, anom)]:
        kb.store_event(e)
        kb.store_signal(e.id, sig)
    assert len(kb.query_events(family=Family.CHANGE)) == 1
    assert len(kb.query_events(family=Family.OPERATIONAL)) == 1


# --- Section 5.6: outcome commensurability (the semantic keystone) ---


def _defn(**kw):
    base = dict(id="d", event="e", observation_process="p", window="w", thresholds="t")
    base.update(kw)
    return OutcomeDefinition(**base)


def test_probability_signal_requires_outcome_definition_id():
    """spec 5.2: a score without a resolvable definition is uninterpretable."""
    with pytest.raises(ValueError):
        RiskSignal(
            score=0.5,
            explanation="x",
            strategy_id="s",
            strategy_version="0",
            family=Family.CHANGE,
            outcome_definition_id="",
        )


def test_outcome_requires_definition_id():
    """spec 7: outcomes record the definition they were determined under."""
    with pytest.raises(ValueError):
        Outcome(event_id="e", signal_strategy_id="s", predicted_condition_occurred=True)


def test_commensurable_when_all_four_fields_match():
    a = _defn(id="a")
    b = _defn(id="b")  # ids differ, semantics identical
    res = check_commensurable(a, b)
    assert res.commensurable
    assert res.differing_fields == []


def test_incommensurable_when_event_differs():
    res = check_commensurable(_defn(id="a"), _defn(id="b", event="other"))
    assert not res.commensurable
    assert "event" in res.differing_fields


def test_incommensurable_when_only_observation_process_differs():
    """Same event name, different detector => still not comparable."""
    res = check_commensurable(_defn(id="a"), _defn(id="b", observation_process="other"))
    assert not res.commensurable
    assert "observation_process" in res.differing_fields


def test_require_commensurable_guards_joint_reasoning():
    """spec 5.6.3: comparison across non-commensurable definitions is barred."""
    with pytest.raises(IncommensurableError):
        require_commensurable(DEFECT_LINKED_FIX, JOB_RUN_FAILURE)


def test_baseline_strategies_are_non_commensurable():
    """The reference implementation's own example fails the semantic test --
    deliberately (spec D.1)."""
    res = check_commensurable(DEFECT_LINKED_FIX, JOB_RUN_FAILURE)
    assert not res.commensurable


def test_cross_family_report_withholds_pooled_figure():
    """spec 5.6.3 / 8.5: no aggregate across non-commensurable definitions."""
    from isoprax.evaluation import cross_family_report

    scores = [0.1, 0.5, 0.9] * 5
    outcomes = [0, 0, 1] * 5
    rep = cross_family_report(
        "change",
        DEFECT_LINKED_FIX,
        scores,
        outcomes,
        "operational",
        JOB_RUN_FAILURE,
        scores,
        outcomes,
    )
    assert rep.commensurable is False
    assert rep.pooled_ece is None
    assert "Structural" in rep.declarable_class


def test_cross_family_report_pools_when_commensurable():
    from isoprax.evaluation import cross_family_report

    shared = _defn(id="shared")
    scores = [0.1, 0.5, 0.9] * 5
    outcomes = [0, 0, 1] * 5
    rep = cross_family_report(
        "change", shared, scores, outcomes, "operational", shared, scores, outcomes
    )
    assert rep.commensurable is True
    assert rep.pooled_ece is not None
    assert "Structural" in rep.declarable_class
    assert "Semantic/Full" in rep.declarable_class


def test_outcome_definition_resolvable_from_kb(tmp_path):
    """spec 6: stored scores stay interpretable after the Strategy is gone."""
    kb = SQLiteKB(str(tmp_path / "t.db"))
    kb.store_outcome_definition(DEFECT_LINKED_FIX)
    got = kb.get_outcome_definition(DEFECT_LINKED_FIX.id)
    assert got.event == DEFECT_LINKED_FIX.event
    with pytest.raises(KeyError):
        kb.get_outcome_definition("nope")


def test_calibration_conformance_handles_required_edges():
    assert not check_calibration_conformance([0.5], [1]).passes
    assert not check_calibration_conformance([0.5] * 500, [1] * 500).passes
    with pytest.raises(ValueError, match="equal length"):
        check_calibration_conformance([0.1], [0, 1])
    with pytest.raises(ValueError, match="binary"):
        check_calibration_conformance([0.1], [2])


def test_time_sliced_and_paired_evaluation_utilities_reject_invalid_inputs():
    train, test = time_sliced_split(
        [
            {"timestamp": "2026-01-03T00:00:00+00:00"},
            {"timestamp": "2026-01-01T00:00:00+00:00"},
            {"timestamp": "2026-01-02T00:00:00+00:00"},
        ],
        train_frac=2 / 3,
    )
    assert [event["timestamp"] for event in train + test] == sorted(
        event["timestamp"] for event in train + test
    )
    assert paired_comparison([0.4, 0.3], [0.2, 0.1]).candidate_brier < 0.4
    with pytest.raises(ValueError, match="equal-length"):
        paired_comparison([0.1], [0.1, 0.2])


def test_evaluation_reports_all_calibration_and_rendering_paths():
    assert brier_score([0, 1], [0, 1]) == 0
    bins = reliability_curve([0, 1], [0, 1], n_bins=2)
    assert len(bins) == 2 and expected_calibration_error([], []) == 0
    assert (
        check_calibration_conformance([], [], min_events=0).as_declaration()
        == "uncalibrated"
    )
    assert (
        check_calibration_conformance([0, 1], [0, 1], min_events=2).as_declaration()
        == "calibrated"
    )
    with pytest.raises(ValueError, match="scores must"):
        check_calibration_conformance([-1], [0])
    better = paired_comparison([1] * 10, [0] * 10)
    worse = paired_comparison([0] * 10, [1] * 10)
    assert "better" in better.verdict and "worse" in worse.verdict
    assert not check_calibration_conformance([1, 1], [0, 0], min_events=2).passes
    withheld = CrossFamilyReport("a", "b", "d1", "d2", False, "no", 0, 0, 1, 1)
    pooled = CrossFamilyReport("a", "b", "d1", "d2", True, "yes", 0, 0, 1, 1, 0.1)
    assert "WITHHELD" in withheld.render() and "pooled ECE" in pooled.render()
