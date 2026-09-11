from isoprax.admission import SplitDefinition
from isoprax.commensurability import OutcomeDefinition
from isoprax.corpus_assembly import (
    CorpusAssemblyProfile,
    ReplayCaptureInput,
    assemble_corpus,
)
from isoprax.replay_capture import (
    DeploymentEvidence,
    ObservationArtifactEvidence,
    ObservationEvidence,
    ReplayCaptureRecord,
    ReplayLaneDefinition,
)
from isoprax.stage2_corpus_evaluation import (
    CorpusEvaluationProfile,
    evaluate_stage2_corpus,
)


def _definition(identifier: str) -> OutcomeDefinition:
    return OutcomeDefinition(
        identifier,
        "latency threshold crossed",
        {"kind": "shared-http", "parameters": {"endpoint": "/bench"}},
        {"duration": 10, "unit": "minute", "anchor": "score_time"},
        ({"metric": "p99", "operator": ">", "value": 0.5},),
    )


def _capture(index: int, outcome: str) -> ReplayCaptureRecord:
    commit = f"commit-{index}"
    score_time = f"2026-04-{index + 1:02d}T00:00:00Z"
    lane = ReplayLaneDefinition(
        "public-system",
        "public-service",
        commit,
        "fixed-http-workload",
        "PT10M",
        "threshold-v1",
        "capture-v1",
        "public-replay",
        score_time,
        score_time,
        f"2026-04-{index + 1:02d}T00:10:00Z",
    )
    observation = ObservationEvidence(
        score_time,
        score_time,
        f"2026-04-{index + 1:02d}T00:10:00Z",
        True,
        True,
        True,
        outcome == "observed_positive",
        False,
        False,
        "public-replay",
        ("metrics.json",),
        {"metrics.json": b"public-metrics"},
        "integration fixture",
    )
    return ReplayCaptureRecord(
        f"lane-{commit}",
        lane,
        f"qualification-{commit}",
        f"execution-{commit}",
        DeploymentEvidence(
            f"target-{commit}",
            commit,
            "succeeded",
            score_time,
            score_time,
            f"deploy://{commit}",
        ),
        observation,
        (ObservationArtifactEvidence("metrics.json", "collected", "a" * 64, 14),),
        outcome,
        None,
    )


def test_replay_capture_assembly_feeds_stage2_corpus_gate():
    split_definitions = (
        SplitDefinition(
            "train", "2026-01-01T00:00:00+00:00", "2026-02-01T00:00:00+00:00"
        ),
        SplitDefinition(
            "calibration_fit",
            "2026-02-01T00:00:00+00:00",
            "2026-03-01T00:00:00+00:00",
        ),
        SplitDefinition(
            "calibration_gate",
            "2026-03-01T00:00:00+00:00",
            "2026-03-31T00:00:00+00:00",
        ),
        SplitDefinition(
            "test", "2026-03-31T00:00:00+00:00", "2026-05-01T00:00:00+00:00"
        ),
    )
    assembly = assemble_corpus(
        CorpusAssemblyProfile(
            "public-system",
            "PT10M",
            "threshold-v1",
            "public-replay",
            frozenset({"change_score", "operational_score"}),
            frozenset({"post_score_latency"}),
            split_definitions,
            ("corpus.json",),
        ),
        tuple(
            ReplayCaptureInput(
                _capture(index, outcome),
                {
                    "change_score": score,
                    "operational_score": score,
                },
                {
                    "change_score": "2025-12-31T00:00:00Z",
                    "operational_score": "2025-12-31T00:00:00Z",
                },
            )
            for index, (score, outcome) in enumerate(
                (
                    (0.25, "observed_positive"),
                    (0.25, "observed_negative"),
                    (0.25, "observed_negative"),
                    (0.25, "observed_negative"),
                    (0.75, "observed_positive"),
                    (0.75, "observed_positive"),
                    (0.75, "observed_positive"),
                    (0.75, "observed_negative"),
                )
            )
        ),
    )

    assert assembly.rejections == ()
    report = evaluate_stage2_corpus(
        assembly.rows,
        CorpusEvaluationProfile(
            "public-system",
            "feasibility-report-id",
            "predeclared-hash",
            "corpus-hash",
            _definition("change-definition"),
            _definition("operational-definition"),
            "change_score",
            "operational_score",
            "PT10M",
            "threshold-v1",
            "public-replay",
            ("corpus.json", "report.json"),
            8,
            4,
            4,
        ),
    )

    assert report.status == "qualified"
    assert report.counts["selected"] == 8
