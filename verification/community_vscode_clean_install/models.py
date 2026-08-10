"""Models for Slice 17.21."""

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
    register: dict[str, Any] = field(default_factory=dict)
    epic17_boundary: dict[str, Any] = field(default_factory=dict)
    package: dict[str, Any] = field(default_factory=dict)
    profile: dict[str, Any] = field(default_factory=dict)
    install: dict[str, Any] = field(default_factory=dict)
    activation: dict[str, Any] = field(default_factory=dict)
    engine_discovery: dict[str, Any] = field(default_factory=dict)
    repository: dict[str, Any] = field(default_factory=dict)
    assessment: dict[str, Any] = field(default_factory=dict)
    report: dict[str, Any] = field(default_factory=dict)
    lifecycle: dict[str, Any] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)
    api_authority: dict[str, Any] = field(default_factory=dict)
    publishing: dict[str, Any] = field(default_factory=dict)
    no_ai: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, Any] = field(default_factory=dict)
    offline: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    privacy: dict[str, Any] = field(default_factory=dict)
    performance: dict[str, Any] = field(default_factory=dict)
    ux: dict[str, Any] = field(default_factory=dict)
    docs: dict[str, Any] = field(default_factory=dict)
    export: dict[str, Any] = field(default_factory=dict)
    prior_slices: dict[str, Any] = field(default_factory=dict)
    scenario_results: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
