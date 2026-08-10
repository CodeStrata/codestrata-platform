"""Models for Slice 17.13 verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    PASS = "PASS"
    PASS_WITH_LIMITATIONS = "PASS_WITH_LIMITATIONS"
    FAIL = "FAIL"


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
    verdict: str
    total_checks: int
    failed_checks: int
    repository_target: int
    catalog_count: int
    suite_execution_status: str
    checks: list[dict[str, Any]] = field(default_factory=list)
    defects: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    statuses: dict[str, str] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    catalog: dict[str, Any] = field(default_factory=dict)
    epic17_boundary: dict[str, Any] = field(default_factory=dict)
    scenario_results: dict[str, bool] = field(default_factory=dict)
    repository_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
