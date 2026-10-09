from __future__ import annotations

import json

import pytest

from scripts import model_role_metrics as metrics
from scripts.model_role_experiment import (
    ExperimentError,
    ModelRoleClient,
    OllamaClient,
    _native_probabilities,
    _pin_models,
    _relevance_state,
    run_suite,
)


def _preregistration() -> dict[str, object]:
    models = {
        key: {
            "requested_tag": f"{key}:requested",
            "api_model": f"{key}:resolved",
            "tag": f"{key}:requested",
            "manifest_sha256": f"{i:064x}",
        }
        for i, key in enumerate(
            ("qwen", "gemma", "coder", "embedding", "tev1", "guardian"), 1
        )
    }
    return {
        "study_id": "test-model-role",
        "status": "frozen before scored calls",
        "frozen_date": "2026-10-08",
        "service_version": "0.40.1",
        "models": models,
        "seeds": {"tev1_cases": 47060, "relevance_cases": 47061, "calls": 47069},
    }


class FakeClient:
    def __init__(self, prereg: dict[str, object]) -> None:
        self.prereg = prereg
        self.pinned_tags: dict[str, str] = {}

    def server_version(self) -> str:
        return "0.40.1"

    def model_digests(self, tags: dict[str, str]) -> dict[str, str]:
        self.pinned_tags = tags.copy()
        return {
            key: self.prereg["models"][key]["manifest_sha256"]  # type: ignore[index]
            for key in tags
        }

    def system_one(
        self, model: str, state: object, questions: dict[str, object], seed: int
    ) -> dict[str, object]:
        del model, state, seed
        if set(questions) == {"outcome"}:
            question = questions["outcome"]
            if question["type"] == "noul":  # type: ignore[index]
                answer = {"noul": 0.5}
            elif question["type"] == "choice":  # type: ignore[index]
                labels = list(question["criteria"])  # type: ignore[index]
                answer = {"probabilities": {label: 1 / len(labels) for label in labels}}
            else:
                answer = {"probabilities": [0.25] * 4}
            return {"answers": {"outcome": answer}}
        return {"answers": {item_id: {"noul": 0.4} for item_id in questions}}

    def chat(self, model: str, system: str, user: str, seed: int) -> str:
        del user, seed
        del system
        items = [
            {"item_id": item_id, "relevant": False, "probability": 0.4}
            for item_id in metrics.ITEM_IDS
        ]
        return json.dumps({"items": items})

    def chat_messages(
        self,
        model: str,
        messages: list[dict[str, str]],
        seed: int,
        json_output: bool = False,
    ) -> str:
        del model, messages, seed, json_output
        return "<score>no</score>"

    def embed(self, model: str, inputs: list[str]) -> list[list[float]]:
        del model
        return [[1.0, float(sum(map(ord, text)) % 997 + 1)] for text in inputs]


def test_fixture_generation_is_deterministic_balanced_and_label_separated() -> None:
    first_tev = metrics.generate_tev1_cases()
    second_tev = metrics.generate_tev1_cases()
    assert metrics.digest_json(first_tev) == metrics.digest_json(second_tev)
    assert len(first_tev) == 192
    for family in metrics.TEV1_FAMILIES:
        rows = [row for row in first_tev if row["family"] == family]
        assert len(rows) == 64
        assert sum(row["split"] == "development" for row in rows) == 32
        assert sum(row["split"] == "heldout" for row in rows) == 32

    cases = metrics.generate_relevance_cases()
    assert metrics.digest_json(cases) == metrics.digest_json(
        metrics.generate_relevance_cases()
    )
    assert len(cases) == 128
    assert all(len(case["items"]) == 8 for case in cases)
    assert all(sum(item["relevant"] for item in case["items"]) == 3 for case in cases)
    state = _relevance_state(cases[0])
    assert "source_status" not in json.dumps(state)
    assert "operation_use" not in json.dumps(state)
    assert "relevant" not in json.dumps(state)


def test_parsers_preserve_native_score_types_and_reject_bad_outputs() -> None:
    ids = list(metrics.ITEM_IDS)
    chat = json.dumps(
        {
            "items": [
                {"item_id": item_id, "relevant": item_id == "E01", "probability": 0.7}
                for item_id in ids
            ]
        }
    )
    parsed = metrics.parse_chat_items(chat, ids)
    assert parsed[0]["score_type"] == "self_reported_relevance_probability"
    guardian = metrics.parse_guardian_score("<score>yes</score>")
    assert guardian["score_type"] == "binary_critic_judgment"
    with pytest.raises(ValueError, match="probability"):
        metrics.parse_chat_items(
            chat.replace('"probability": 0.7', '"probability": 1.2', 1), ids
        )
    with pytest.raises(ValueError, match="documented yes/no"):
        metrics.parse_guardian_score("probably yes")


def test_tev1_probability_parser_uses_native_distributions() -> None:
    binary = metrics.generate_tev1_cases()[0]
    assert _native_probabilities({"noul": 0.8}, binary) == pytest.approx([0.2, 0.8])
    categorical = next(
        row
        for row in metrics.generate_tev1_cases()
        if row["family"] == "software_category"
    )
    probs = {label: 0.25 for label in categorical["class_labels"]}
    assert _native_probabilities(
        {"probabilities": probs}, categorical
    ) == pytest.approx([0.25] * 4)
    with pytest.raises(ValueError, match="sum to one"):
        _native_probabilities({"probabilities": [0.1, 0.1, 0.1, 0.1]}, categorical)


