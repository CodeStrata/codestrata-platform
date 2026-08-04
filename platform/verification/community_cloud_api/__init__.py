"""SV.7 Community Cloud API end-to-end verification (Platform-only).

Not part of the Platform runtime distribution package.
"""

from __future__ import annotations

from verification.community_cloud_api.contract import (
    COMMUNITY_CLOUD_API_VERIFICATION_ID,
    COMMUNITY_CLOUD_API_VERIFICATION_VERSION,
)
from verification.community_cloud_api.runner import (
    run_community_cloud_api_verification,
)

__all__ = [
    "COMMUNITY_CLOUD_API_VERIFICATION_ID",
    "COMMUNITY_CLOUD_API_VERIFICATION_VERSION",
    "run_community_cloud_api_verification",
]
