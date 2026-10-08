from __future__ import annotations

import json

import pytest

from scripts.retrieval_dependence_experiment import (
    CAUSES,
    MODEL_DIGESTS,
    MODEL_X,
    MODEL_Y,
    ExperimentError,
    OllamaClient,
    _acceptable_abstention,
    _error_association,
    _interpretation_metrics,
    _item_map,
    _model_interpretation,
    _model_ranking,
    _policy_permission,
    _retrieval_metrics,
    _selector_pair_order,
    bm25_ranking,
    canonical_json,
    digest_json,
    evaluate_policies,
    finalize_replay,
    generate_cases,
    load_preregistration,
    selector_prompt,
    validate_case_set,
)


class FakeClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def model_digests(self) -> dict[str, str]:
        return MODEL_DIGESTS.copy()

    def chat(
        self,
        model: str,
        system: str,
        user: str,
        seed: int,
        num_predict: int = 256,
    ) -> dict[str, object]:
        del model, seed, num_predict
        self.prompts.append(user)
        if "evidence selector" in system:
            value = json.loads(user)
            ranking = [item["item_id"] for item in value["items"]]
            return {
                "content": json.dumps({"ranking": ranking}),
                "prompt_eval_count": 100,
                "eval_count": 20,
            }
        return {
            "content": json.dumps({"ranking": list(CAUSES), "abstain": False}),
            "prompt_eval_count": 100,
            "eval_count": 20,
        }


def test_case_generator_is_fixed_stratified_and_keeps_labels_separate() -> None:
    first = generate_cases()
    second = generate_cases()

    assert len(first) == 36
    assert digest_json(first) == digest_json(second)
    assert {
        split: sum(case["split"] == split for case in first)
        for split in {"development", "rule_authoring", "heldout"}
    } == {
        "development": 6,
        "rule_authoring": 6,
        "heldout": 24,
    }
    assert all(len(case["items"]) == 16 for case in first)
    assert all(case["gold_root_cause"] in CAUSES for case in first)
    validate_case_set(first)


def test_preregistration_pins_current_models_and_analysis() -> None:
    preregistration = load_preregistration()

    assert preregistration["models"]["X"]["tag"] == MODEL_X
    assert (
        preregistration["models"]["X"]["ollama_manifest_sha256"]
        == MODEL_DIGESTS[MODEL_X]
    )
    assert preregistration["case_design"]["case_count"] == 36
    assert preregistration["case_design"]["budgets"] == [1, 2, 4, 8, 16]


def test_model_client_rejects_nonlocal_endpoints() -> None:
    with pytest.raises(ExperimentError, match="only to a local"):
        OllamaClient("https://example.com")


def test_selector_prompt_contains_no_gold_or_source_status_labels() -> None:
    case = generate_cases()[0]
    system, prompt = selector_prompt(case)
    combined = system + prompt

    assert "source_status" not in combined
    assert "gold_root_cause" not in combined
    assert "operation_use_labels" not in combined
    assert "supports_claim" not in combined
    assert all(item["item_id"] in prompt for item in case["items"])


def test_bm25_is_a_complete_deterministic_ranking() -> None:
    case = generate_cases()[0]
    first = bm25_ranking(case)
    second = bm25_ranking(case)

    assert first == second
    assert len(first["ranking"]) == 16
    assert set(first["ranking"]) == {item["item_id"] for item in case["items"]}
    assert len(first["scores"]) == 16
    assert first["score_basis"].startswith("BM25 raw score")


def test_prompted_selector_records_model_output_and_exact_rank_order() -> None:
    client = FakeClient()
    case = generate_cases()[0]
    result = _model_ranking(client, MODEL_X, case)

    assert result["ranking"] == [item["item_id"] for item in case["items"]]
    assert result["prompt_sha256"]
    assert result["prompt_eval_count"] == 100
    assert result["attempts"][0]["content"]


def test_interpreter_metrics_separate_wrong_answers_and_acceptable_abstention() -> None:
    case = next(case for case in generate_cases() if case["split"] == "heldout")
    item_by_id = _item_map(case)
    selected = [item_by_id[item_id] for item_id in case["gold_required_items"]]
    wrong_cause = next(cause for cause in CAUSES if cause != case["gold_root_cause"])
    wrong = {
        "ranking": [wrong_cause, *[cause for cause in CAUSES if cause != wrong_cause]],
        "abstain": False,
        "answer": wrong_cause,
    }
    metrics = _interpretation_metrics(case, selected, wrong)

    assert metrics["false_belief"] is True
    assert metrics["interpretation_error"] is True
    assert _acceptable_abstention(case, selected) is False


def test_interpreter_client_returns_a_complete_locked_ranking() -> None:
    client = FakeClient()
    case = next(case for case in generate_cases() if case["split"] == "heldout")
    selected = [
        item for item in case["items"] if item["item_id"] in case["gold_required_items"]
    ]
    result = _model_interpretation(client, MODEL_X, case, selected)

    assert set(result["ranking"]) == set(CAUSES)
    assert result["abstain"] is False
    assert result["prompt_eval_count"] == 100


def test_retrieval_metrics_use_required_items_and_misleading_rank() -> None:
    case = next(
        case
        for case in generate_cases()
        if case["stratum"] == "misleading" and case["split"] == "heldout"
    )
    required = case["gold_required_items"]
    misleading = next(
        item["item_id"] for item in case["items"] if item["misleading_label"]
    )
    remainder = [
        item["item_id"]
        for item in case["items"]
        if item["item_id"] not in {*required, misleading}
    ]
    ranking = [misleading, required[0], *remainder, required[1]]
    metrics = _retrieval_metrics(case, ranking, 4)

    assert metrics["missing_required"] is True
    assert metrics["misleading_outranks_decisive"] is True
    assert metrics["retrieval_error"] is True


