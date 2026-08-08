"""Models for Slice 14.2 verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    category: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "detail": self.detail,
            "name": self.name,
            "ok": self.ok,
        }


@dataclass(frozen=True, slots=True)
class Defect:
    classification: str
    surface: str
    expected: str
    observed: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CommunityDocsRedesignReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "14"
    slice: str = "14.2"
    documentation_policy: str = "community-documentation-redesign-policy:1.0"
    design_system_consumed: bool = False
    community_only_scope: bool = False
    tokens_status: str = "not_executed"
    navigation_status: str = "not_executed"
    components_status: str = "not_executed"
    typography_status: str = "not_executed"
    accessibility_status: str = "not_executed"
    responsive_status: str = "not_executed"
    dark_mode_status: str = "not_executed"
    mobile_status: str = "not_executed"
    no_product_redesign_status: str = "not_executed"
    slice_14_8_absence_status: str = "not_executed"
    release_posture: dict[str, Any] = field(default_factory=dict)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_status": self.accessibility_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "community_only_scope": self.community_only_scope,
            "components_status": self.components_status,
            "dark_mode_status": self.dark_mode_status,
            "defects": [d.to_dict() for d in self.defects],
            "design_system_consumed": self.design_system_consumed,
            "documentation_policy": self.documentation_policy,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "limitations": sorted(self.limitations),
            "mobile_status": self.mobile_status,
            "navigation_status": self.navigation_status,
            "no_product_redesign_status": self.no_product_redesign_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "responsive_status": self.responsive_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_14_8_absence_status": self.slice_14_8_absence_status,
            "tokens_status": self.tokens_status,
            "total_checks": self.total_checks,
            "typography_status": self.typography_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