def test_calibration_fits_only_development_scores() -> None:
    dev = [
        {"raw_score": score, "gold": gold, "valid": True}
        for score, gold in ((0.1, False), (0.2, False), (0.8, True), (0.9, True))
    ]
    fitted = metrics.fit_calibration(dev)
    p = metrics.apply_calibration(0.7, fitted)
    assert p is not None and p > 0.5
    assert (
        metrics.fit_calibration([{"raw_score": 0.3, "gold": True, "valid": True}])[
            "available"
        ]
        is False
    )


def test_ranking_refuses_incomplete_query_and_reports_coverage() -> None:
    rows = [
        {
            "query_id": "Q1",
            "item_id": item_id,
            "gold": item_id == "E01",
            "raw_score": 0.5,
            "valid": True,
        }
        for item_id in metrics.ITEM_IDS[:-1]
    ]
    result = metrics.ranking_metrics(rows)
    assert result["ranked_query_count"] == 0
    assert result["incomplete_query_count"] == 1
    assert result["query_coverage"] == 0


def test_model_pin_fails_closed_when_a_role_digest_is_missing() -> None:
    prereg = _preregistration()
    prereg["models"]["embedding"]["manifest_sha256"] = None  # type: ignore[index]
    with pytest.raises(ExperimentError, match="exact manifest digest"):
        _pin_models(FakeClient(prereg), prereg)


def test_model_pin_uses_resolved_api_model_not_requested_tag() -> None:
    prereg = _preregistration()
    client = FakeClient(prereg)

    _pin_models(client, prereg)

    assert client.pinned_tags == {
        key: prereg["models"][key]["api_model"]  # type: ignore[index]
        for key in ("qwen", "gemma", "coder", "embedding", "tev1", "guardian")
    }


def test_model_digests_rejects_ambiguous_duplicate_tag_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = OllamaClient()

    def fake_request(route: str, payload: dict[str, object] | None = None):
        del payload
        if route == "/api/show":
            return {"manifests": []}
        if route == "/api/tags":
            return {
                "models": [
                    {"name": "gemma4:e4b", "digest": "a" * 64},
                    {"name": "gemma4:e4b", "digest": "b" * 64},
                ]
            }
        raise AssertionError(f"unexpected route: {route}")

    monkeypatch.setattr(client, "_request", fake_request)
    with pytest.raises(ExperimentError, match="cannot resolve one selected manifest"):
        client.model_digests({"gemma": "gemma4:e4b"})


def test_model_client_rejects_non_loopback_hosts() -> None:
    with pytest.raises(ExperimentError, match="local Ollama"):
        OllamaClient("https://example.com")


def test_synthetic_end_to_end_keeps_targets_pools_and_digests() -> None:
    prereg = _preregistration()
    result = run_suite(FakeClient(prereg), prereg)
    assert result["evidence_class"] == "synthetic"
    assert set(result["tev1_summary"]) >= set(metrics.TEV1_FAMILIES)
    assert result["tev1_summary"]["declared_mixture"]["weights"] == {
        family: 1 / 3 for family in metrics.TEV1_FAMILIES
    }
    relevance = result["relevance_summary"]
    assert set(relevance["judge_pools"]) == {
        "majority_label",
        "equal_weight_calibrated_probability",
    }
    for pool in relevance["judge_pools"].values():
        assert pool["domain_weights"] == {domain: 0.25 for domain in metrics.DOMAINS}
        assert pool["coverage_by_domain"] == {domain: 1.0 for domain in metrics.DOMAINS}
        assert set(pool["heldout_by_domain"]) == set(metrics.DOMAINS)
        assert set(pool["equal_weight_domain_mixture"]) >= {"brier", "log_loss", "auc"}
    assert set(relevance["coder_by_domain"]) == set(metrics.DOMAINS)
    assert set(result["judgment_dependence"]) == {
        "qwen+gemma",
        "qwen+guardian",
        "gemma+guardian",
    }
    assert result["case_set_sha256"]
    assert result["predictions_sha256"]

    embedding_key = next(
        key for key in result["raw_responses"] if key.startswith("embedding:")
    )
    vectors = json.loads(result["raw_responses"][embedding_key])
    assert len(vectors) == 9
    assert all(len(vector) == 2 for vector in vectors)
    embedding_rows = [
        row for row in result["relevance_rows"] if row["model"] == "embedding"
    ]
    assert all("raw_response" not in row for row in embedding_rows)
    assert all(row["raw_response_sha256"] for row in embedding_rows)


def test_mixed_backend_client_pins_ollama_manifests_and_embedding_identity() -> None:
    class FakeEmbedding:
        identity_sha256 = "e" * 64

        def embed(self, inputs: list[str]) -> list[list[float]]:
            return [[1.0] for _ in inputs]

        def runtime_metadata(self) -> dict[str, str]:
            return {"backend": "sentence-transformers-cpu"}

    class FakeOllama:
        def __init__(self) -> None:
            self.pinned_tags: dict[str, str] = {}

        def model_digests(self, tags: dict[str, str]) -> dict[str, str]:
            self.pinned_tags = tags.copy()
            return {key: f"{index:064x}" for index, key in enumerate(tags, 1)}

    prereg = _preregistration()
    models = prereg["models"]
    models["embedding"].update(
        {
            "backend": "sentence-transformers-cpu",
            "api_model": "google/embeddinggemma-2@revision",
        }
    )
    ollama = FakeOllama()
    client = ModelRoleClient(ollama, FakeEmbedding(), models)

    digests = client.model_digests(
        {key: value["api_model"] for key, value in models.items()}
    )

    assert set(ollama.pinned_tags) == {"qwen", "gemma", "coder", "tev1", "guardian"}
    assert digests["embedding"] == "e" * 64
    assert client.embed("google/embeddinggemma-2@revision", ["query"]) == [[1.0]]
    assert client.embedding_runtime_metadata() == {
        "backend": "sentence-transformers-cpu"
    }
