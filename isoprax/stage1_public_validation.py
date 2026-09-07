"""Offline adapters for the bounded Stage 1 public-data validation run."""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .admission import (
    AdmissionProfile,
    CalibrationEvidence,
    CorpusProvenance,
    CorpusRow,
    PredeclarationEvidence,
    SplitDefinition,
    evaluate_admission,
)
from .commensurability import ObservationProcess, OutcomeDefinition, Threshold, Window
from .per_family_evaluation import (
    PerFamilyEvaluationProfile,
    evaluate_per_family,
)
from .strategies import Calibrator

_UTC = dt.timezone.utc
_CLAIM_BOUNDARY = (
    "Stage 1 public-data structural validation evidence only; separate family "
    "results, no cross-family pooling, no Semantic or Full Conformance claim"
)
_APACHE_SOURCE = {
    "source_id": "apachejit-zenodo-5907002",
    "source_reference": "https://doi.org/10.5281/zenodo.5907002",
    "license": "CC-BY-4.0",
    "published_checksum": "md5:98e102741020b3b13798d1e10a350689",
    "published_algorithm": "md5",
    "filename": "apachejit_total.csv",
}
_GOOGLE_SOURCE = {
    "source_id": "google-cluster-trace-v1",
    "source_reference": "https://github.com/google/cluster-data/blob/master/TraceVersion1.md",
    "license": "CC-BY-4.0",
    "published_checksum": "sha1:98c87f059aa1cc37f1e9523ac691ee0fd5629188",
    "published_algorithm": "sha1",
    "filename": "google-cluster-data-1.csv.gz",
}


@dataclass(frozen=True)
class SourceArtifact:
    source_id: str
    source_reference: str
    license: str
    published_checksum: str
    sha256: str
    byte_count: int
    local_filename: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_artifact(path: Path, expected: dict[str, str]) -> SourceArtifact:
    if not path.is_file():
        raise FileNotFoundError(f"public source file is missing: {path}")
    algorithm, expected_digest = expected["published_checksum"].split(":", 1)
    actual_published = _hash_file(path, algorithm)
    if actual_published != expected_digest:
        raise ValueError(
            f"{expected['source_id']} {algorithm} checksum mismatch: "
            f"expected {expected_digest}, got {actual_published}"
        )
    return SourceArtifact(
        expected["source_id"],
        expected["source_reference"],
        expected["license"],
        expected["published_checksum"],
        _hash_file(path, "sha256"),
        path.stat().st_size,
        expected["filename"],
    )


def _split_for_timestamp(timestamp: dt.datetime) -> str:
    if (
        dt.datetime(2014, 1, 1, tzinfo=_UTC)
        <= timestamp
        < dt.datetime(2015, 1, 1, tzinfo=_UTC)
    ):
        return "train"
    if (
        dt.datetime(2015, 1, 1, tzinfo=_UTC)
        <= timestamp
        < dt.datetime(2016, 1, 1, tzinfo=_UTC)
    ):
        return "calibration_fit"
    if (
        dt.datetime(2016, 1, 1, tzinfo=_UTC)
        <= timestamp
        < dt.datetime(2017, 1, 1, tzinfo=_UTC)
    ):
        return "calibration_gate"
    if (
        dt.datetime(2017, 1, 1, tzinfo=_UTC)
        <= timestamp
        < dt.datetime(2020, 1, 1, tzinfo=_UTC)
    ):
        return "test"
    return "outside"


def _apache_split_definitions() -> tuple[SplitDefinition, ...]:
    return (
        SplitDefinition(
            "train", "2014-01-01T00:00:00+00:00", "2015-01-01T00:00:00+00:00"
        ),
        SplitDefinition(
            "calibration_fit", "2015-01-01T00:00:00+00:00", "2016-01-01T00:00:00+00:00"
        ),
        SplitDefinition(
            "calibration_gate", "2016-01-01T00:00:00+00:00", "2017-01-01T00:00:00+00:00"
        ),
        SplitDefinition(
            "test", "2017-01-01T00:00:00+00:00", "2020-01-01T00:00:00+00:00"
        ),
    )


