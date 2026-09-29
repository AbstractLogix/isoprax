"""Differential checks for the CI-only Haskell semantic oracle."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from isoprax.commensurability import OutcomeDefinition, check_commensurable
from isoprax.evaluation import authorized_pooled_ece
from isoprax.semantic_types import (
    CalibrationPolicy,
    _definition_content_digest,
    authorize_pooled_comparison,
    calibration_sample_digest,
    establish_calibration,
    establish_commensurability,
)


class LeftFamily:
    pass


class RightFamily:
    pass


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/reference/semantic-oracle/contract-v1.json"
ORACLE = os.environ.get("ISOPRAX_SEMANTIC_ORACLE_BIN")


def _definition(raw: dict[str, Any]) -> OutcomeDefinition:
    return OutcomeDefinition(
        id=raw["id"],
        event=raw["event"],
        observation_process=raw["observation_process"],
        window=raw["window"],
        thresholds=raw.get("thresholds", ()),
        description=raw.get("description", ""),
    )


def _policy(raw: dict[str, Any]) -> CalibrationPolicy:
    return CalibrationPolicy(
        min_events=raw["min_events"],
        n_bins=raw["n_bins"],
        max_ece=raw["max_ece"],
    )


def _python_projection(case: dict[str, Any]) -> dict[str, Any]:
    left = _definition(case["left"])
    right = _definition(case["right"])
    left_cal = case["left_calibration"]
    right_cal = case["right_calibration"]
    left_cal_definition = _definition(left_cal["definition"])
    right_cal_definition = _definition(right_cal["definition"])
    left_policy = _policy(left_cal["policy"])
    right_policy = _policy(right_cal["policy"])
    left_scores = left_cal["scores"]
    left_outcomes = left_cal["outcomes"]
    right_scores = right_cal["scores"]
    right_outcomes = right_cal["outcomes"]

    commensurable = check_commensurable(left, right).commensurable
    left_evidence = right_evidence = None
    try:
        left_evidence = establish_calibration(
            left_cal_definition,
            left_scores,
            left_outcomes,
            tag=LeftFamily,
            min_events=left_policy.min_events,
            n_bins=left_policy.n_bins,
            max_ece=left_policy.max_ece,
        )
    except ValueError:
        pass
    try:
        right_evidence = establish_calibration(
            right_cal_definition,
            right_scores,
            right_outcomes,
            tag=RightFamily,
            min_events=right_policy.min_events,
            n_bins=right_policy.n_bins,
            max_ece=right_policy.max_ece,
        )
    except ValueError:
        pass

    authorization = None
    if commensurable and left_evidence is not None and right_evidence is not None:
        try:
            commensurability = establish_commensurability(
                left,
                right,
                left_tag=LeftFamily,
                right_tag=RightFamily,
            )
            authorization = authorize_pooled_comparison(
                commensurability, left_evidence, right_evidence
            )
        except ValueError:
            pass

    pooled_ece = None
    if authorization is not None:
        pooled = case["pooled"]
        try:
            pooled_ece = authorized_pooled_ece(
                authorization,
                pooled["left_scores"],
                pooled["left_outcomes"],
                pooled["right_scores"],
                pooled["right_outcomes"],
            )
        except ValueError:
            pass

    return {
        "commensurable": commensurable,
        "definition_digests": {
            "left": _definition_content_digest(left),
            "right": _definition_content_digest(right),
            "left_calibration": _definition_content_digest(left_cal_definition),
            "right_calibration": _definition_content_digest(right_cal_definition),
        },
        "calibration_passes": {
            "left": left_evidence is not None,
            "right": right_evidence is not None,
        },
        "sample_digests": {
            "left": calibration_sample_digest(left_scores, left_outcomes),
            "right": calibration_sample_digest(right_scores, right_outcomes),
        },
        "policy_digests": {
            "left": left_policy.digest,
            "right": right_policy.digest,
        },
        "authorized": authorization is not None,
        "pooled_ece": pooled_ece,
    }


@pytest.mark.skipif(not ORACLE, reason="Haskell oracle executable is provided by CI")
def test_python_and_haskell_match_shared_semantic_fixtures() -> None:
    fixtures = json.loads(FIXTURE.read_text(encoding="utf-8"))
    completed = subprocess.run(
        [ORACLE],
        input=json.dumps(fixtures),
        text=True,
        capture_output=True,
        check=True,
    )
    haskell_results = json.loads(completed.stdout)
    assert len(haskell_results) == len(fixtures)

    for case, haskell in zip(fixtures, haskell_results, strict=True):
        python = _python_projection(case)
        for key in (
            "commensurable",
            "definition_digests",
            "calibration_passes",
            "sample_digests",
            "policy_digests",
            "authorized",
        ):
            assert haskell[key] == python[key], case["name"]
        if python["pooled_ece"] is None:
            assert haskell["pooled_ece"] is None, case["name"]
        else:
            assert haskell["pooled_ece"] == pytest.approx(
                python["pooled_ece"], abs=1e-12
            ), case["name"]
