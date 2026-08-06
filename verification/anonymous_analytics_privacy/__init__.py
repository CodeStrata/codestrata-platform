"""Anonymous analytics privacy verification (Epic 10 Slice 10.8).

Verification-only package. Does not ship in Engine or VS Code runtimes.
Does not enable analytics collection or transmission.
"""

from __future__ import annotations

ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_ID = "sv10-8-anonymous-analytics-privacy"
ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_VERSION = "1.0.0"

__all__ = [
    "ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_ID",
    "ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_VERSION",
]
