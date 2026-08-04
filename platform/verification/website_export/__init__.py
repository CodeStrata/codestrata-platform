"""SV.8 Website-safe Engineering Intelligence export verification.

Not part of the Platform runtime distribution package.
"""

from __future__ import annotations

from verification.website_export.contract import (
    WEBSITE_EXPORT_VERIFICATION_ID,
    WEBSITE_EXPORT_VERIFICATION_VERSION,
)
from verification.website_export.runner import run_website_export_verification

__all__ = [
    "WEBSITE_EXPORT_VERIFICATION_ID",
    "WEBSITE_EXPORT_VERIFICATION_VERSION",
    "run_website_export_verification",
]
