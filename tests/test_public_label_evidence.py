from isoprax.commensurability import ObservationProcess, OutcomeDefinition, Window
from isoprax.public_label_evidence import (
    PublicLabelComparisonStatus,
    PublicLabelDefinition,
    PublicLabelEvidenceManifest,
    PublicLabelProcedure,
    PublicLabelSource,
    PublicLabelStatus,
    build_public_label_semantics_report,
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


def definition(source_id, *, days=7, event="defect", process="szz", **changes):
    source = PublicLabelSource(
        source_id, "1.0", "Apache-2.0", f"snapshot:{source_id}", f"sha:{source_id}"
    )
    values = {
        "source": source,
        "outcome_definition": OutcomeDefinition(
            f"{source_id}-outcome",
            event,
            ObservationProcess(process),
            Window(days, "day", "commit"),
        ),
        "procedure": PublicLabelProcedure("temporal", "split:1", "model:1", "frozen"),
        "retained_observations": False,
        "aligned_event_count": 10,
    }
    values.update(changes)
    return PublicLabelDefinition(**values)


def test_semantics_report_is_sorted_and_preserves_procedure_metadata():
    report = build_public_label_semantics_report([definition("b"), definition("a")])

    assert report.status == PublicLabelStatus.REPRODUCED
    assert [item.source.source_id for item in report.sources] == ["a", "b"]
    assert report.sources[0].procedure.model_version == "model:1"
    assert report.comparisons[0].status == PublicLabelComparisonStatus.DIRECT
    assert report.comparisons[0].pooling_permitted is False


def test_window_difference_requires_bridge_evidence():
    report = build_public_label_semantics_report(
        [definition("a"), definition("b", days=90)]
    )
    assert report.comparisons[0].status == PublicLabelComparisonStatus.BRIDGEABLE
    assert report.comparisons[0].pooling_permitted is False
    assert "required" in report.comparisons[0].reason

    bridged = build_public_label_semantics_report(
        [
            definition("a", retained_observations=True, bridge_provenance="raw:a"),
            definition(
                "b", days=90, retained_observations=True, bridge_provenance="raw:b"
            ),
        ]
    )
    assert bridged.comparisons[0].status == PublicLabelComparisonStatus.BRIDGEABLE
    assert bridged.comparisons[0].pooling_permitted is False


def test_event_or_observation_process_difference_is_irreducible():
    report = build_public_label_semantics_report(
        [definition("a"), definition("b", process="revert")]
    )
    assert report.comparisons[0].status == PublicLabelComparisonStatus.IRREDUCIBLE
    assert report.comparisons[0].pooling_permitted is False


def test_unavailable_source_blocks_report_and_comparison():
    report = build_public_label_semantics_report(
        [definition("a"), definition("b", available=False)]
    )
    assert report.status == PublicLabelStatus.BLOCKED
    assert report.comparisons[0].status == PublicLabelComparisonStatus.UNAVAILABLE


def test_unknown_procedure_values_are_preserved_and_invalid_split_rejected():
    assert PublicLabelProcedure().model_version == "unknown"
    assert PublicLabelProcedure().adaptation_policy == "unknown"
    blank = PublicLabelProcedure(model_version="", adaptation_policy="")
    assert blank.model_version == "unknown"
    assert blank.adaptation_policy == "unknown"
    try:
        PublicLabelProcedure("rolling")
    except ValueError as error:
        assert "split_strategy" in str(error)
    else:
        raise AssertionError("invalid split strategy was accepted")


def test_duplicate_sources_and_negative_counts_are_rejected():
    try:
        build_public_label_semantics_report([definition("a"), definition("a")])
    except ValueError as error:
        assert "unique" in str(error)
    else:
        raise AssertionError("duplicate source was accepted")
    try:
        definition("negative", aligned_event_count=-1)
    except ValueError as error:
        assert "non-negative" in str(error)
    else:
        raise AssertionError("negative count was accepted")


def test_missing_provenance_is_inconclusive_or_blocked():
    assert (
        reduce_public_label_evidence(manifest(sources=(), left_definition="")).status
        == PublicLabelStatus.INCONCLUSIVE
    )
    assert (
        definition(
            "nolicense", source=PublicLabelSource("nolicense", "1", "", "ref")
        ).status
        == PublicLabelStatus.BLOCKED
    )
    assert (
        definition("changed", source_identity_current=False).status
        == PublicLabelStatus.INCONCLUSIVE
    )
    assert (
        definition(
            "noversion", source=PublicLabelSource("noversion", "", "MIT", "ref")
        ).status
        == PublicLabelStatus.INCONCLUSIVE
    )
    assert (
        definition("noref", source=PublicLabelSource("noref", "1", "MIT", "")).status
        == PublicLabelStatus.INCONCLUSIVE
    )


def test_empty_source_and_definition_ids_are_rejected():
    try:
        definition("ignored", source=PublicLabelSource("", "1", "MIT", "ref"))
    except ValueError as error:
        assert "source_id" in str(error)
    else:
        raise AssertionError("empty source id was accepted")
    try:
        definition(
            "ignored",
            outcome_definition=OutcomeDefinition(
                "", "defect", ObservationProcess("szz"), Window(7, "day", "commit")
            ),
        )
    except ValueError as error:
        assert "outcome definition" in str(error)
    else:
        raise AssertionError("empty outcome definition id was accepted")
