"""Reduce the recorded real whoami Docker pilot through the Stage 2 gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from isoprax.commensurability import OutcomeDefinition
from isoprax.replay_capture import (
    DeploymentEvidence,
    ObservationArtifactEvidence,
    ObservationEvidence,
    ReplayCaptureRecord,
    ReplayLaneDefinition,
)
from isoprax.stage2_feasibility import (
    ReplayPilotProfile,
    build_stage2_feasibility_report,
    normalize_replay_records,
    validate_stage2_feasibility_report,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "docs/stage2/whoami-pilot-data-v2.json"
PREDECLARATION_PATH = ROOT / "docs/stage2/whoami-pilot-predeclaration-v2.json"
SCORE_TIME = "2026-09-08T00:00:00Z"
WINDOW_END = "2026-09-08T00:10:00Z"
PREDECLARATION_COMMIT = "2d146a2f7affd3747662db0c00e8a00c1d4c3259"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _definition(identifier: str, data: dict[str, object]) -> OutcomeDefinition:
    return OutcomeDefinition(
        identifier,
        str(data["event"]),
        {"kind": "shared_http_latency", "parameters": {"endpoint": "/bench"}},
        {"duration": 10, "unit": "minute", "anchor": "score_time"},
        (
            {
                "metric": "p99_latency_seconds",
                "operator": ">",
                "value": 0.5,
                "sustain": 60,
                "sustain_unit": "second",
            },
        ),
    )


def _profile(predecl: dict[str, object]) -> ReplayPilotProfile:
    lane = predecl["lane"]
    definitions = predecl["outcome_definitions"]
    selected = tuple(str(commit) for commit in predecl["selected_commits"])
    change = _definition("whoami.change.v1", definitions)
    operational = _definition("whoami.operational.v1", definitions)
    gates = predecl["feasibility_gates"]
    boundary = predecl["prediction_boundary"]
    return ReplayPilotProfile(
        "traefik-whoami",
        str(lane["system_id"]),
        str(lane["service_id"]),
        selected,
        str(lane["workload_reference"]),
        change,
        operational,
        str(lane["horizon_rule"]),
        str(lane["threshold_version"]),
        str(lane["capture_schema_version"]),
        str(lane["allowed_evidence_scope"]),
        ("whoami-pilot-data.json", "whoami-pilot-report.json"),
        str(predecl["artifact_hash"]),
        str(predecl["external_anchor_reference"]),
        str(predecl["predeclaration_commit"]),
        (str(predecl["corpus_data_commit"]),),
        bool(predecl["predeclaration_is_ancestor"]),
        frozenset(str(value) for value in boundary["allowed_fields"]),
        frozenset(str(value) for value in boundary["forbidden_fields"]),
        int(gates["min_complete_records"]),
        bool(gates["require_positive_and_negative"]),
        float(gates["min_observation_rate"]),
        False,
    )


def _capture(
    row: dict[str, object], profile: ReplayPilotProfile
) -> ReplayCaptureRecord:
    commit = str(row["commit"])
    lane = ReplayLaneDefinition(
        profile.system_id,
        profile.service_id,
        commit,
        profile.workload_reference,
        profile.horizon_rule,
        profile.threshold_version,
        profile.capture_schema_version,
        profile.allowed_evidence_scope,
        SCORE_TIME,
        SCORE_TIME,
        WINDOW_END,
    )
    payload = json.dumps(
        {
            "commit": commit,
            "requests": row["requests"],
            "p99_seconds": row["p99_seconds"],
            "min_seconds": row["min_seconds"],
            "max_seconds": row["max_seconds"],
            "threshold_met": row["outcome_class"] == "observed_positive",
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    artifact = ObservationArtifactEvidence(
        "metrics.json", "collected", _sha256(payload), len(payload)
    )
    observation = ObservationEvidence(
        SCORE_TIME,
        SCORE_TIME,
        WINDOW_END,
        True,
        True,
        True,
        str(row["outcome_class"]) == "observed_positive",
        False,
        False,
        profile.allowed_evidence_scope,
        ("metrics.json",),
        {"metrics.json": payload},
        "captured by Docker HTTP workload",
    )
    deployment = DeploymentEvidence(
        f"docker:{commit[:12]}",
        commit,
        "succeeded",
        SCORE_TIME,
        SCORE_TIME,
        f"docker://{commit}",
    )
    return ReplayCaptureRecord(
        f"whoami:{commit}",
        lane,
        str(row["build_log_sha256"]),
        str(row["image_id"]),
        deployment,
        observation,
        (artifact,),
        str(row["outcome_class"]),
        row["censor_reason"],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/stage2/whoami-pilot-report.json"
    )
    args = parser.parse_args()
    data = json.loads(DATA_PATH.read_text())
    predecl = json.loads(PREDECLARATION_PATH.read_text())
    data_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    # The JSON artifact is immutable after its introducing commit.  Keep the
    # actual commit binding in the generated report rather than rewriting the
    # predeclaration with a self-referential hash.
    predecl["predeclaration_commit"] = PREDECLARATION_COMMIT
    predecl["corpus_data_commit"] = data_commit
    predecl["predeclaration_is_ancestor"] = (
        subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                str(predecl["predeclaration_commit"]),
                data_commit,
            ],
            cwd=ROOT,
        ).returncode
        == 0
    )
    profile = _profile(predecl)
    captures = tuple(_capture(row, profile) for row in data["records"])
    records = normalize_replay_records(
        profile,
        captures,
        run_identity="whoami-docker-pilot-2026-09-08",
        prediction_fields={
            str(row["commit"]): {
                "commit_metadata_before_score_time": "2026-09-07T23:59:00Z"
            }
            for row in data["records"]
        },
    )
    build_seconds = [float(row["build_seconds"]) for row in data["records"]]
    report = build_stage2_feasibility_report(
        profile,
        records,
        throughput={
            "build_mean_seconds": sum(build_seconds) / len(build_seconds),
            "build_total_seconds": sum(build_seconds),
            "observation_requests_per_commit": float(
                data["workload"]["requests_per_commit"]
            ),
        },
        temporal_coverage={"collection_date_utc": data["collection_date_utc"]},
        extrapolation={
            "basis": "three real public revisions and one repeated revision",
            "uncertainty": "pilot-only; no full-corpus adequacy claim",
            "full_corpus_estimate_required": True,
        },
    )
    validate_stage2_feasibility_report(report)
    output = {
        "schema": "isoprax.stage2.whoami-pilot-report.v1",
        "candidate": data["candidate_repository"],
        "predeclaration_commit": predecl["predeclaration_commit"],
        "corpus_data_commit": data_commit,
        "predeclaration_is_ancestor": predecl["predeclaration_is_ancestor"],
        "observed_measurements": data,
        "feasibility_report": report.to_dict(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": report.status,
                "report": str(args.output),
                "identity": report.report_identity,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
