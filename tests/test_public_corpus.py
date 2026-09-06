from dataclasses import replace

import pytest

from isoprax.public_corpus import (
    PublicCorpusSnapshot,
    normalize_public_corpus,
)


def snapshot(**changes):
    return replace(
        PublicCorpusSnapshot(
            "system-a",
            "https://example.test/corpus-entry",
            "threshold-v1",
            "2026-09-06T00:00:00Z",
            "2026-09-06T00:10:00Z",
            "observed_positive",
            None,
            "test",
            "change-group-a",
            ("manifest.json",),
            True,
            True,
        ),
        **changes,
    )


def test_normalizes_deterministically_and_preserves_ordered_identity():
    first = snapshot()
    second = snapshot(
        system_id="system-b",
        score_time="2026-09-07T00:00:00Z",
        window_end="2026-09-07T00:10:00Z",
        change_group_id="change-group-b",
    )
    left = normalize_public_corpus([second, first])
    right = normalize_public_corpus([first, second])

    assert left == right
    assert left[0].system_id == "system-a"
    assert left[0].outcome_class == "observed_positive"
    assert left[0].censor_reason is None


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"artifacts_complete": False}, "incomplete"),
        ({"valid": False}, "invalid"),
    ],
)
def test_incomplete_or_invalid_snapshots_are_censored(changes, reason):
    record = normalize_public_corpus([snapshot(**changes)])[0]

    assert record.outcome_class == "censored"
    assert reason in record.censor_reason


@pytest.mark.parametrize(
    "changes",
    [
        {"source_reference": "https://token@bad"},
        {"source_reference": "https://example.test/corpus-entry?token=bad"},
        {"uses_private_data": True},
        {"uses_privileged_telemetry": True},
        {"split": "unknown"},
        {"outcome_class": "other"},
        {"window_end": "2026-09-05T00:00:00Z"},
        {"score_time": "2026-09-06T00:00:00+00:00"},
        {"score_time": "not-a-timeZ"},
        {"artifacts": ()},
        {"artifacts": ("manifest.json", "manifest.json")},
        {"change_group_id": " "},
    ],
)
def test_rejects_unsafe_or_invalid_snapshots(changes):
    with pytest.raises(ValueError):
        normalize_public_corpus([snapshot(**changes)])


def test_rejects_censored_without_reason():
    with pytest.raises(ValueError, match="requires reason"):
        normalize_public_corpus(
            [snapshot(outcome_class="censored", censor_reason=None)]
        )


def test_rejects_invalid_or_duplicate_snapshots():
    with pytest.raises(ValueError):
        normalize_public_corpus([object()])
    with pytest.raises(ValueError):
        normalize_public_corpus([snapshot(), snapshot()])
