"""Models for Slice 17.22."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


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
    total_checks: int
    failed_checks: int
    checks: list[dict[str, Any]] = field(default_factory=list)
    defects: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    statuses: dict[str, str] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    defect_inventory: dict[str, Any] = field(default_factory=dict)
    providers: dict[str, Any] = field(default_factory=dict)
    ai_usage: dict[str, Any] = field(default_factory=dict)
    identity_retention: dict[str, Any] = field(default_factory=dict)
    git_security: dict[str, Any] = field(default_factory=dict)
    public_urls: dict[str, Any] = field(default_factory=dict)
    worktree: dict[str, Any] = field(default_factory=dict)
    exports: dict[str, Any] = field(default_factory=dict)
    domains: dict[str, Any] = field(default_factory=dict)
    report_storage: dict[str, Any] = field(default_factory=dict)
    data_lake: dict[str, Any] = field(default_factory=dict)
    insights: dict[str, Any] = field(default_factory=dict)
    assessment: dict[str, Any] = field(default_factory=dict)
    eir: dict[str, Any] = field(default_factory=dict)
    vscode: dict[str, Any] = field(default_factory=dict)
    docs: dict[str, Any] = field(default_factory=dict)
    infrastructure: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    stale_limitations: dict[str, Any] = field(default_factory=dict)
    release_carry_forward: dict[str, Any] = field(default_factory=dict)
    prior_slices: dict[str, Any] = field(default_factory=dict)
    epic17_boundary: dict[str, Any] = field(default_factory=dict)
    scenario_results: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
