"""Reduce the recorded real whoami Docker pilot through the Stage 2 gate."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Mapping

from isoprax.commensurability import OutcomeDefinition
from isoprax.external_anchor import (
    DEFAULT_SUBJECT_NAME,
    ExternalAnchorVerification,
    verify_sigstore_attestation,
)
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
    estimate_stage2_yield,
    normalize_replay_records,
    validate_stage2_feasibility_report,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "docs/stage2/whoami-pilot-data-v2.json"
PREDECLARATION_PATH = ROOT / "docs/stage2/whoami-pilot-predeclaration-v2.json"
SCORE_TIME = "2026-09-08T00:00:00Z"
WINDOW_END = "2026-09-08T00:10:00Z"
YIELD_TARGET_POSITIVE = 5
YIELD_TARGET_NEGATIVE = 5


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


def _predeclaration_introducing_commit(
    predeclaration_path: Path = PREDECLARATION_PATH,
) -> str:
    relative_path = predeclaration_path.relative_to(ROOT)
    commits = _git_output(
        "log", "--diff-filter=A", "--format=%H", "--", str(relative_path)
    ).splitlines()
    if not commits:
        raise ValueError("predeclaration introducing commit is unavailable")
    return commits[0]


def _configured_attestation(
    predecl: Mapping[str, object],
    *,
    bundle_path: Path | None,
    signer_identity: str | None,
    issuer: str | None,
    subject_name: str | None,
) -> tuple[Path | None, str | None, str | None, str]:
    configured = predecl.get("sigstore_attestation", {})
    if not isinstance(configured, Mapping):
        raise ValueError("sigstore_attestation must be an object")
    configured_bundle = configured.get("bundle_path")
    resolved_bundle = bundle_path or (
        None if not configured_bundle else Path(str(configured_bundle))
    )
    if resolved_bundle is not None and not resolved_bundle.is_absolute():
        resolved_bundle = ROOT / resolved_bundle
    return (
        resolved_bundle,
        signer_identity or _optional_text(configured.get("signer_identity")),
        issuer or _optional_text(configured.get("issuer")),
        subject_name
        or _optional_text(configured.get("subject_name"))
        or DEFAULT_SUBJECT_NAME,
    )


def _optional_text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _yield_estimate(data: Mapping[str, object]) -> dict[str, object]:
    records = data.get("records")
    if not isinstance(records, list):
        raise ValueError("pilot records are required for yield estimation")
    return estimate_stage2_yield(
        (str(row["outcome_class"]) for row in records),
        target_positive=YIELD_TARGET_POSITIVE,
        target_negative=YIELD_TARGET_NEGATIVE,
    ).to_dict()


def _validate_predeclaration(
    predecl: dict[str, object],
    corpus_data_commit: str,
    *,
    predeclaration_path: Path = PREDECLARATION_PATH,
    attestation_bundle: Path | None = None,
    signer_identity: str | None = None,
    signer_issuer: str | None = None,
    attestation_subject: str | None = None,
):
    recorded_hash = str(predecl.get("artifact_hash", "")).strip()
    if not recorded_hash:
        raise ValueError("predeclaration artifact_hash is required")
    actual_hash = _predeclaration_hash(predecl)
    if actual_hash != recorded_hash:
        raise ValueError("predeclaration artifact hash mismatch")
    declared_commit = str(predecl.get("predeclaration_commit", "")).strip()
    introducing_commit = _predeclaration_introducing_commit(predeclaration_path)
    if declared_commit != introducing_commit:
        raise ValueError("predeclaration_commit does not match the introducing commit")
    (
        bundle_path,
        configured_identity,
        configured_issuer,
        subject_name,
    ) = _configured_attestation(
        predecl,
        bundle_path=attestation_bundle,
        signer_identity=signer_identity,
        issuer=signer_issuer,
        subject_name=attestation_subject,
    )
    verification = verify_sigstore_attestation(
        bundle_path,
        artifact_hash=recorded_hash,
        predeclaration_commit=declared_commit,
        signer_identity=configured_identity,
        issuer=configured_issuer,
        subject_name=subject_name,
    )
    provenance = evaluate_predeclaration_provenance(
        predecl,
        artifact_hash=recorded_hash,
        observed_hash=actual_hash,
        predeclaration_commit=declared_commit,
        corpus_data_commits=(corpus_data_commit,),
        external_anchor={
            "anchor_type": (
                verification.anchor_type if verification.verified else "public_commit"
            ),
            "anchor_reference": (
                verification.anchor_reference
                if verification.verified
                else str(predecl["external_anchor_reference"])
            ),
            "independent_of_repository_and_clock": verification.verified,
        },
        require_external_anchor=verification.verified,
        repository_path=ROOT,
    )
    return replace(
        provenance,
        records={
            **provenance.records,
            "external_anchor_verification": verification.to_dict(),
        },
    )


def _inconclusive_report(
    predecl: dict[str, object],
    provenance,
    corpus_data_commit: str,
    verification: ExternalAnchorVerification | None = None,
    yield_estimate: Mapping[str, object] | None = None,
) -> dict[str, object]:
    verification_data = (
        verification.to_dict()
        if verification is not None
        else provenance.records.get("external_anchor_verification", {})
    )
    reason = (
        verification.reason
        if verification is not None
        else str(
            verification_data.get(
                "reason",
                "Sigstore attestation bundle is not configured",
            )
        )
    )
    report = {
        "schema": "isoprax.stage2.whoami-pilot-report.v1",
        "status": "inconclusive",
        "reason": f"{reason}; no feasibility report is emitted",
        "candidate": predecl["candidate"]["repository"],
        "predeclaration_commit": provenance.predeclaration_commit,
        "corpus_data_commit": corpus_data_commit,
        "predeclaration_is_ancestor": provenance.ancestry_ok,
        "external_anchor_reference": (
            provenance.external_anchor_reference or predecl["external_anchor_reference"]
        ),
        "external_anchor_status": "unverified",
        "external_anchor_verification": verification_data,
        "predeclaration_artifact_hash": provenance.artifact_hash,
        "claim_boundary": (
            "Stage 2 replay feasibility evidence only; no feasibility, Semantic, "
            "or Full Conformance claim is emitted without an independent anchor."
        ),
    }
    if yield_estimate is not None:
        report["yield_estimate"] = dict(yield_estimate)
    return report


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
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--predeclaration", type=Path, default=PREDECLARATION_PATH)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/stage2/whoami-pilot-report.json"
    )
    parser.add_argument("--attestation-bundle", type=Path)
    parser.add_argument("--attestation-identity")
    parser.add_argument("--attestation-issuer")
    parser.add_argument("--attestation-subject")
    args = parser.parse_args()
    data_path = args.data if args.data.is_absolute() else ROOT / args.data
    predeclaration_path = (
        args.predeclaration
        if args.predeclaration.is_absolute()
        else ROOT / args.predeclaration
    )
    data = json.loads(data_path.read_text(encoding="utf-8"))
    predecl = json.loads(predeclaration_path.read_text(encoding="utf-8"))
    yield_estimate = _yield_estimate(data)
    data_commit = _git_output("rev-parse", "HEAD")
    provenance = _validate_predeclaration(
        predecl,
        data_commit,
        predeclaration_path=predeclaration_path,
        attestation_bundle=args.attestation_bundle,
        signer_identity=args.attestation_identity,
        signer_issuer=args.attestation_issuer,
        attestation_subject=args.attestation_subject,
    )
    if not provenance.anchored:
        output = _inconclusive_report(
            predecl, provenance, data_commit, yield_estimate=yield_estimate
        )
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
        "yield_estimate": yield_estimate,
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
