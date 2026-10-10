"""Reproduce and verify only the IsoPrax flagship paper evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from isoprax.operation_gate_experiment import run_gate_experiment
from isoprax.research_experiments import run_benchmark_a

ROOT = Path(__file__).resolve().parents[1]
PAPER = Path(
    "docs/research/Calibration Is Not Enough_ Outcome Commensurability as a Precondition for Cross-Family Failure Prediction.md"
)
CLAIMS = Path("docs/research/paper-claims-evidence.json")
RESULTS = Path("docs/research/experimental-results.json")
LOCK = Path("docs/research/paper-flagship-integrity-lock.json")
OUTPUT = Path("docs/research/paper-recomputed-results.json")
TABLES = Path("docs/research/paper-recomputed-tables.md")

LOCKED_FILES = {
    str(PAPER),
    str(CLAIMS),
    "docs/research/README.md",
    "docs/research/flagship-scope-decision-2026-10-10.md",
    "docs/research/flagship-dependency-separation-2026-10-10.md",
    "docs/research/flagship-replication-2026-10-10.md",
    "docs/research/flagship-adversarial-review-2026-10-10.md",
    "docs/research/paper-review-packet-2026-10-10.md",
    "docs/research/literature-citation-audit-2026-10-10.md",
    "docs/research/tev1-output-rights-2026-10-10.md",
    "docs/research/coverage-reconciliation-2026-10-10.md",
    "scripts/flagship_paper_integrity.py",
    "tests/test_flagship_paper_integrity.py",
    "isoprax/research_experiments.py",
    "isoprax/operation_gate_experiment.py",
    "isoprax/commensurability.py",
    "specs/014-normative-commensurability-evidence/spec.md",
    "tests/test_research_experiments.py",
    "pyproject.toml",
    "uv.lock",
}
LOCKED_RESULT_POINTERS = {
    (str(RESULTS), "/benchmark_a"),
    (str(RESULTS), "/gate_comparison/cases"),
    (str(RESULTS), "/gate_comparison/rules"),
}
FORBIDDEN_PATH_MARKERS = (
    "bouleusis",
    "model-role",
    "model_role",
    "model-runtime",
    "retrieval-selection",
    "evidence-acquisition",
    "operation-policy-challenge-v2",
)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _pointer(value: Any, pointer: str) -> Any:
    if not pointer.startswith("/"):
        raise ValueError(f"JSON pointer must start with '/': {pointer}")
    current = value
    for part in pointer[1:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        current = current[int(key)] if isinstance(current, list) else current[key]
    return current


def _verify_lock(root: Path) -> dict[str, Any]:
    lock = _json(root / LOCK)
    files = lock.get("files")
    if not isinstance(files, list):
        raise ValueError("flagship integrity lock has no file hashes")
    file_paths = [entry.get("path") for entry in files]
    if len(file_paths) != len(set(file_paths)) or set(file_paths) != LOCKED_FILES:
        raise ValueError("flagship file lock differs from the reviewed dependency set")
    for entry in files:
        path = entry["path"]
        if any(marker in path.lower() for marker in FORBIDDEN_PATH_MARKERS):
            raise ValueError(f"companion artifact cannot be a flagship input: {path}")
        actual = _sha((root / path).read_bytes())
        if actual != entry.get("sha256"):
            raise ValueError(f"source hash mismatch: {path}")

    sections = lock.get("result_sections")
    actual_pairs = {
        (entry.get("path"), entry.get("pointer")) for entry in sections or []
    }
    if actual_pairs != LOCKED_RESULT_POINTERS or len(sections or []) != len(
        actual_pairs
    ):
        raise ValueError(
            "result lock must pin only the three declared flagship sections"
        )
    source = _json(root / RESULTS)
    checked_sections = []
    for entry in sections:
        path, pointer = entry["path"], entry["pointer"]
        if any(marker in path.lower() for marker in FORBIDDEN_PATH_MARKERS):
            raise ValueError(f"companion artifact cannot be a flagship input: {path}")
        actual = _sha(_canonical(_pointer(source, pointer)))
        if actual != entry.get("sha256"):
            raise ValueError(f"selected result section changed: {pointer}")
        checked_sections.append({"path": path, "pointer": pointer, "sha256": actual})
    return {
        "verified_source_files": len(files),
        "verified_result_sections": checked_sections,
        "full_result_file_hash_is_provenance_only": True,
    }


def _validate_claim_registry(root: Path) -> dict[str, Any]:
    registry = _json(root / CLAIMS)
    claims = registry.get("claims")
    if not isinstance(claims, list) or len(claims) != 36:
        raise ValueError("the full 36-claim registry must be retained")
    ids = [claim.get("id") for claim in claims]
    if len(ids) != len(set(ids)):
        raise ValueError("claim IDs are not unique")
    flagship = [claim for claim in claims if claim.get("scope") == "flagship"]
    companion = [claim for claim in claims if claim.get("scope") == "companion"]
    if len(flagship) != 24 or len(companion) != 12:
        raise ValueError("claim scope must be 24 flagship and 12 companion-only")

    paper = (root / PAPER).read_text(encoding="utf-8")
    known_tags = set(ids)
    tagged = set(re.findall(r"\[\[(C\d+|L\d+)\]\]", paper))
    expected = {claim["id"] for claim in flagship}
    if tagged != expected or tagged - known_tags:
        raise ValueError("manuscript claim tags do not match the 24 flagship claims")
    untagged_numbers = []
    in_references = False
    for line_no, line in enumerate(paper.splitlines(), start=1):
        if line.strip().lower() == "## references":
            in_references = True
        if in_references or not line.strip() or line.lstrip().startswith("#"):
            continue
        claim_text = re.sub(r"\[\[(?:C|L)\d+\]\]", "", line)
        claim_text = re.sub(r"\bRQ\d+\b", "", claim_text, flags=re.IGNORECASE)
        if re.search(r"\d", claim_text) and not re.search(r"\[\[(?:C|L)\d+\]\]", line):
            untagged_numbers.append((line_no, line))
    if untagged_numbers:
        raise ValueError(
            f"numeric manuscript lines lack claim tags: {untagged_numbers}"
        )

    for claim in flagship:
        for artifact in claim.get("artifacts", []):
            path = artifact.get("path")
            if path:
                if any(marker in path.lower() for marker in FORBIDDEN_PATH_MARKERS):
                    raise ValueError(
                        f"flagship claim depends on companion file: {path}"
                    )
                local = root / path
                if not local.is_file():
                    raise ValueError(f"flagship claim artifact missing: {path}")
                expected_hash = artifact.get("sha256")
                if expected_hash and _sha(local.read_bytes()) != expected_hash:
                    raise ValueError(f"claim artifact hash changed: {path}")
                for pointer in artifact.get("json_pointers", []):
                    value = _pointer(_json(local), pointer["pointer"])
                    if _sha(_canonical(value)) != pointer.get("sha256"):
                        raise ValueError(
                            f"claim result section changed: {path}{pointer['pointer']}"
                        )
        protocol = claim.get("protocol", {})
        if protocol.get("path") not in (None, "scripts/flagship_paper_integrity.py"):
            raise ValueError(
                f"flagship claim uses a non-standalone protocol: {claim['id']}"
            )
        if (
            protocol.get("sha256")
            and _sha((root / "scripts/flagship_paper_integrity.py").read_bytes())
            != protocol["sha256"]
        ):
            raise ValueError(f"flagship protocol hash changed: {claim['id']}")

    for claim in companion:
        for artifact in claim.get("artifacts", []):
            if artifact.get("path"):
                raise ValueError(
                    f"companion claim has a local dependency: {claim['id']}"
                )
        if claim.get("protocol", {}).get("path"):
            raise ValueError(
                f"companion claim has a local protocol dependency: {claim['id']}"
            )

    if registry.get("scope_counts") != {"total": 36, "flagship": 24, "companion": 12}:
        raise ValueError("claim registry scope counts are missing or stale")
    return {
        "total_claims": 36,
        "flagship_claims": 24,
        "companion_claims_excluded_from_reproduction": 12,
        "flagship_ids": sorted(expected),
    }


def _gate_case_metrics(gate: dict[str, Any]) -> dict[str, dict[str, int]]:
    cases = gate["cases"]
    rules = sorted(gate["rules"])
    if len(cases) != 23 or gate.get("case_count") != 23:
        raise ValueError("operation-gate challenge must contain the frozen 23 cases")
    invalid = [case for case in cases if not case["expected_permission"]]
    valid = [case for case in cases if case["expected_permission"]]
    result = {}
    for rule in rules:
        result[rule] = {
            "false_permissions": sum(
                bool(case["permissions"][rule]) for case in invalid
            ),
            "invalid_case_denominator": len(invalid),
            "unnecessary_refusals": sum(
                not bool(case["permissions"][rule]) for case in valid
            ),
            "valid_case_denominator": len(valid),
            "interpretation_errors": sum(
                case["interpretations"][rule] != case["expected_target_relationship"]
                for case in cases
            ),
            "case_count": len(cases),
        }
    return result


def _fmt(value: Any) -> str:
    return "not available" if value is None else f"{float(value):.3f}"


def _render_tables(benchmark: dict[str, Any], gate_metrics: dict[str, Any]) -> str:
    rows = [
        "| Condition | Exact target ID | n | Mean forecast | Event rate | Brier | ROC AUC | Evidence |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]

    def row(label: str, target_id: str, metrics: dict[str, Any]) -> str:
        auc = (
            "not available (constant scores)"
            if metrics["roc_auc"] is None
            else _fmt(metrics["roc_auc"])
        )
        return (
            f"| {label} | `{target_id}` | {metrics['n']} | {_fmt(metrics['mean_forecast'])} | "
            f"{_fmt(metrics['event_rate'])} | {_fmt(metrics['brier_score'])} | {auc} | [[C9]] |"
        )

    for lane in benchmark["lanes"]:
        rows.append(
            row(lane["lane"], lane["outcome_definition"]["id"], lane["metrics"])
        )
    control = benchmark["valid_same_target_control"]
    for lane in control["lanes"]:
        rows.append(
            row(
                f"{lane['lane']} (positive control)",
                lane["outcome_definition"]["id"],
                lane["metrics"],
            )
        )
    mixture = benchmark["declared_numeric_mixture"]
    rows.append(
        row(
            "Different-target numeric mixture",
            mixture["target_definition"]["id"],
            mixture["metrics"],
        )
    )
    rows.append(
        row(
            "Same-target positive-control mixture",
            control["target"]["id"],
            control["metrics"],
        )
    )
    table_a = "\n".join(rows)

    rows = [
        "| Rule | False permissions / invalid cases | Unnecessary refusals / valid cases | Interpretation errors / cases | Evidence |",
        "|---|---:|---:|---:|---|",
    ]
    for rule, values in gate_metrics.items():
        rows.append(
            f"| {rule.replace('_', ' ')} | {values['false_permissions']}/{values['invalid_case_denominator']} | "
            f"{values['unnecessary_refusals']}/{values['valid_case_denominator']} | "
            f"{values['interpretation_errors']}/{values['case_count']} | [[C10]] |"
        )
    table_b = "\n".join(rows)
    return (
        "# Recomputed manuscript tables\n\n"
        "Generated from the deterministic Benchmark A source and frozen operation-gate case records. "
        "The gate counts are independently reduced from the 23 case rows.\n\n"
        "## Table 1. Synthetic forecast targets and declared mixtures [[C9]]\n\n"
        + table_a
        + "\n\nThe different-target row is the named 50:50 mixture in the table; it is not a forecast of one common event.\n\n"
        "## Table 2. Operation-specific rule challenge [[C10]]\n\n"
        "The challenge cases are internally authored. Counts are descriptive and are not population error rates.\n\n"
        + table_b
        + "\n"
    )


def _markdown_tables(text: str) -> list[str]:
    output: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("|"):
            current.append(line)
        elif current:
            output.append("\n".join(current))
            current = []
    if current:
        output.append("\n".join(current))
    return output


def _assert_benchmark_claims(benchmark: dict[str, Any]) -> None:
    lanes = benchmark["lanes"]
    if [lane["lane"] for lane in lanes] != ["change", "operational"]:
        raise ValueError("Benchmark A lane identities changed")
    for lane in lanes:
        metrics = lane["metrics"]
        if (
            lane["n"] != 100
            or lane["forecast"] != 0.8
            or metrics["positive_count"] != 80
            or metrics["negative_count"] != 20
            or not abs(metrics["event_rate"] - 0.8) < 1e-12
            or not abs(metrics["brier_score"] - 0.16) < 1e-12
            or metrics["roc_auc"] is not None
        ):
            raise ValueError(f"Benchmark A numeric claim changed for {lane['lane']}")
    if lanes[0]["outcome_definition"] == lanes[1]["outcome_definition"]:
        raise ValueError("different-target lanes must remain distinct")
    mixture = benchmark["declared_numeric_mixture"]
    if (
        mixture["target_definition"]["id"]
        != "synthetic.mixture.change-30d-and-operational-30m.equal-weight"
        or mixture["weights"] != {"change": 0.5, "operational": 0.5}
        or mixture["is_one_common_event"] is not False
        or mixture["metrics"]["n"] != 200
        or mixture["metrics"]["positive_count"] != 160
        or mixture["metrics"]["event_rate"] != 0.8
        or mixture["metrics"]["mean_forecast"] != 0.8
        or mixture["metrics"]["brier_score"] != 0.16
    ):
        raise ValueError("declared mixture estimand changed")
    control = benchmark["valid_same_target_control"]
    if len(control["lanes"]) != 2 or any(
        lane["outcome_definition"] != control["target"] for lane in control["lanes"]
    ):
        raise ValueError("same-target positive control changed")
    if (
        control["metrics"]["n"] != 200
        or control["metrics"]["positive_count"] != 160
        or control["metrics"]["brier_score"] != 0.16
        or any(lane["metrics"]["n"] != 100 for lane in control["lanes"])
    ):
        raise ValueError("same-target control numeric result changed")


def _validate_numeric_prose(
    paper: str, benchmark: dict[str, Any], gate_metrics: dict[str, Any]
) -> None:
    lanes = benchmark["lanes"]
    first_metrics = lanes[0]["metrics"]
    expected_abstract = (
        f"two lanes each produced mean forecast {first_metrics['mean_forecast']:.1f}, "
        f"event rate {first_metrics['event_rate']:.1f}, and "
        f"Brier score {first_metrics['brier_score']:.2f}"
    )
    expected_results = (
        f"The two distinct-target lanes each have {lanes[0]['n']} observations, "
        f"mean forecast {first_metrics['mean_forecast']:.3f}, "
        f"event rate {first_metrics['event_rate']:.3f}, and "
        f"Brier score {first_metrics['brier_score']:.3f}."
    )
    expected_counterexample = (
        f"Two forecasts can each report \\(p={lanes[0]['forecast']:.1f}\\) and be calibrated "
        f"when their respective event rates are {first_metrics['event_rate']:.1f}"
    )
    if (
        expected_abstract not in paper
        or expected_results not in paper
        or expected_counterexample not in paper
    ):
        raise ValueError(
            "Benchmark A prose numbers do not match the recomputed results"
        )
    if "50:50 different-target mixture" not in paper:
        raise ValueError("the declared mixture weights are missing from the manuscript")

    operation = gate_metrics["operation_specific"]
    metadata = gate_metrics["metadata_only"]
    if (
        len(gate_metrics) != 4
        or operation["false_permissions"] != 0
        or operation["unnecessary_refusals"] != 0
        or operation["interpretation_errors"] != 0
        or metadata["false_permissions"] != 5
        or metadata["unnecessary_refusals"] != 0
        or metadata["interpretation_errors"] != 0
    ):
        raise ValueError("operation-gate prose result changed")
    expected_gate = (
        f"On the {operation['case_count']} internally authored cases, operation-specific gating made "
        "no false permissions, unnecessary refusals, or interpretation errors. "
        "Metadata-only gating also made no unnecessary refusals or interpretation errors, "
        "but it made five false permissions."
    )
    if expected_gate not in paper or "Four rules are compared" not in paper:
        raise ValueError(
            "operation-gate prose does not match the recomputed case counts"
        )


def _write_or_check(path: Path, content: str, write: bool) -> None:
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    elif not path.is_file() or path.read_text(encoding="utf-8") != content:
        raise ValueError(f"generated artifact is stale or changed: {path}")


def run(root: Path = ROOT, write: bool = True) -> dict[str, Any]:
    root = root.resolve()
    lock_result = _verify_lock(root)
    claim_result = _validate_claim_registry(root)
    saved = _json(root / RESULTS)
    benchmark = run_benchmark_a()
    generated_gate = run_gate_experiment()
    saved_gate = saved["gate_comparison"]
    if _canonical(saved["benchmark_a"]) != _canonical(benchmark):
        raise ValueError("frozen Benchmark A section no longer matches its source")
    for key in ("cases", "rules"):
        if _canonical(saved_gate[key]) != _canonical(generated_gate[key]):
            raise ValueError(
                f"frozen operation-gate {key} no longer matches its source"
            )
    _assert_benchmark_claims(benchmark)
    gate_metrics = _gate_case_metrics(saved_gate)
    tables = _render_tables(benchmark, gate_metrics)
    paper_text = (root / PAPER).read_text(encoding="utf-8")
    _validate_numeric_prose(paper_text, benchmark, gate_metrics)
    paper_tables = _markdown_tables(paper_text)
    rendered_tables = _markdown_tables(tables)
    if len(paper_tables) != 2 or paper_tables != rendered_tables:
        raise ValueError(
            "manuscript tables do not match the regenerated flagship tables"
        )

    output = {
        "schema_version": 1,
        "status": "reproduced for the pinned synthetic flagship records; not independent scientific replication",
        "source_record": {
            "path": str(RESULTS),
            "source_commit": "79df12d14a1b931863ea263cf6c827bd7cb9fd71",
            "full_file_sha256_at_source_commit": "02d3642044768c47957221a1e615dc221baf248b97eb4a61c8d75fa8eca80fcd",
            "consumed_sections": [
                "/benchmark_a",
                "/gate_comparison/cases",
                "/gate_comparison/rules",
            ],
        },
        "claim_registry": claim_result,
        "integrity": lock_result,
        "benchmark_a": benchmark,
        "operation_gate_cases": saved_gate["cases"],
        "operation_gate_case_metrics": gate_metrics,
        "operation_gate_case_count": len(saved_gate["cases"]),
        "excluded_data": [
            "shared_model result section in the source JSON",
            "six-role model outputs and runtime metadata",
            "Bouleusis retrieval and acquisition records",
            "operation-policy challenge v2 records",
        ],
        "interpretation_limits": [
            "All flagship experiments are synthetic and deterministic.",
            "The 23 policy cases were authored within the project and not independently adjudicated.",
            "A hash or replay establishes byte or calculation identity, not semantic truth or external validity.",
            "The operation-gate table reports only permission, refusal, and interpretation counts reduced from saved case rows.",
        ],
    }
    text = json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n"
    _write_or_check(root / OUTPUT, text, write)
    _write_or_check(root / TABLES, tables, write)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run(args.root, write=not args.check_only)
    except Exception as exc:
        parser.exit(1, f"FAIL: {type(exc).__name__}: {exc}\n")
    print(
        "PASS: flagship claims reproduced; "
        f"{result['claim_registry']['flagship_claims']} flagship claims; "
        f"{result['claim_registry']['companion_claims_excluded_from_reproduction']} companion claims out of scope"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
