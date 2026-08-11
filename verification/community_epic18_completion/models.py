"""Models for Slice 18.8 Epic 18 completion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]
EpicVerdict = Literal[
    "EPIC_COMPLETE",
    "EPIC_COMPLETE_WITH_DOCUMENTED_LIMITATIONS",
    "EPIC_BLOCKED",
]
Epic19Gate = Literal[
    "EPIC_19_RELEASE_READINESS_MAY_START",
    "EPIC_19_RELEASE_READINESS_MUST_NOT_START",
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
    epic19_gate: Epic19Gate
    total_checks: int
    failed_checks: int
    checks: list[dict[str, Any]] = field(default_factory=list)
    defects: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    statuses: dict[str, str] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    evidence_inventory: list[dict[str, Any]] = field(default_factory=list)
    claim_inventory: dict[str, Any] = field(default_factory=dict)
    contradiction_closure: dict[str, Any] = field(default_factory=dict)
    slice_matrix: dict[str, Any] = field(default_factory=dict)
    topic_verification: dict[str, str] = field(default_factory=dict)
    security_scan: dict[str, Any] = field(default_factory=dict)
    prior_suites: dict[str, Any] = field(default_factory=dict)
    release_carry_forwards: list[dict[str, Any]] = field(default_factory=list)
    epic18_boundary: dict[str, Any] = field(default_factory=dict)
    freeze_confirmations: dict[str, bool] = field(default_factory=dict)
    sv18_7_baseline: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
