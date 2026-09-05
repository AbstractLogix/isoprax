"""Deterministic replay constraints for real-data corpus follow-on work.

These constraints are intentionally narrow: they formalize the replay safety
rules that the Stage 1 spec requires, without importing any model or profile
implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .admission import CorpusRow, SplitDefinition

_DEFAULT_REPLAY_RULES = (
    "single_system_boundary",
    "cluster_by_change",
    "frozen_split_boundaries",
    "release_scope_metadata",
    "threshold_freeze",
)


class ReplayConstraintError(ValueError):
    """Raised when a candidate corpus violates a replay safety rule."""


@dataclass(frozen=True)
class ReplayConstraint:
    name: str
    description: str
    required: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("ReplayConstraint.name is required")


def build_replay_constraints() -> tuple[ReplayConstraint, ...]:
    return tuple(
        ReplayConstraint(name=name, description=description)
        for name, description in {
            "single_system_boundary": (
                "The admitted corpus must stay within one system boundary."
            ),
            "cluster_by_change": (
                "Rows derived from one change must not span multiple splits."
            ),
            "frozen_split_boundaries": (
                "Split windows must be predeclared and remain fixed."
            ),
            "release_scope_metadata": (
                "A manifest must declare the publishable scope of the corpus."
            ),
            "threshold_freeze": (
                "Threshold definitions must be frozen before corpus collection."
            ),
        }.items()
    )


def validate_replay_constraints(
    rows: Iterable[CorpusRow],
    *,
    split_definitions: Iterable[SplitDefinition] | None = None,
    expected_system_id: str | None = None,
    release_scope: str | None = None,
    threshold_frozen: bool = True,
    horizon_frozen: bool = True,
) -> None:
    """Validate the replay safety contract for a candidate corpus.

    The function raises `ReplayConstraintError` with a single explicit failure
    reason. It is intentionally deterministic and does not mutate the rows.
    """

    row_list = list(rows)
    systems = {r.system_id for r in row_list}

    if expected_system_id is not None and systems and systems != {expected_system_id}:
        raise ReplayConstraintError(
            "single_system_boundary: rows must match expected_system_id"
        )
    if len(systems) > 1:
        raise ReplayConstraintError(
            "single_system_boundary: cross-system pooling is forbidden"
        )

    if split_definitions is not None:
        required_splits = {s.name for s in split_definitions}
        observed_splits = {r.split for r in row_list}
        missing = sorted(required_splits - observed_splits)
        if missing:
            raise ReplayConstraintError(
                "frozen_split_boundaries: missing required split assignments "
                f"{missing}"
            )

        split_by_change: dict[str, set[str]] = {}
        for row in row_list:
            key = row.change_group_id or row.change_id
            split_by_change.setdefault(key, set()).add(row.split)
        leaking = sorted(k for k, v in split_by_change.items() if len(v) > 1)
        if leaking:
            raise ReplayConstraintError(
                "cluster_by_change: rows derived from one change span multiple splits"
            )

    if release_scope is None or not str(release_scope).strip():
        raise ReplayConstraintError("release_scope_metadata: release scope is required")
    if not threshold_frozen:
        raise ReplayConstraintError(
            "threshold_freeze: threshold definitions must be frozen before corpus collection"
        )
    if not horizon_frozen:
        raise ReplayConstraintError(
            "frozen_split_boundaries: horizon definition must be frozen before corpus collection"
        )


def _coerce_split_definitions(
    split_definitions: object,
) -> Iterable[SplitDefinition] | None:
    if split_definitions is None:
        return None
    if isinstance(split_definitions, (list, tuple)):
        converted: list[SplitDefinition] = []
        for split in split_definitions:
            if isinstance(split, SplitDefinition):
                converted.append(split)
                continue
            if isinstance(split, dict):
                converted.append(
                    SplitDefinition(
                        str(split["name"]),
                        str(split["start"]),
                        str(split["end"]),
                    )
                )
                continue
            raise ValueError("split_definitions must be SplitDefinition instances or dicts")
        return tuple(converted)
    if isinstance(split_definitions, SplitDefinition):
        return (split_definitions,)
    raise ValueError("split_definitions must be list-like or SplitDefinition")


def validate_replay_constraints_dict(
    rows: Iterable[CorpusRow],
    *,
    manifest: dict[str, object] | None = None,
    expected_system_id: str | None = None,
) -> None:
    """Validate an admitted candidate using a manifest-style dictionary."""

    manifest = manifest or {}
    split_definitions = manifest.get("split_definitions")
    if split_definitions is None:
        split_definitions = manifest.get("splits")
    validate_replay_constraints(
        rows,
        split_definitions=_coerce_split_definitions(split_definitions),
        expected_system_id=expected_system_id,
        release_scope=manifest.get("release_scope"),
        threshold_frozen=bool(manifest.get("thresholds_frozen", True)),
        horizon_frozen=bool(manifest.get("horizon_frozen", True)),
    )


__all__ = [
    "ReplayConstraint",
    "ReplayConstraintError",
    "_DEFAULT_REPLAY_RULES",
    "build_replay_constraints",
    "validate_replay_constraints",
    "validate_replay_constraints_dict",
]
