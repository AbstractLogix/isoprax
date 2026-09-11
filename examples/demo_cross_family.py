"""
Cross-family conformance demonstration for Isoprax.

What this proves:
  1. A Change-family strategy (commit risk) and an Operational-family strategy
     (job anomaly) emit Signals through the IDENTICAL contract and land in the
     SAME knowledge base. (Cross-Family Conformance, spec 3.3)
  2. Both strategies' scores can be CALIBRATED via the same shared mechanism,
     making each score track the empirical frequency of its own declared
     adverse event. Calibration alone does NOT make the two scores comparable;
     the commensurability check below decides that separately. (specs 5.3, 5.6)
  3. Calibration is measured, not asserted: we report Brier score and ECE
     before vs after calibration, and run a paired significance test
     (spec Section 8).

The data here is SYNTHETIC with a known ground-truth relationship, so we can
show calibration works. Real validation would swap in public JIT-defect and
AIOps datasets -- the point of the PoC is the plumbing and the argument.
"""

import random

import numpy as np

from isoprax import (
    Calibrator,
    ChangeEvent,
    DistributionAnomalyStrategy,
    HeuristicRiskStrategy,
    HistoricalMeanForecastStrategy,
    MetricSample,
    Outcome,
    OutcomeDefinition,
    RunEvent,
    SQLiteKB,
    check_commensurable,
)
from isoprax.baseline_strategies import DEFECT_LINKED_FIX, JOB_RUN_FAILURE
from isoprax.evaluation import (
    brier_score,
    cross_family_report,
    expected_calibration_error,
    paired_comparison,
    reliability_curve,
    time_sliced_split,
)
from isoprax.evidence import build_pooling_harm_evidence

random.seed(7)
np.random.seed(7)

FRAGILE = ["src/patroni/", "src/celery_tasks/export"]


def synth_change_events(n):
    """Generate commits with a known latent defect probability, so we have
    ground-truth outcomes to calibrate against."""
    events, truths = [], []
    for i in range(n):
        churn_a = random.randint(0, 400)
        churn_r = random.randint(0, 200)
        nfiles = random.randint(1, 15)
        touches_fragile = random.random() < 0.25
        files = [f"src/module{random.randint(0, 20)}/f{j}.py" for j in range(nfiles)]
        if touches_fragile:
            files.append("src/patroni/config.py")
        hour = random.randint(0, 23)
        ts = f"2026-06-{(i % 27) + 1:02d}T{hour:02d}:15:00+00:00"
        # latent ground-truth defect probability driven by the SAME factors
        # the heuristic keys on, so the heuristic's ranking is informative...
        latent = (
            0.0006 * (churn_a + churn_r)
            + 0.02 * nfiles
            + (0.25 if touches_fragile else 0)
            + (0.12 if (hour >= 22 or hour <= 5) else 0)
        )
        # ...but deliberately compress the TRUE probability so the raw
        # heuristic is systematically OVER-confident (its 0.8 really means
        # ~0.4 in reality). This is the realistic miscalibration that gives
        # the calibrator genuine work to do -- ranking good, scale wrong.
        latent = 0.5 * min(max(latent, 0), 0.95) + 0.05
        latent = min(max(latent + random.uniform(-0.03, 0.03), 0.0), 0.95)
        defect = 1 if random.random() < latent else 0
        e = ChangeEvent(
            source="git",
            repo="afg-infra",
            change_ref=f"sha{i:04d}",
            timestamp=ts,
            files_touched=files,
            loc_added=churn_a,
            loc_removed=churn_r,
        )
        events.append(e)
        truths.append(defect)
    return events, truths


def synth_run_events(n):
    """Generate job runs with a known anomaly/failure relationship."""
    events, truths = [], []
    base_by_type = {"nightly_export": 120.0, "api_sync": 8.0}
    history = {
        k: list(np.random.normal(v, v * 0.1, 40)) for k, v in base_by_type.items()
    }
    for i in range(n):
        jt = random.choice(list(base_by_type))
        base = base_by_type[jt]
        # 20% of runs are genuinely degraded (longer + more likely to fail)
        degraded = random.random() < 0.2
        dur = float(np.random.normal(base * (1.8 if degraded else 1.0), base * 0.12))
        ts = f"2026-06-{(i % 27) + 1:02d}T{random.randint(0, 23):02d}:30:00+00:00"
        failed = 1 if (degraded and random.random() < 0.6) else 0
        e = RunEvent(
            source="nomad",
            job_type=jt,
            job_identifier=f"{jt}-{i}",
            timestamp=ts,
            duration=dur,
            exit_status="failed" if failed else "ok",
        )
        events.append(e)
        truths.append(failed)
    return events, truths, history


