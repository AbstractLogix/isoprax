"""Build the frozen, internally authored operation-policy challenge cases."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PATH = ROOT / "docs/experiments/operation-policy-challenge-v2-public.jsonl"
EVALUATOR_PATH = ROOT / "docs/experiments/operation-policy-challenge-v2-evaluator.jsonl"


def _source(
    source_id: str,
    *,
    target: str,
    event: str,
    score: float,
    semantics: str,
    revision: str = "model-v1",
    process: str = "observed-process-v1",
    window: str = "window-1",
    status: str = "verified",
    lineage: str | None = None,
    calibration: dict[str, str] | None = None,
    mapped_score: float | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "target_id": target,
        "event_id": event,
        "observation_process": process,
        "observation_window": window,
        "score": score,
        "score_semantics": semantics,
        "model_revision": revision,
        "source_status": status,
        "lineage_group": lineage or source_id,
        "conflict": False,
        "calibration": calibration,
        "mapped_score": mapped_score,
        "global_label": semantics,
    }


def _cal(
    target: str, revision: str = "model-v1", split: str = "development"
) -> dict[str, str]:
    return {"target_id": target, "model_revision": revision, "split": split}


def _record(
    case_id: str,
    operation: str,
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
    expected_permission: bool,
    expected_decision: bool | None = None,
    expected_ranking: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    public = {
        "case_id": case_id,
        "operation": operation,
        "left": left,
        "right": right,
        "context": context or {},
    }
    evaluator = {
        "case_id": case_id,
        "expected_permission": expected_permission,
        "expected_decision": expected_decision,
        "expected_ranking": expected_ranking,
    }
    return public, evaluator


def build_cases() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    public: list[dict[str, Any]] = []
    evaluator: list[dict[str, Any]] = []

    forecast_target = "forecast:rain-24h"
    forecast_event = "rain-at-least-10mm"
    fleft = _source(
        "f-left",
        target=forecast_target,
        event=forecast_event,
        score=0.72,
        semantics="probability",
        calibration=_cal(forecast_target),
    )
    fright = _source(
        "f-right",
        target=forecast_target,
        event=forecast_event,
        score=0.61,
        semantics="probability",
        calibration=_cal(forecast_target),
        revision="model-v2",
    )
    forecasts = [
        (
            True,
            {
                "right": {
                    "model_revision": "model-v1",
                    "calibration": _cal(forecast_target),
                }
            },
            True,
            True,
        ),
        (True, {"right": {"score": 0.48}}, True, False),
        (
            True,
            {
                "right": {
                    "target_id": "forecast:snow-24h",
                    "event_id": "snow-at-least-5cm",
                    "calibration": _cal("forecast:snow-24h"),
                    "score": 0.81,
                },
                "context": {
                    "mixture_estimand": "mixture:regional-weather",
                    "weights": [0.5, 0.5],
                },
            },
            True,
            True,
        ),
        (
            True,
            {
                "right": {
                    "model_revision": "model-v3",
                    "calibration": _cal(forecast_target, "model-v3"),
                }
            },
            True,
            True,
        ),
        (True, {"left": {"score": 0.41}, "right": {"score": 0.35}}, True, False),
        (
            True,
            {
                "right": {
                    "target_id": "forecast:wind-24h",
                    "event_id": "wind-gust-50kmh",
                    "calibration": _cal("forecast:wind-24h"),
                    "score": 0.54,
                },
                "context": {
                    "mixture_estimand": "mixture:regional-hazards",
                    "weights": [0.25, 0.75],
                },
            },
            True,
            True,
        ),
        (
            False,
            {
                "right": {
                    "target_id": "forecast:snow-24h",
                    "event_id": "snow-at-least-5cm",
                    "calibration": _cal("forecast:snow-24h"),
                }
            },
            False,
            None,
        ),
        (False, {"right": {"observation_window": "window-7d"}}, False, None),
        (False, {"right": {"observation_process": "satellite-process"}}, False, None),
        (
            False,
            {
                "right": {
                    "model_revision": "model-v1",
                    "calibration": _cal(forecast_target, split="evaluation"),
                }
            },
            True,
            True,
        ),
        (
            False,
            {
                "right": {
                    "model_revision": "model-v1",
                    "calibration": _cal(forecast_target, "old-model"),
                }
            },
            True,
            False,
        ),
        (
            False,
            {
                "right": {
                    "score_semantics": "ordinal",
                    "global_label": "ordinal",
                    "calibration": _cal(forecast_target),
                }
            },
            True,
            True,
        ),
    ]
    for index, (valid, change, has_target_decision, truth) in enumerate(
        forecasts, start=1
    ):
        left, right = deepcopy(fleft), deepcopy(fright)
        context: dict[str, Any] = {"decision_threshold": 0.5}
        for side in ("left", "right"):
            if side in change:
                target = left if side == "left" else right
                target.update(change[side])
        context.update(change.get("context", {}))
        if not has_target_decision:
            context.pop("decision_threshold", None)
        pair = _record(
            f"FP{index:02d}",
            "forecast_pool",
            left,
            right,
            context=context,
            expected_permission=valid,
            expected_decision=truth if has_target_decision else None,
        )
        public.append(pair[0])
        evaluator.append(pair[1])

    relevance_target = "relevance:patch-fixes-bug"
    relevance_event = "patch-fixes-declared-bug"
    rleft = _source(
        "r-left",
        target=relevance_target,
        event=relevance_event,
        score=0.82,
        semantics="cosine",
        calibration=_cal(relevance_target),
        mapped_score=0.72,
    )
    rright = _source(
        "r-right",
        target=relevance_target,
        event=relevance_event,
        score=0.61,
        semantics="cosine",
        calibration=_cal(relevance_target, "model-v2"),
        revision="model-v2",
        mapped_score=0.43,
    )
    relevance = [
        (
            True,
            {
                "right": {
                    "model_revision": "model-v1",
                    "calibration": _cal(relevance_target),
                }
            },
            ["r-left", "r-right"],
        ),
        (
            True,
            {
                "right": {
                    "score_semantics": "bm25",
                    "global_label": "bm25",
                    "score": 3.2,
                    "calibration": _cal(relevance_target, "model-v2"),
                    "mapped_score": 0.91,
                }
            },
            ["r-right", "r-left"],
        ),
        (
            True,
            {
                "right": {
                    "model_revision": "model-v3",
                    "calibration": _cal(relevance_target, "model-v3"),
                    "mapped_score": 0.87,
                }
            },
            ["r-right", "r-left"],
        ),
        (
            True,
            {
                "left": {"lineage_group": "upstream-a"},
                "right": {"lineage_group": "upstream-b"},
            },
            ["r-left", "r-right"],
        ),
        (
            True,
            {
                "left": {
                    "score_semantics": "logit",
                    "global_label": "logit",
                    "score": 2.5,
                    "mapped_score": 0.69,
                }
            },
            ["r-left", "r-right"],
        ),
        (
            True,
            {
                "left": {"score": 0.94, "mapped_score": 0.22},
                "right": {"score": 0.32, "mapped_score": 0.81},
            },
            ["r-right", "r-left"],
        ),
        (
            False,
            {
                "right": {
                    "target_id": "relevance:other-bug",
                    "event_id": "patch-fixes-other-bug",
                    "calibration": _cal("relevance:other-bug"),
                }
            },
            None,
        ),
        (
            False,
            {"right": {"model_revision": "model-v1", "calibration": None}},
            ["r-left", "r-right"],
        ),
        (
            False,
            {
                "right": {
                    "model_revision": "model-v1",
                    "calibration": _cal(relevance_target, "model-v1", "evaluation"),
                }
            },
            ["r-left", "r-right"],
        ),
        (
            False,
            {
                "right": {
                    "model_revision": "model-v1",
                    "calibration": _cal(relevance_target, "old-model"),
                }
            },
            ["r-left", "r-right"],
        ),
        (False, {"right": {"source_status": "unknown"}}, ["r-left", "r-right"]),
        (False, {"right": {"event_id": "patch-reviews-bug"}}, None),
    ]
    for index, (valid, change, expected_order) in enumerate(relevance, start=1):
        left, right = deepcopy(rleft), deepcopy(rright)
        for side in ("left", "right"):
            if side in change:
                target = left if side == "left" else right
                target.update(change[side])
        pair = _record(
            f"RL{index:02d}",
            "relevance_rank",
            left,
            right,
            context={"ranking_estimand": relevance_target},
            expected_permission=valid,
            expected_ranking=expected_order,
        )
        public.append(pair[0])
        evaluator.append(pair[1])

    claim = "claim:root-cause-is-null-check"
    eleft = _source(
        "e-left",
        target=claim,
        event=claim,
        score=0.8,
        semantics="claim_support",
        process="document-review",
        window="revision-4",
        revision="qwen-v1",
        lineage="root-a",
    )
    eright = _source(
        "e-right",
        target=claim,
        event=claim,
        score=0.7,
        semantics="claim_support",
        process="test-review",
        window="revision-4",
        revision="gemma-v1",
        lineage="root-b",
    )
    evidence = [
        (
            True,
            {
                "right": {
                    "model_revision": "qwen-v1",
                    "observation_process": "document-review",
                }
            },
        ),
        (True, {"right": {"model_revision": "guardian-v2"}}),
        (
            True,
            {
                "right": {
                    "score_semantics": "test_result",
                    "global_label": "test_result",
                }
            },
        ),
        (True, {"right": {"observation_process": "independent-test"}}),
        (
            True,
            {"left": {"lineage_group": "root-c"}, "right": {"lineage_group": "root-d"}},
        ),
        (
            True,
            {
                "left": {"observation_window": "revision-5"},
                "right": {"observation_window": "revision-6"},
            },
        ),
        (False, {"right": {"lineage_group": "root-a"}}),
        (False, {"right": {"source_status": "unknown"}}),
        (
            False,
            {
                "right": {
                    "model_revision": "qwen-v1",
                    "observation_process": "document-review",
                    "observation_window": "revision-4",
                    "conflict": True,
                }
            },
        ),
        (
            False,
            {
                "right": {
                    "target_id": "claim:other-root-cause",
                    "event_id": "claim:other-root-cause",
                }
            },
        ),
        (False, {"left": {"source_status": "unverified"}}),
        (False, {"right": {"conflict": None}}),
    ]
    for index, (valid, change) in enumerate(evidence, start=1):
        left, right = deepcopy(eleft), deepcopy(eright)
        for side in ("left", "right"):
            if side in change:
                target = left if side == "left" else right
                target.update(change[side])
        pair = _record(
            f"EC{index:02d}",
            "evidence_combine",
            left,
            right,
            context={"claim_id": claim},
            expected_permission=valid,
        )
        public.append(pair[0])
        evaluator.append(pair[1])

    assert len(public) == len(evaluator) == 36
    assert len({row["case_id"] for row in public}) == 36
    return public, evaluator


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            for row in rows
        )
    )


def main() -> None:
    public, evaluator = build_cases()
    _write_jsonl(PUBLIC_PATH, public)
    _write_jsonl(EVALUATOR_PATH, evaluator)
    print(f"wrote {len(public)} public cases and {len(evaluator)} evaluator outcomes")


if __name__ == "__main__":
    main()
