"""
Isoprax normalized event model (spec Section 4).

Three event types, two families. This module is the normative data contract:
everything downstream sees only these shapes. Adapters (out of scope for
conformance) are responsible for translating vendor data into these.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class Family(str, Enum):
    CHANGE = "change"
    OPERATIONAL = "operational"


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    # RFC 3339 UTC, per spec 4.1
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Event:
    """Common fields required of every event (spec 4.1)."""

    id: str = field(default_factory=_new_id)
    timestamp: str = field(default_factory=_now)
    source: str = "unknown"
    # family is set by subclasses; declared here for a uniform interface
    family: Family = Family.OPERATIONAL

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["family"] = self.family.value
        d["event_type"] = type(self).__name__
        return d


@dataclass
class ChangeEvent(Event):
    """A unit of source-code change (spec 4.2). Change family."""

    family: Family = Family.CHANGE
    repo: str = ""
    change_ref: str = ""
    author: Optional[str] = None
    files_touched: list[str] = field(default_factory=list)
    loc_added: int = 0
    loc_removed: int = 0
    linked_ticket_ids: list[str] = field(default_factory=list)
    ci_result: Optional[str] = None
    deploy_result: Optional[str] = None
    # single extensible field (spec 4.4)
    features: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # mandatory-field enforcement (spec 4.2)
        if not self.repo or not self.change_ref:
            raise ValueError("ChangeEvent requires 'repo' and 'change_ref'")
        # spec 4.1: family is derived from type; a mismatch MUST be rejected
        if self.family != Family.CHANGE:
            raise ValueError(
                f"ChangeEvent family MUST be 'change' (spec 4.1); got '{self.family}'"
            )


@dataclass
class RunEvent(Event):
    """A single execution of a job/task/service (spec 4.3). Operational family."""

    family: Family = Family.OPERATIONAL
    job_type: str = ""
    job_identifier: str = ""
    exit_status: str = ""
    duration: Optional[float] = None
    resource_metrics: dict[str, Any] = field(default_factory=dict)  # extensible

    def __post_init__(self) -> None:
        if not self.job_type or not self.exit_status:
            raise ValueError("RunEvent requires 'job_type' and 'exit_status'")
        if self.family != Family.OPERATIONAL:
            raise ValueError(
                f"RunEvent family MUST be 'operational' (spec 4.1); got '{self.family}'"
            )


@dataclass
class MetricSample(Event):
    """One time-series observation (spec 4.3). Operational family."""

    family: Family = Family.OPERATIONAL
    resource_id: str = ""
    resource_type: str = ""
    value: float = 0.0
    unit: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.resource_id or not self.resource_type:
            raise ValueError("MetricSample requires 'resource_id' and 'resource_type'")
        if self.family != Family.OPERATIONAL:
            raise ValueError(
                "MetricSample family MUST be 'operational' (spec 4.1); "
                f"got '{self.family}'"
            )
