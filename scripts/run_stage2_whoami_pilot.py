"""Reduce the recorded real whoami Docker pilot through the Stage 2 gate."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from isoprax.commensurability import OutcomeDefinition
from isoprax.identity import bytes_hash, content_hash
from isoprax.replay_capture import (
    DeploymentEvidence,
    ObservationArtifactEvidence,
    ObservationEvidence,
    ReplayCaptureRecord,
    ReplayLaneDefinition,
)
from isoprax.replay_selection import evaluate_predeclaration_provenance
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


def _predeclaration_hash(predecl: dict[str, object]) -> str:
    payload = {key: value for key, value in predecl.items() if key != "artifact_hash"}
    return content_hash(payload)


def _git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _predeclaration_introducing_commit() -> str:
    relative_path = PREDECLARATION_PATH.relative_to(ROOT)
    commits = _git_output(
        "log", "--diff-filter=A", "--format=%H", "--", str(relative_path)
    ).splitlines()
    if not commits:
        raise ValueError("predeclaration introducing commit is unavailable")
    return commits[0]


def _validate_predeclaration(predecl: dict[str, object], corpus_data_commit: str):
    recorded_hash = str(predecl.get("artifact_hash", "")).strip()
    if not recorded_hash:
        raise ValueError("predeclaration artifact_hash is required")
    actual_hash = _predeclaration_hash(predecl)
    if actual_hash != recorded_hash:
        raise ValueError("predeclaration artifact hash mismatch")
    declared_commit = str(predecl.get("predeclaration_commit", "")).strip()
    introducing_commit = _predeclaration_introducing_commit()
    if declared_commit != introducing_commit:
        raise ValueError("predeclaration_commit does not match the introducing commit")
    return evaluate_predeclaration_provenance(
        predecl,
        artifact_hash=recorded_hash,
        observed_hash=actual_hash,
        predeclaration_commit=declared_commit,
        corpus_data_commits=(corpus_data_commit,),
        external_anchor={
            "anchor_type": "public_commit",
            "anchor_reference": str(predecl["external_anchor_reference"]),
            "independent_of_repository_and_clock": False,
        },
        require_external_anchor=False,
        repository_path=ROOT,
    )


def _inconclusive_report(
    predecl: dict[str, object], provenance, corpus_data_commit: str
) -> dict[str, object]:
    return {
        "schema": "isoprax.stage2.whoami-pilot-report.v1",
        "status": "inconclusive",
        "reason": (
            "external anchor is recorded but not independently verified; "
            "no feasibility report is emitted"
        ),
        "candidate": predecl["candidate"]["repository"],
        "predeclaration_commit": provenance.predeclaration_commit,
        "corpus_data_commit": corpus_data_commit,
        "predeclaration_is_ancestor": provenance.ancestry_ok,
        "external_anchor_reference": predecl["external_anchor_reference"],
        "external_anchor_status": "unverified",
        "predeclaration_artifact_hash": provenance.artifact_hash,
        "claim_boundary": (
            "Stage 2 replay feasibility evidence only; no feasibility, Semantic, "
            "or Full Conformance claim is emitted without an independent anchor."
        ),
    }


def _definition(
    identifier: str, data: dict[str, object], family_field: str
) -> OutcomeDefinition:
    return OutcomeDefinition(
        identifier,
        str(data["event"]),
        data["observation_process"],
        data["window"],
        tuple(data["thresholds"]),
        description=str(data[family_field]),
    )


def _profile(
    predecl: dict[str, object], provenance, corpus_data_commit: str
) -> ReplayPilotProfile:
    lane = predecl["lane"]
    definitions = predecl["outcome_definitions"]
    selected = tuple(str(commit) for commit in predecl["selected_commits"])
    change = _definition("whoami.change.v1", definitions, "change_family")
    operational = _definition(
        "whoami.operational.v1", definitions, "operational_family"
    )
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
        provenance.artifact_hash,
        str(predecl["external_anchor_reference"]),
        provenance.predeclaration_commit,
        (corpus_data_commit,),
        provenance.ancestry_ok,
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
        "metrics.json", "collected", bytes_hash(payload), len(payload)
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
    data_commit = _git_output("rev-parse", "HEAD")
    provenance = _validate_predeclaration(predecl, data_commit)
    if not provenance.anchored:
        output = _inconclusive_report(predecl, provenance, data_commit)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
        print(
            json.dumps(
                {"status": output["status"], "report": str(args.output)},
                sort_keys=True,
            )
        )
        return
    profile = _profile(predecl, provenance, data_commit)
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
        "predeclaration_commit": provenance.predeclaration_commit,
        "corpus_data_commit": data_commit,
        "predeclaration_is_ancestor": provenance.ancestry_ok,
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
