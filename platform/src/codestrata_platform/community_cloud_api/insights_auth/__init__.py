"""Insights shared-password authentication (Slice 15.9).

Separate from Community Cloud client-credential authentication used for
ingestion. This package protects the internal Insights SPA and metric APIs.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights_auth.policy import (
    COMMUNITY_INSIGHTS_AUTH_POLICY_URN,
    InsightsAuthPolicy,
    default_insights_auth_policy,
    load_insights_auth_policy,
)
from codestrata_platform.community_cloud_api.insights_auth.service import (
    InsightsAuthService,
)

__all__ = [
    "COMMUNITY_INSIGHTS_AUTH_POLICY_URN",
    "InsightsAuthPolicy",
    "InsightsAuthService",
    "default_insights_auth_policy",
    "load_insights_auth_policy",
]