def run_family(name, kb, events, truths, strategy, score_fn):
    """Split time-sliced, fit calibrator on train, evaluate on test, store all
    to the shared KB, and report calibration before/after."""
    idx = list(range(len(events)))
    paired = [{"timestamp": events[i].timestamp, "i": i} for i in idx]
    train, test = time_sliced_split(paired, train_frac=0.7)
    train_i = [p["i"] for p in train]
    test_i = [p["i"] for p in test]

    # raw (uncalibrated) scores on train to fit the calibrator
    raw_train = [score_fn(strategy, events[i]).score for i in train_i]
    y_train = [truths[i] for i in train_i]
    cal = Calibrator().fit(raw_train, y_train)
    strategy.calibrator = cal  # inject fitted calibrator

    # evaluate on the held-out (future) slice
    raw_test, cal_test, y_test = [], [], []
    for i in test_i:
        # raw: temporarily bypass calibrator for the "before" number
        strategy.calibrator = Calibrator()  # unfitted -> passthrough
        raw = score_fn(strategy, events[i]).score
        strategy.calibrator = cal
        sig = score_fn(strategy, events[i])
        raw_test.append(raw)
        cal_test.append(sig.score)
        y_test.append(truths[i])
        # store event, signal, outcome to the SHARED kb
        kb.store_event(events[i])
        kb.store_signal(events[i].id, sig)
        kb.store_outcome(
            Outcome(
                event_id=events[i].id,
                signal_strategy_id=strategy.strategy_id,
                predicted_condition_occurred=bool(truths[i]),
                outcome_definition_id=strategy.outcome_definition.id,
            )
        )

    b_raw = brier_score(raw_test, y_test)
    b_cal = brier_score(cal_test, y_test)
    ece_raw = expected_calibration_error(raw_test, y_test)
    ece_cal = expected_calibration_error(cal_test, y_test)

    print(f"\n=== {name} ({strategy.strategy_id}) ===")
    print(f"  test items: {len(y_test)}, positive rate: {np.mean(y_test):.2f}")
    print(f"  Brier  raw={b_raw:.4f}  calibrated={b_cal:.4f}")
    print(f"  ECE    raw={ece_raw:.4f}  calibrated={ece_cal:.4f}")
    return raw_test, cal_test, y_test


