"""Models for Slice 17.27 Epic 17 completion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]
EpicVerdict = Literal[
    "EPIC_COMPLETE",
    "EPIC_COMPLETE_WITH_RELEASE_CARRY_FORWARDS",
    "EPIC_BLOCKED",
]


@dataclass(slots=True)
class CheckResult:
    check_id: str
    ok: bool
    detail: str
    category: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Defect:
    classification: str
    check_id: str
    expected: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Report:
    schema: str
    schema_version: str
    package_id: str
    package_version: str
    epic: int
    slice: str
    suite_id: str
    verdict: Verdict
    epic_verdict: EpicVerdict
    total_checks: int
    failed_checks: int
    checks: list[dict[str, Any]] = field(default_factory=list)
    defects: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    statuses: dict[str, str] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    capability_matrix: dict[str, str] = field(default_factory=dict)
    production_health: dict[str, Any] = field(default_factory=dict)
    insights_auth: dict[str, Any] = field(default_factory=dict)
    community_status: dict[str, Any] = field(default_factory=dict)
    zero_drift: dict[str, Any] = field(default_factory=dict)
    defect_inventory: list[dict[str, Any]] = field(default_factory=list)
    release_carry_forwards: list[dict[str, Any]] = field(default_factory=list)
    transparency_handoff: dict[str, Any] = field(default_factory=dict)
    worktree: dict[str, Any] = field(default_factory=dict)
    security_scan: dict[str, Any] = field(default_factory=dict)
    export_readiness: dict[str, Any] = field(default_factory=dict)
    epic17_boundary: dict[str, Any] = field(default_factory=dict)
    freeze_confirmations: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
