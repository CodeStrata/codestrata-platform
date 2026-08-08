"""Screen reader validation boundary."""

from __future__ import annotations

from verification.responsive_accessibility.contract import ALLOWED_LIMITATIONS
from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult

_CATEGORY = "screen_reader_boundary"
_LIMITATION = "manual_screen_reader_validation_not_performed"


def check_screen_reader_boundary(inv: SurfaceInventory) -> list[CheckResult]:
    policy_limits = set(inv.policy.get("limitations", []))
    allowed = set(ALLOWED_LIMITATIONS)
    return [
        CheckResult(
            "screen_reader_boundary:manual_not_performed",
            True,
            _LIMITATION,
            _CATEGORY,
        ),
        CheckResult(
            "screen_reader_boundary:no_certification_claim",
            inv.policy.get("formal_certification_claimed") is False,
            "not_certified",
            _CATEGORY,
        ),
        CheckResult(
            "screen_reader_boundary:limitation_declared",
            _LIMITATION in policy_limits and _LIMITATION in allowed,
            _LIMITATION,
            _CATEGORY,
        ),
    ]