def _google_split_definitions() -> tuple[SplitDefinition, ...]:
    base = dt.datetime(2011, 5, 1, tzinfo=_UTC)
    boundaries = (90000, 96000, 102000, 108000, 114000)
    values = tuple(
        (base + dt.timedelta(seconds=value)).isoformat() for value in boundaries
    )
    return tuple(
        SplitDefinition(name, values[index], values[index + 1])
        for index, name in enumerate(
            ("train", "calibration_fit", "calibration_gate", "test")
        )
    )


def _apache_raw_score(row: dict[str, str]) -> float:
    churn = int(row["la"]) + int(row["ld"])
    return 1.0 - math.exp(-0.002 * churn)


def _profile(
    *,
    system_id: str,
    splits: tuple[SplitDefinition, ...],
    fit_ids: tuple[str, ...],
    gate_ids: tuple[str, ...],
    threshold_version: str,
    source_reference: str,
    predeclaration_hash: str,
    published_artifact: str,
    horizon_rule: str,
) -> AdmissionProfile:
    return AdmissionProfile(
        allowed_prediction_fields=frozenset({"raw_feature", "score"}),
        forbidden_prediction_fields=frozenset(),
        horizon_rule=horizon_rule,
        horizon_frozen=True,
        adequacy_min_positives=1,
        adequacy_min_negatives=1,
        split_definitions=splits,
        release_scope="public-dataset-stage1-aggregate-evidence",
        thresholds_frozen=True,
        expected_system_id=system_id,
        calibration_evidence=CalibrationEvidence(fit_ids, gate_ids),
        predeclaration_evidence=PredeclarationEvidence(
            artifact_hash=f"sha256:{predeclaration_hash}",
            external_anchor_reference=source_reference,
            predeclared_at="2026-01-01T00:00:00+00:00",
            corpus_collection_started_at="2026-01-02T00:00:00+00:00",
        ),
        corpus_provenance=CorpusProvenance(system_id, False, False),
        published_artifacts=(published_artifact,),
    )


def _row_summary(report: Any) -> dict[str, Any]:
    return {
        "evaluation_identity": report.evaluation_identity,
        "status": report.status,
        "family": report.family,
        "outcome_definition_id": report.outcome_definition_id,
        "declarable_class": report.declarable_class,
        "metrics": dict(report.metrics),
        "calibration": dict(report.calibration),
        "counts": dict(report.counts),
        "uncertainty": dict(report.uncertainty),
        "unavailable_evidence": [asdict(item) for item in report.unavailable_evidence],
        "claim_scope": report.claim_scope,
    }


def _admission_summary(report: Any) -> dict[str, Any]:
    return {
        "admissible": report.admissible,
        "counts_by_split": report.counts_by_split,
        "gates": [
            {"gate_id": gate.gate_id, "passed": gate.passed, "message": gate.message}
            for gate in report.gate_results
        ],
        "declarable_class": report.declarable_class,
    }


