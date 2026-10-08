"""Recompute a Bouleusis evidence-selection sweep from its JSONL event records."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/research/bouleusis-retrieval-sweep-reanalysis.json"
CONCRETE_HYPOTHESIS = re.compile(r"^The defect is in (.+)\.$")


def _read_jsonl(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], str, int]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    rows = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {line_number} is not an object")
        value["_line_number"] = line_number
        rows.append(value)
    metadata_rows = [row for row in rows if row.get("record_type") == "metadata"]
    run_rows = [row for row in rows if row.get("record_type") == "run"]
    unknown_rows = [
        row for row in rows if row.get("record_type") not in {"metadata", "run"}
    ]
    if len(metadata_rows) != 1 or not run_rows or unknown_rows:
        raise ValueError(
            f"Expected one metadata record and run records; got metadata={len(metadata_rows)}, "
            f"runs={len(run_rows)}, unknown={len(unknown_rows)}"
        )
    return metadata_rows[0], run_rows, digest, len(rows)


def _recompute_recall(run: dict[str, Any]) -> float:
    decisive = set(run["decisive_evidence_ids"])
    if not decisive:
        raise ValueError(f"Run {run['run_id']} has no decisive evidence IDs")
    selected = set(run["selected_evidence_ids"])
    return len(decisive & selected) / len(decisive)


def _recompute_success(run: dict[str, Any], target_path: str) -> bool:
    success = bool(
        not run["abstained"]
        and run["final_tests_passed"]
        and run["final_diagnosis"] == target_path
    )
    completed = [
        event["payload"]["success"]
        for event in run["events"]
        if event["kind"] == "run_completed"
    ]
    if len(completed) != 1 or bool(completed[0]) != bool(run["final_tests_passed"]):
        raise ValueError(
            f"Run {run['run_id']} final test result does not match run_completed event"
        )
    return success


def _recompute_false_beliefs(
    run: dict[str, Any], target_path: str
) -> list[dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    events = run["events"]
    expected_sequences = list(range(1, len(events) + 1))
    if [event["sequence"] for event in events] != expected_sequences:
        raise ValueError(f"Run {run['run_id']} has a non-contiguous event sequence")

    for event in events:
        if event["run_id"] != run["run_id"]:
            raise ValueError(f"Run {run['run_id']} contains a mismatched event run_id")
        payload = event["payload"]
        if event["kind"] == "claim_proposed":
            states[payload["claim_id"]] = {
                "proposition": payload["proposition"],
                "confidence": payload["confidence"],
                "status": payload["status"],
            }
        elif event["kind"] in {"belief_updated", "claim_retracted"}:
            state = states.get(payload.get("claim_id"))
            if state is not None:
                state["confidence"] = payload.get("new_confidence", state["confidence"])
                state["status"] = payload.get("new_status", state["status"])

    false_claims = []
    for claim_id, state in states.items():
        match = CONCRETE_HYPOTHESIS.fullmatch(state["proposition"])
        if (
            match is not None
            and match.group(1) != target_path
            and state["status"] == "supported"
            and float(state["confidence"]) > 0
        ):
            false_claims.append(
                {
                    "claim_id": claim_id,
                    "confidence": float(state["confidence"]),
                    "path": match.group(1),
                    "status": state["status"],
                }
            )
    return sorted(false_claims, key=lambda claim: claim["claim_id"])


def _check_stored_false_beliefs(
    run: dict[str, Any], recomputed: list[dict[str, Any]]
) -> None:
    stored = run["false_belief_persistence"]
    if stored["claim_count"] != len(recomputed):
        raise ValueError(
            f"Run {run['run_id']} false-belief claim count does not match events"
        )
    if not math.isclose(
        float(stored["confidence_mass"]),
        sum(claim["confidence"] for claim in recomputed),
        rel_tol=0,
        abs_tol=1e-12,
    ):
        raise ValueError(f"Run {run['run_id']} false-belief mass does not match events")
    stored_claims = sorted(stored["claims"], key=lambda claim: claim["claim_id"])
    for event_claim, stored_claim in zip(recomputed, stored_claims, strict=True):
        if (
            event_claim.keys() != stored_claim.keys()
            or any(
                event_claim[key] != stored_claim[key]
                for key in ("claim_id", "path", "status")
            )
            or not math.isclose(
                event_claim["confidence"],
                float(stored_claim["confidence"]),
                rel_tol=0,
                abs_tol=1e-12,
            )
        ):
            raise ValueError(
                f"Run {run['run_id']} false-belief claim does not match events"
            )


def analyze(path: Path) -> dict[str, Any]:
    metadata, runs, digest, line_count = _read_jsonl(path)
    target_path = metadata["decisive_evidence_path"]
    arms = metadata["arms"]
    seeds = metadata["seeds"]
    budget_specs = {budget["id"]: budget for budget in metadata["budgets"]}
    selector_arms = [arm for arm in arms if arm != "full-context"]

    expected_keys = {("full-context", "unbounded", seed) for seed in seeds} | {
        (arm, budget_id, seed)
        for arm in selector_arms
        for budget_id in budget_specs
        for seed in seeds
    }
    keys = [(run["arm"], run["budget_id"], run["seed"]) for run in runs]
    duplicate_keys = [key for key, count in Counter(keys).items() if count > 1]
    missing_keys = sorted(expected_keys - set(keys))
    unexpected_keys = sorted(set(keys) - expected_keys)
    if duplicate_keys or missing_keys or unexpected_keys:
        raise ValueError(
            f"Unexpected run structure: duplicates={duplicate_keys}, "
            f"missing={missing_keys}, unexpected={unexpected_keys}"
        )
    if len({run["run_id"] for run in runs}) != len(runs):
        raise ValueError("Run IDs are not unique")

    per_run = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    consistency = Counter()
    for run in runs:
        recall = _recompute_recall(run)
        success = _recompute_success(run, target_path)
        false_claims = _recompute_false_beliefs(run, target_path)
        _check_stored_false_beliefs(run, false_claims)
        if not math.isclose(
            recall, float(run["decisive_evidence_recall"]), rel_tol=0, abs_tol=1e-12
        ):
            raise ValueError(f"Run {run['run_id']} recall does not match selected IDs")
        if success != bool(run["debugging_success"]):
            raise ValueError(
                f"Run {run['run_id']} debugging_success does not match raw outcome fields"
            )
        if run.get("changed_file") not in {None, target_path}:
            raise ValueError(
                f"Run {run['run_id']} has a changed_file outside the declared target"
            )

        if run["arm"] == "full-context":
            if run["budget_id"] != "unbounded":
                raise ValueError(
                    f"Full-context run {run['run_id']} is not marked unbounded"
                )
        else:
            spec = budget_specs[run["budget_id"]]
            if run["selected_bytes"] > spec["max_cost"]:
                raise ValueError(
                    f"Run {run['run_id']} exceeds its declared byte budget"
                )
            if len(run["selected_evidence_ids"]) > spec["max_items"]:
                raise ValueError(
                    f"Run {run['run_id']} exceeds its declared item budget"
                )

        row = {
            "source_line": run["_line_number"],
            "run_id": run["run_id"],
            "arm": run["arm"],
            "budget_id": run["budget_id"],
            "seed": run["seed"],
            "seed_scope": metadata["seed_scope"],
            "selected_bytes": run["selected_bytes"],
            "selected_evidence_ids": run["selected_evidence_ids"],
            "decisive_evidence_ids": run["decisive_evidence_ids"],
            "recomputed_decisive_evidence_recall": recall,
            "recomputed_debugging_success": success,
            "final_diagnosis": run["final_diagnosis"],
            "final_tests_passed": run["final_tests_passed"],
            "abstained": run["abstained"],
            "recomputed_false_belief_claims": false_claims,
            "recomputed_false_belief_confidence_mass": sum(
                claim["confidence"] for claim in false_claims
            ),
            "costs": run["costs"],
        }
        per_run.append(row)
        grouped[(run["arm"], run["budget_id"])].append(row)
        consistency["recall_recomputed_and_matched"] += 1
        consistency["success_recomputed_and_matched"] += 1
        consistency["run_completed_test_status_matched"] += 1
        consistency["false_belief_recomputed_from_events_and_matched"] += 1

    summaries = []
    for (arm, budget_id), group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda row: row["seed"])
        n = len(ordered)
        recall_count = sum(
            row["recomputed_decisive_evidence_recall"] == 1.0 for row in ordered
        )
        success_count = sum(row["recomputed_debugging_success"] for row in ordered)
        abstention_count = sum(row["abstained"] for row in ordered)
        masses = [row["recomputed_false_belief_confidence_mass"] for row in ordered]
        summaries.append(
            {
                "arm": arm,
                "budget_id": budget_id,
                "trial_count": n,
                "seeds": [row["seed"] for row in ordered],
                "decisive_evidence_recall_1_count": recall_count,
                "decisive_evidence_recall_1_rate": recall_count / n,
                "debugging_success_count": success_count,
                "debugging_success_rate": success_count / n,
                "abstention_count": abstention_count,
                "abstention_rate": abstention_count / n,
                "false_belief_mass_by_seed": [
                    {
                        "seed": row["seed"],
                        "mass": row["recomputed_false_belief_confidence_mass"],
                    }
                    for row in ordered
                ],
                "mean_false_belief_mass_across_order_trials": sum(masses) / n,
                "selected_bytes_by_seed": [
                    {"seed": row["seed"], "bytes": row["selected_bytes"]}
                    for row in ordered
                ],
            }
        )

    all_evidence_matches = []
    for seed in seeds:
        evidence_by_arm = {
            arm: next(
                row["selected_evidence_ids"]
                for row in per_run
                if row["arm"] == arm
                and row["budget_id"] == "all-evidence"
                and row["seed"] == seed
            )
            for arm in selector_arms
        }
        reference_items = set(evidence_by_arm[selector_arms[0]])
        for arm, selected in evidence_by_arm.items():
            same_items = set(selected) == reference_items
            if not same_items:
                raise ValueError(
                    f"Bounded all-evidence selector items differ for {arm}, seed {seed}"
                )
            all_evidence_matches.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "same_items_as_other_bounded_selectors": same_items,
                }
            )

    return {
        "analysis_version": 1,
        "source": {
            "repository": "Bouleusis",
            "path": "docs/experiments/evidence-selection-sweep-2026-10-08.jsonl",
            "sha256": digest,
            "jsonl_record_count_including_metadata": line_count,
            "run_record_count": len(runs),
            "metadata": {
                key: value for key, value in metadata.items() if key != "_line_number"
            },
        },
        "structure": {
            "runs_by_arm_and_budget": [
                {
                    "arm": arm,
                    "budget_id": budget_id,
                    "trial_count": len(group),
                    "seeds": sorted(row["seed"] for row in group),
                }
                for (arm, budget_id), group in sorted(grouped.items())
            ],
            "duplicate_arm_budget_seed_keys": duplicate_keys,
            "missing_expected_keys": missing_keys,
            "unexpected_keys": unexpected_keys,
            "unique_run_ids": len({run["run_id"] for run in runs}),
            "expected_run_count": len(expected_keys),
        },
        "validation": {
            "all_checks_passed": True,
            "check_counts": dict(consistency),
            "seed_variants_are_within_one_injected_fault": metadata["seed_scope"],
            "bounded_all_evidence_item_sets_match_by_seed": all_evidence_matches,
        },
        "recomputed_condition_summaries": summaries,
        "per_run_outcomes": per_run,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, type=Path, help="Bouleusis experiment JSONL"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = analyze(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {len(result['per_run_outcomes'])} per-run outcomes; "
        f"source sha256 {result['source']['sha256']}"
    )


if __name__ == "__main__":
    main()
