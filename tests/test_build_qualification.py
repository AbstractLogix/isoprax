import pytest
from hypothesis import given
from hypothesis import strategies as st

from isoprax.build_qualification import (
    BuildRowResult,
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


@pytest.mark.parametrize(
    "runner",
    (
        RunnerDescriptor("example:latest", True, True),
        RunnerDescriptor("example@sha256:abc", False, True),
        RunnerDescriptor("example@sha256:abc", True, False),
    ),
)
def test_runner_preflight_blocks_unsafe_execution_before_invocation(runner):
    blocked = prepare_build_sample(sample(runner=runner))

    assert blocked.blocked_reason == "runner is not immutable, non-root, and writable"
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


def test_qualification_rejects_invalid_samples_and_runner_interruptions():
    with pytest.raises(ValueError, match="duplicate-free"):
        prepare_build_sample(
            BuildSample(
                ("a", "a"),
                "recipe-v1",
                (LegalCoverageRecord("a", "licence/a"),),
                RunnerDescriptor("example@sha256:abc", True, True),
            )
        )
    with pytest.raises(ValueError, match="recipe_reference"):
        prepare_build_sample(
            BuildSample(
                ("a",),
                "",
                (LegalCoverageRecord("a", "licence/a"),),
                RunnerDescriptor("example@sha256:abc", True, True),
            )
        )

    prepared = prepare_build_sample(sample())
    rows = execute_prepared_sample(
        prepared, lambda *_: (_ for _ in ()).throw(RuntimeError("offline"))
    )
    assert {row.status for row in rows} == {"blocked-before-compilation"}
    unavailable = reduce_build_qualification(prepared, rows, frozen_build_floor=0.0)
    assert unavailable.measured_success_rate is None

    low_rate = (
        BuildRowResult("a", "success", "ok"),
        BuildRowResult("b", "censored", "failed"),
        BuildRowResult("c", "censored", "failed"),
    )
    assert not reduce_build_qualification(
        prepared, low_rate, frozen_build_floor=0.5
    ).qualified


@given(st.lists(st.text(min_size=1, max_size=12), min_size=1, max_size=12, unique=True))
def test_preparation_hash_and_rows_are_deterministic_for_any_safe_commit_set(commits):
    commits = tuple(commits)
    candidate = BuildSample(
        commits,
        "recipe-v1",
        tuple(LegalCoverageRecord(commit, f"licence/{commit}") for commit in commits),
        RunnerDescriptor("example@sha256:abc", True, True),
    )
    prepared = prepare_build_sample(candidate)
    assert prepare_build_sample(candidate).preparation_hash == prepared.preparation_hash
    assert [
        row.commit
        for row in execute_prepared_sample(
            prepared, lambda _commit, _recipe: {"status": "success"}
        )
    ] == list(commits)
