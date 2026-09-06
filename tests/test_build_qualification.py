import pytest

from isoprax.build_qualification import (
    BuildSample,
    LegalCoverageRecord,
    RunnerDescriptor,
    execute_prepared_sample,
    prepare_build_sample,
    reduce_build_qualification,
)


def sample(*, covered=True, runner=None):
    commits = ("a", "b", "c")
    return BuildSample(
        commits,
        "recipe-v1",
        tuple(LegalCoverageRecord(c, f"licence/{c}", covered) for c in commits),
        runner or RunnerDescriptor("example@sha256:abc", True, True),
    )


def test_preparation_is_stable_and_blocks_before_runner_for_missing_coverage():
    prepared = prepare_build_sample(sample())
    assert prepared.preparation_hash == prepare_build_sample(sample()).preparation_hash
    blocked = prepare_build_sample(sample(covered=False))
    rows = execute_prepared_sample(blocked, lambda *_: pytest.fail("must not invoke"))
    assert {row.status for row in rows} == {"blocked-before-compilation"}


def test_execution_retains_all_rows_and_reduction_is_complete_only():
    prepared = prepare_build_sample(sample())
    outcomes = iter(
        ({"status": "success"}, {"status": "build_failed"}, {"status": "success"})
    )
    rows = execute_prepared_sample(prepared, lambda *_: next(outcomes))
    report = reduce_build_qualification(prepared, rows, frozen_build_floor=0.6)
    assert [row.status for row in rows] == ["success", "censored", "success"]
    assert report.qualified is True
    assert report.claim_scope == "build_qualification_only"
    assert (
        reduce_build_qualification(
            prepared, rows[:2], frozen_build_floor=0.0
        ).measured_success_rate
        is None
    )
    assert not reduce_build_qualification(
        prepared, rows, frozen_build_floor=0.0, failures_clustered=True
    ).qualified
