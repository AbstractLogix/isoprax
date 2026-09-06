from dataclasses import replace

import pytest

from isoprax.public_observation import (
    PublicObservationSnapshot,
    normalize_public_observations,
)


def snapshot(**changes):
    return replace(
        PublicObservationSnapshot(
            "system-a",
            "https://example.test/observation",
            "threshold-v1",
            "2026-09-06T00:00:00Z",
            "2026-09-06T00:10:00Z",
            ("result.json",),
            True,
            True,
        ),
        **changes,
    )


def test_normalizes_deterministically():
    second = snapshot(
        system_id="system-b",
        score_time="2026-09-07T00:00:00Z",
        window_end="2026-09-07T00:10:00Z",
    )
    assert normalize_public_observations(
        [second, snapshot()]
    ) == normalize_public_observations([snapshot(), second])
    assert normalize_public_observations([snapshot()])[0].outcome_class == "observed"


@pytest.mark.parametrize(
    "changes,reason",
    [({"artifacts_complete": False}, "incomplete"), ({"valid": False}, "invalid")],
)
def test_incomplete_or_invalid_observations_are_censored(changes, reason):
    record = normalize_public_observations([snapshot(**changes)])[0]
    assert record.outcome_class == "censored"
    assert reason in record.censor_reason


@pytest.mark.parametrize(
    "changes",
    [
        {"source_reference": "https://token@bad"},
        {"source_reference": "https://example.test/observation?token=bad"},
        {"uses_private_data": True},
        {"uses_privileged_telemetry": True},
        {"window_end": "2026-09-05T00:00:00Z"},
        {"score_time": "2026-09-06T00:00:00+00:00"},
        {"score_time": "not-a-timeZ"},
        {"artifacts": ()},
    ],
)
def test_rejects_unsafe_or_invalid_observations(changes):
    with pytest.raises(ValueError):
        normalize_public_observations([snapshot(**changes)])


def test_rejects_invalid_or_duplicate_snapshots():
    with pytest.raises(ValueError):
        normalize_public_observations([object()])
    with pytest.raises(ValueError):
        normalize_public_observations([snapshot(), snapshot()])
