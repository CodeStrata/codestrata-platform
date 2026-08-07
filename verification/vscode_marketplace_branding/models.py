"""Models for Slice 13.12 Marketplace branding verification."""

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
class VsCodeMarketplaceBrandingReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    branding_policy_status: str = "not_executed"
    product_naming_status: str = "not_executed"
    metadata_status: str = "not_executed"
    icon_status: str = "not_executed"
    gallery_banner_status: str = "not_executed"
    screenshot_status: str = "not_executed"
    gallery_order_status: str = "not_executed"
    asset_safety_status: str = "not_executed"
    package_inventory_status: str = "not_executed"
    cursor_absence_status: str = "not_executed"
    claim_review_status: str = "not_executed"
    accessibility_status: str = "not_executed"
    link_inventory_status: str = "not_executed"
    website_reference_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    deferred_marketplace_documentation_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_status": self.accessibility_status,
            "asset_safety_status": self.asset_safety_status,
            "blockers": list(self.blockers),
            "branding_policy_status": self.branding_policy_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "claim_review_status": self.claim_review_status,
            "cursor_absence_status": self.cursor_absence_status,
            "deferred_marketplace_documentation_status": (
                self.deferred_marketplace_documentation_status
            ),
            "defects": [d.to_dict() for d in self.defects],
            "failed_checks": self.failed_checks,
            "gallery_banner_status": self.gallery_banner_status,
            "gallery_order_status": self.gallery_order_status,
            "icon_status": self.icon_status,
            "limitations": sorted(self.limitations),
            "link_inventory_status": self.link_inventory_status,
            "metadata_status": self.metadata_status,
            "package_inventory_status": self.package_inventory_status,
            "product_naming_status": self.product_naming_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "screenshot_status": self.screenshot_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
            "website_reference_status": self.website_reference_status,
        }
