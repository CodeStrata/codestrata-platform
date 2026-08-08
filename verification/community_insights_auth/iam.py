"""IAM boundary checks."""

from verification.community_insights_auth.infrastructure_boundary import (
    check_infrastructure_boundary,
)

check_iam = check_infrastructure_boundary

__all__ = ["check_iam"]