def test_error_association_reports_conditional_denominators() -> None:
    rows = [
        {
            "retrieval": {"retrieval_error": True},
            "interpretation": {"interpretation_error": True},
        },
        {
            "retrieval": {"retrieval_error": True},
            "interpretation": {"interpretation_error": False},
        },
        {
            "retrieval": {"retrieval_error": False},
            "interpretation": {"interpretation_error": False},
        },
        {
            "retrieval": {"retrieval_error": False},
            "interpretation": {"interpretation_error": False},
        },
    ]

    result = _error_association(rows)
    assert result["retrieval_error_n"] == 2
    assert result["no_retrieval_error_n"] == 2
    assert result["p_interpretation_error_given_retrieval_error"] == 0.5
    assert result["p_interpretation_error_given_no_retrieval_error"] == 0
    assert result["conditional_risk_difference"] == 0.5


def test_operation_specific_policy_uses_operation_and_lineage_metadata() -> None:
    case = next(
        case
        for case in generate_cases()
        if case["stratum"] == "clean"
        and case["split"] == "heldout"
        and case["audit"]["independent_review_pass"]
    )
    item_by_id = _item_map(case)
    selected = [item_by_id[item_id] for item_id in case["gold_required_items"]]

    assert _policy_permission("naive_aggregation", case, selected, MODEL_X, MODEL_X)
    assert not _policy_permission("global_label", case, selected, MODEL_X, MODEL_X)
    assert not _policy_permission("metadata_only", case, selected, MODEL_X, MODEL_X)
    assert _policy_permission("operation_specific", case, selected, MODEL_X, MODEL_X)
    evaluated = evaluate_policies(
        case,
        selected,
        MODEL_X,
        MODEL_X,
        {item["item_id"]: 1.0 for item in selected},
        False,
    )
    assert evaluated["operation_specific"]["expected_permission"] is True
    assert evaluated["operation_specific"]["unnecessary_refusal"] is False


def test_operation_specific_counts_disjoint_upstream_sources_once() -> None:
    case = next(
        case
        for case in generate_cases()
        if case["stratum"] == "clean"
        and case["split"] == "heldout"
        and case["audit"]["independent_review_pass"]
    )
    item_by_id = _item_map(case)
    first_required = item_by_id[case["gold_required_items"][0]]
    duplicate = dict(first_required)
    duplicate["item_id"] = f"{case['case_id']}-duplicate-vote"
    selected = [*case["items"], duplicate]
    scores = {item["item_id"]: 10.0 for item in selected}
    for item_id in case["gold_required_items"]:
        scores[item_id] = 1.0
    scores[duplicate["item_id"]] = 100.0

    evaluated = evaluate_policies(
        case,
        selected,
        MODEL_X,
        MODEL_Y,
        scores,
        False,
    )

    assert evaluated["operation_specific"]["permission"] is True
    assert evaluated["operation_specific"]["decision"] == case["gold_root_cause"]
    assert evaluated["metadata_only"]["permission"] is False


def test_policy_rules_reject_overlapping_upstream_lineage_as_independent() -> None:
    case = next(
        case
        for case in generate_cases()
        if case["stratum"] == "clean"
        and case["split"] == "heldout"
        and case["audit"]["independent_review_pass"]
    )
    item_by_id = _item_map(case)
    selected = [item_by_id[item_id] for item_id in case["gold_required_items"]]
    shared_root = selected[0]["upstream_source_ids"][0]
    selected[1]["upstream_source_ids"] = [shared_root, "additional-root"]

    assert not _policy_permission(
        "operation_specific", case, selected, MODEL_X, MODEL_Y
    )
    assert not _policy_permission("metadata_only", case, selected, MODEL_X, MODEL_Y)


def test_selector_pair_deduplicates_overlap_and_matches_realized_budget() -> None:
    left = {"ranking": ["a", "b", "c", "d"]}
    right = {"ranking": ["a", "e", "f", "g"]}

    pair, left_top, right_top = _selector_pair_order(left, right, 4)
    assert pair == ["a", "b", "e"]
    assert len(pair) == 3
    assert left_top == ["a", "b"]
    assert right_top == {"a", "e"}


def test_canonical_json_and_case_digest_are_stable() -> None:
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    with pytest.raises(ValueError):
        canonical_json({"not_finite": float("nan")})


def test_replay_finalizer_requires_identical_complete_results() -> None:
    run = {
        "case_set_sha256": "cases",
        "selection_trace_sha256": "selections",
        "hypothesis_assessment": {
            "H1_correlated_failure": {"single_run_gate_passed": True}
        },
    }

    exact = finalize_replay(run, json.loads(json.dumps(run)))
    assert exact["replay"]["complete_result_match"] is True
    assert exact["hypothesis_assessment"]["H1_correlated_failure"]["status"] == (
        "supported in this bounded synthetic pilot"
    )

    changed = json.loads(json.dumps(run))
    changed["selection_trace_sha256"] = "different"
    mismatch = finalize_replay(run, changed)
    assert mismatch["replay"]["complete_result_match"] is False
    assert mismatch["replay"]["second_run_result"] == changed
