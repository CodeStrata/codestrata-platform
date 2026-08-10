"""Models for Slice 17.17."""

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
    consent_register: dict[str, Any] = field(default_factory=dict)
    epic17_boundary: dict[str, Any] = field(default_factory=dict)
    state_machine: dict[str, Any] = field(default_factory=dict)
    persistence: dict[str, Any] = field(default_factory=dict)
    precedence: dict[str, Any] = field(default_factory=dict)
    interactive: dict[str, Any] = field(default_factory=dict)
    non_interactive: dict[str, Any] = field(default_factory=dict)
    cli: dict[str, Any] = field(default_factory=dict)
    report_publish: dict[str, Any] = field(default_factory=dict)
    event_types: dict[str, Any] = field(default_factory=dict)
    auth: dict[str, Any] = field(default_factory=dict)
    identity: dict[str, Any] = field(default_factory=dict)
    payload_privacy: dict[str, Any] = field(default_factory=dict)
    offline: dict[str, Any] = field(default_factory=dict)
    data_lake: dict[str, Any] = field(default_factory=dict)
    insights: dict[str, Any] = field(default_factory=dict)
    vscode_contract: dict[str, Any] = field(default_factory=dict)
    docs: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    scenario_results: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
