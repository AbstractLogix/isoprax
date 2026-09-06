from dataclasses import replace

import pytest

from isoprax.public_evidence import PublicEvidenceSnapshot, normalize_public_evidence


def snapshot(**changes):
    return replace(
        PublicEvidenceSnapshot(
            "system-a",
            "a" * 40,
            "https://example.test/source",
            "https://example.test/ci",
            "a" * 40,
            "2026-09-06T00:00:00Z",
        ),
        **changes,
    )


def test_normalizes_deterministically_without_payloads():
    second = snapshot(system_id="system-b", revision="b" * 40, ci_revision="b" * 40)
    first = normalize_public_evidence([second, snapshot()])
    assert first == normalize_public_evidence([snapshot(), second])
    assert first[0].claim_scope == "candidate_build_preparation_evidence_only"


def test_missing_ci_is_explicitly_unavailable():
    record = normalize_public_evidence([snapshot(ci_reference=None, ci_revision=None)])[
        0
    ]
    assert not record.available
    assert record.unavailable_reason


@pytest.mark.parametrize(
    "changes",
    [
        {"revision": "main"},
        {"source_reference": "https://token@bad"},
        {"uses_private_data": True},
        {"ci_revision": "b" * 40},
        {"observed_at": "bad"},
    ],
)
def test_rejects_unsafe_or_contradictory_input(changes):
    with pytest.raises(ValueError):
        normalize_public_evidence([snapshot(**changes)])


def test_rejects_duplicate_revision_per_system():
    with pytest.raises(ValueError):
        normalize_public_evidence([snapshot(), snapshot()])
