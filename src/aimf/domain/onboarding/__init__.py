"""Domain package for repository onboarding (Phase 5.11)."""

from aimf.domain.onboarding.enums import OnboardingStatus
from aimf.domain.onboarding.errors import OnboardingError
from aimf.domain.onboarding.identifiers import (
    ONBOARDING_MANIFEST_FILENAME,
    ONBOARDING_SCHEMA_NAME,
    ONBOARDING_SCHEMA_VERSION,
)
from aimf.domain.onboarding.models import (
    OnboardingResult,
    OnboardingSummary,
    RepositoryOnboardingManifest,
)

__all__ = [
    "ONBOARDING_MANIFEST_FILENAME",
    "ONBOARDING_SCHEMA_NAME",
    "ONBOARDING_SCHEMA_VERSION",
    "OnboardingError",
    "OnboardingResult",
    "OnboardingStatus",
    "OnboardingSummary",
    "RepositoryOnboardingManifest",
]