def _build_apache_rows(path: Path) -> tuple[list[CorpusRow], SourceArtifact]:
    artifact = _source_artifact(path, _APACHE_SOURCE)
    values: list[tuple[dt.datetime, dict[str, str], int, float, str]] = []
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        required = {"commit_id", "project", "buggy", "year", "la", "ld"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError("ApacheJIT schema is missing required columns")
        for row in reader:
            if row["project"] != "apache/ignite":
                continue
            timestamp = dt.datetime.fromtimestamp(int(row["author_date"]), _UTC)
            split = _split_for_timestamp(timestamp)
            if split == "outside":
                continue
            values.append(
                (
                    timestamp,
                    row,
                    int(row["buggy"].lower() == "true"),
                    _apache_raw_score(row),
                    split,
                )
            )
    values.sort(key=lambda item: (item[0], item[1]["commit_id"]))
    fit = [item for item in values if item[4] == "calibration_fit"]
    calibrator = Calibrator().fit([item[3] for item in fit], [item[2] for item in fit])
    rows: list[CorpusRow] = []
    for index, (timestamp, source_row, outcome, raw, split) in enumerate(values):
        score_time = timestamp.isoformat()
        rows.append(
            CorpusRow(
                row_id=f"apache-{index}",
                system_id="apache/ignite",
                change_id=source_row["commit_id"],
                deployment_id=f"apache-deployment-{index}",
                observation_id=f"apache-observation-{index}",
                split=split,
                score_time=score_time,
                outcome_class="observed_positive" if outcome else "observed_negative",
                prediction_fields={
                    "raw_feature": raw,
                    "score": calibrator.transform(raw),
                },
                linkage_bases=("public-commit-id",),
                outcome_window_complete=True,
                horizon_rule_used="fixed-14d-published-label",
                threshold_version="apachejit-v1",
                change_group_id=source_row["commit_id"],
                prediction_field_observed_at={
                    "raw_feature": score_time,
                    "score": score_time,
                },
            )
        )
    return rows, artifact


def _google_jobs(
    path: Path,
) -> tuple[dict[str, list[tuple[int, float, float]]], SourceArtifact]:
    artifact = _source_artifact(path, _GOOGLE_SOURCE)
    jobs: dict[str, list[tuple[int, float, float]]] = {}
    with gzip.open(path, "rt", newline="") as source:
        header = next(source, "").split()
        required = [
            "Time",
            "ParentID",
            "TaskID",
            "JobType",
            "NrmlTaskCores",
            "NrmlTaskMem",
        ]
        if header[: len(required)] != required:
            raise ValueError("Google Trace v1 schema is missing required columns")
        for line in source:
            fields = line.split()
            if len(fields) < len(required):
                continue
            jobs.setdefault(fields[1], []).append(
                (
                    int(fields[0]),
                    float(fields[4]),
                    float(fields[5]),
                )
            )
    return jobs, artifact


def _build_google_rows(path: Path) -> tuple[list[CorpusRow], SourceArtifact]:
    jobs, artifact = _google_jobs(path)
    base = dt.datetime(2011, 5, 1, tzinfo=_UTC)
    cuts = (90000, 96000, 102000, 108000, 114000)
    values: list[tuple[int, str, int, float, str]] = []
    for job_id, observations in jobs.items():
        observations.sort()
        if len(observations) < 2:
            continue
        first_time, first_cores, first_memory = observations[0]
        if not cuts[0] <= first_time < cuts[-1]:
            continue
        outcome = int(
            any(
                cores >= 0.005 or memory >= 0.005
                for _, cores, memory in observations[1:]
            )
        )
        raw = min(
            1.0,
            0.5 * min(first_cores / 0.02, 1.0) + 0.5 * min(first_memory / 0.01, 1.0),
        )
        split = (
            "train"
            if first_time < cuts[1]
            else "calibration_fit"
            if first_time < cuts[2]
            else "calibration_gate"
            if first_time < cuts[3]
            else "test"
        )
        values.append((first_time, job_id, outcome, raw, split))
    values.sort(key=lambda item: (item[0], item[1]))
    fit = [item for item in values if item[4] == "calibration_fit"]
    calibrator = Calibrator().fit([item[3] for item in fit], [item[2] for item in fit])
    rows: list[CorpusRow] = []
    for index, (first_time, job_id, outcome, raw, split) in enumerate(values):
        score_time = (base + dt.timedelta(seconds=first_time)).isoformat()
        rows.append(
            CorpusRow(
                row_id=f"google-{index}",
                system_id="google-cluster-v1",
                change_id=f"job-{job_id}",
                deployment_id=f"google-job-{job_id}",
                observation_id=f"google-observation-{job_id}",
                split=split,
                score_time=score_time,
                outcome_class="observed_positive" if outcome else "observed_negative",
                prediction_fields={
                    "raw_feature": raw,
                    "score": calibrator.transform(raw),
                },
                linkage_bases=("public-job-id",),
                outcome_window_complete=True,
                horizon_rule_used="fixed-5m-followup",
                threshold_version="google-v1",
                change_group_id=f"job-{job_id}",
                prediction_field_observed_at={
                    "raw_feature": score_time,
                    "score": score_time,
                },
            )
        )
    return rows, artifact


def _family_evidence(
    *,
    rows: list[CorpusRow],
    source: SourceArtifact,
    family: str,
    outcome_definition: OutcomeDefinition,
    threshold_version: str,
    splits: tuple[SplitDefinition, ...],
    source_reference: str,
    predeclaration_hash: str,
    published_artifact: str,
    horizon_rule: str,
) -> dict[str, Any]:
    fit_ids = tuple(row.row_id for row in rows if row.split == "calibration_fit")
    gate_ids = tuple(row.row_id for row in rows if row.split == "calibration_gate")
    profile = _profile(
        system_id=rows[0].system_id,
        splits=splits,
        fit_ids=fit_ids,
        gate_ids=gate_ids,
        threshold_version=threshold_version,
        source_reference=source_reference,
        predeclaration_hash=predeclaration_hash,
        published_artifact=published_artifact,
        horizon_rule=horizon_rule,
    )
    admission = evaluate_admission(rows, profile)
    evaluation = evaluate_per_family(
        rows,
        profile,
        admission,
        PerFamilyEvaluationProfile(
            family, outcome_definition, "score", threshold_version
        ),
    )
    return {
        "source_id": source.source_id,
        "adapter_version": "stage1-public-validation-v1",
        "outcome_definition": outcome_definition.to_dict(),
        "split_definitions": [asdict(item) for item in splits],
        "admission": _admission_summary(admission),
        "evaluation": _row_summary(evaluation),
    }


def build_stage1_public_validation_report(
    apachejit_path: str | Path,
    google_trace_path: str | Path,
    *,
    predeclaration_path: str | Path,
) -> dict[str, Any]:
    """Build the aggregate Stage 1 report from caller-supplied source files."""

    predeclaration = Path(predeclaration_path)
    if not predeclaration.is_file():
        raise FileNotFoundError(f"predeclaration is missing: {predeclaration}")
    predeclaration_hash = _hash_file(predeclaration, "sha256")
    apache_rows, apache_source = _build_apache_rows(Path(apachejit_path))
    google_rows, google_source = _build_google_rows(Path(google_trace_path))
    families = [
        _family_evidence(
            rows=apache_rows,
            source=apache_source,
            family="change",
            outcome_definition=OutcomeDefinition(
                "defect.fix_linkage.v1",
                "commit later linked to a defect fix",
                ObservationProcess("szz-style-repository-linkage"),
                Window(None, "dataset", "published-bug-label"),
            ),
            threshold_version="apachejit-v1",
            splits=_apache_split_definitions(),
            source_reference=apache_source.source_reference,
            predeclaration_hash=predeclaration_hash,
            published_artifact="apachejit-aggregate.json",
            horizon_rule="fixed-14d-published-label",
        ),
        _family_evidence(
            rows=google_rows,
            source=google_source,
            family="operational",
            outcome_definition=OutcomeDefinition(
                "resource.threshold.v1",
                "later task resource threshold crossed",
                ObservationProcess("cluster-task-observation"),
                Window(5, "minute", "first-task-observation"),
                (Threshold("normalized resource", ">=", 0.005),),
            ),
            threshold_version="google-v1",
            splits=_google_split_definitions(),
            source_reference=google_source.source_reference,
            predeclaration_hash=predeclaration_hash,
            published_artifact="google-trace-aggregate.json",
            horizon_rule="fixed-5m-followup",
        ),
    ]
    payload: dict[str, Any] = {
        "predeclaration": {
            "local_filename": predeclaration.name,
            "sha256": predeclaration_hash,
        },
        "sources": [apache_source.to_dict(), google_source.to_dict()],
        "families": families,
        "cross_family_pooling": "withheld: Outcome Definitions use different observation processes",
        "claim_boundary": _CLAIM_BOUNDARY,
    }
    identity = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {"report_identity": f"sha256:{identity}", **payload}


__all__ = ["build_stage1_public_validation_report"]
