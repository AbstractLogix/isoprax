from isoprax.public_label_evidence import (
    PublicLabelEvidenceManifest,
    PublicLabelSource,
    PublicLabelStatus,
    reduce_public_label_evidence,
)


def manifest(**changes):
    values = {
        "sources": (PublicLabelSource("apachejit", "2022", "Apache-2.0", "zenodo:1"),),
        "left_definition": "SZZ labels later fix-linked commits",
        "right_definition": "revert-labelled defect-inducing commits",
        "aligned_event_ids": ("c1", "c2"),
        "disagreement_count": 1,
    }
    values.update(changes)
    return PublicLabelEvidenceManifest(**values)


def test_valid_public_label_manifest_is_reproduced():
    record = reduce_public_label_evidence(manifest())

    assert record.status == PublicLabelStatus.REPRODUCED
    assert record.disagreement_count == 1
    assert "not Semantic" in record.claim_boundary


def test_unavailable_or_unlicensed_public_data_is_blocked():
    unavailable = reduce_public_label_evidence(manifest(sources_available=False))
    unlicensed = reduce_public_label_evidence(manifest(licenses_verified=False))

    assert unavailable.status == PublicLabelStatus.BLOCKED
    assert unlicensed.status == PublicLabelStatus.BLOCKED


def test_changed_source_identity_is_inconclusive():
    record = reduce_public_label_evidence(manifest(source_identities_current=False))

    assert record.status == PublicLabelStatus.INCONCLUSIVE
