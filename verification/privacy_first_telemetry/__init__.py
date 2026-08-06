"""Cross-client privacy-first telemetry verification (Epic 9 Slice 9.14).

Verification-only package. Does not ship in Engine or VS Code runtimes.
Does not create a shared runtime schema.
"""

from __future__ import annotations

PRIVACY_FIRST_TELEMETRY_VERIFICATION_ID = "sv9-14-cross-client-telemetry-privacy"
PRIVACY_FIRST_TELEMETRY_VERIFICATION_VERSION = "1.0.0"

__all__ = [
    "PRIVACY_FIRST_TELEMETRY_VERIFICATION_ID",
    "PRIVACY_FIRST_TELEMETRY_VERIFICATION_VERSION",
]