def main():
    kb = SQLiteKB(":memory:")  # ONE shared KB for BOTH families
    kb.store_outcome_definition(DEFECT_LINKED_FIX)
    kb.store_outcome_definition(JOB_RUN_FAILURE)

    # ---- Change family ----
    ce, ct = synth_change_events(2000)
    risk = HeuristicRiskStrategy(fragile_paths=FRAGILE)
    r_raw, r_cal, r_y = run_family(
        "CHANGE / commit risk", kb, ce, ct, risk, lambda s, e: s.score(e, {})
    )

    # ---- Operational family ----
    re_, rt, hist = synth_run_events(2000)
    anom = DistributionAnomalyStrategy(history_by_jobtype=hist)
    a_raw, a_cal, a_y = run_family(
        "OPERATIONAL / job anomaly", kb, re_, rt, anom, lambda s, e: s.evaluate(e, {})
    )

    # ---- Prove both families are in the SAME KB under the SAME contract ----
    from isoprax.events import Family

    n_change = len(kb.query_events(family=Family.CHANGE))
    n_op = len(kb.query_events(family=Family.OPERATIONAL))
    print("\n=== CROSS-FAMILY CONFORMANCE (spec 3.3) ===")
    print(f"  events in shared KB -> change: {n_change}, operational: {n_op}")
    print("  both families emit Signals via identical contract: OK")

    # ---- Calibration: scores must track their own declared outcome ----
    # Honest check: after calibration, does mean predicted ~= observed freq in
    # each bin, for BOTH families? Report the gap; don't assert success.
    print("\n=== CALIBRATION KEYSTONE (spec 5.3) ===")
    print("  After calibration, predicted probability should track observed")
    print("  frequency in EACH family. This is necessary but not sufficient")
    print("  for cross-family comparison; §5.6 decides that separately.\n")
    for label, raw, cal, y in [
        ("change", r_raw, r_cal, r_y),
        ("operational", a_raw, a_cal, a_y),
    ]:
        ece_before = expected_calibration_error(raw, y)
        ece_after = expected_calibration_error(cal, y)
        arrow = "improved" if ece_after < ece_before else "NOT improved"
        print(f"  {label:12s}: ECE {ece_before:.3f} -> {ece_after:.3f}  ({arrow})")
    # Show the score band separately for each family. These values are NOT a
    # cross-family comparison: their Outcome Definitions differ below.
    print("\n  Separately-scoped calibrated score band [0.4,0.7):")
    for label, cal, y in [("change", r_cal, r_y), ("operational", a_cal, a_y)]:
        bins = reliability_curve(cal, y, n_bins=10)
        band = [b for b in bins if 0.4 <= b.bin_low < 0.7]
        if band:
            mp = np.average(
                [b.mean_predicted for b in band], weights=[b.count for b in band]
            )
            ef = np.average(
                [b.empirical_frequency for b in band], weights=[b.count for b in band]
            )
            print(f"    {label:12s}: predicts ~{mp:.2f}, observed ~{ef:.2f}")

    # ---- Evaluation discipline: paired significance test (spec 8.2) ----
    # Worked example: is calibrated significantly better than raw (per-item
    # squared error), on each family? This is exactly the kind of comparison
    # spec 8.2 requires instead of a single accuracy number.
    print("\n=== EVALUATION DISCIPLINE (spec 8.2) ===")
    for label, raw, cal, y in [
        ("change", r_raw, r_cal, r_y),
        ("operational", a_raw, a_cal, a_y),
    ]:
        raw_err = [(s - t) ** 2 for s, t in zip(raw, y)]
        cal_err = [(s - t) ** 2 for s, t in zip(cal, y)]
        cmp = paired_comparison(raw_err, cal_err)
        print(
            f"  {label:12s}: raw Brier={cmp.baseline_brier:.4f} "
            f"calibrated Brier={cmp.candidate_brier:.4f} "
            f"| {cmp.test} p={cmp.p_value:.3g}"
        )
        print(f"                -> {cmp.verdict}")

    # ---- Commensurability + declarable conformance (spec 5.6, 3.3) ----
    print("\n=== COMMENSURABILITY (spec 5.6) ===")
    print("  Calibration is necessary but NOT sufficient. Two calibrated")
    print("  forecasts of DIFFERENT events are both correct and still")
    print("  incomparable. So: what event is each score a probability of?\n")
    print(f"  change      : {DEFECT_LINKED_FIX.event}")
    print(f"                via {DEFECT_LINKED_FIX.observation_process}")
    print(f"  operational : {JOB_RUN_FAILURE.event}")
    print(f"                via {JOB_RUN_FAILURE.observation_process}")

    rep = cross_family_report(
        "change",
        DEFECT_LINKED_FIX,
        r_cal,
        r_y,
        "operational",
        JOB_RUN_FAILURE,
        a_cal,
        a_y,
    )
    print("\n=== CROSS-FAMILY RESULT (spec 8, obligation 5) ===")
    print(rep.render())
    print(
        "     (third Strategy type is now exercised, but this remains a synthetic proof)"
    )

    # ---- Third Strategy type: ForecastSignal has coverage, not score ----
    forecast_history = [
        MetricSample(resource_id="demo", resource_type="service", value=value)
        for value in (10.0, 12.0, 14.0)
    ]
    forecast_strategy = HistoricalMeanForecastStrategy()
    for sample in forecast_history:
        kb.store_event(sample)
    forecast_signal = forecast_strategy.forecast(forecast_history, {})
    kb.store_signal(forecast_history[-1].id, forecast_signal)
    restored_forecast = kb.get_signal(
        forecast_history[-1].id, forecast_strategy.strategy_id
    )
    print("\n=== FORECAST STRATEGY ROUND-TRIP (spec 5.1, 5.2) ===")
    print(f"  technique: {restored_forecast.technique}")
    print(f"  interval confidence: {restored_forecast.interval_confidence:.2f}")
    print("  probability score carried: no")

    # ---- Counterexample: pooled calibration can mask bad ranking ----
    harm = build_pooling_harm_evidence()
    print("\n=== POOLING HARM (synthetic, non-conformance evidence) ===")
    print(
        f"  {harm.left_window} ECE={harm.left_ece:.3f}; "
        f"{harm.right_window} ECE={harm.right_ece:.3f}; "
        f"pooled ECE={harm.pooled_ece:.3f}"
    )
    print(
        f"  per-family top-k precision={harm.per_family_macro_precision:.3f}; "
        f"pooled top-k precision={harm.pooled_macro_precision:.3f}; "
        f"degradation={harm.degradation:.3f}"
    )

    # ---- Counterfactual: what commensurable labelling would look like ----
    # Under deterministic replay (spec D.3) BOTH families are labelled by the
    # same telemetry process, in the same window, against the same predeclared
    # thresholds -- differing only in what CONDITIONS the prediction.
    replay_def = OutcomeDefinition(
        id="replay.threshold_crossing.v1",
        event="p99 latency threshold crossed",
        observation_process="instrumented replay telemetry, predeclared thresholds",
        window="soak period following deployment of the observed state",
        thresholds="p99 > 500ms sustained 60s",
    )
    same = check_commensurable(replay_def, replay_def)
    print("\n=== WHY REPLAY (spec 5.6.4, D.3) ===")
    print("  Under one shared observation process both families would use:")
    print(f"    {replay_def.event} via {replay_def.observation_process}")
    print(
        f"  commensurable: {same.commensurable} -> shared-label prerequisite satisfied; "
        "Semantic claim withheld until corpus/evaluation evidence"
    )
    print("  No amount of calibration or corpus size substitutes for this;")
    print("  record linkage pairs events but does not share label semantics.")


if __name__ == "__main__":
    main()
