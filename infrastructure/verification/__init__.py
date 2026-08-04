"""SV.9 Platform Deployment Foundation Verification.

Private infrastructure verification — not part of Platform/Engine runtime wheels.
"""

from __future__ import annotations

from infrastructure.verification.contract import (
    PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID,
    PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_VERSION,
)
from infrastructure.verification.runner import (
    run_platform_deployment_foundation_verification,
)

__all__ = [
    "PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID",
    "PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_VERSION",
    "run_platform_deployment_foundation_verification",
]
