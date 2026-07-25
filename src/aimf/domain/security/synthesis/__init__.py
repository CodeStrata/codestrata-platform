"""Security synthesis domain package (Phase 4.5.5)."""

from aimf.domain.security.synthesis.enums import (
    SecurityConclusionAudience,
    SecurityConclusionKind,
    SecurityRecommendationKind,
    SecuritySynthesisStatus,
    SecurityThemeKind,
    SecurityThemeScope,
)
from aimf.domain.security.synthesis.identifiers import (
    SYNTHESIS_VERSION,
    build_concentration_fact_id,
    build_conclusion_id,
    build_recommendation_id,
    build_theme_id,
)
from aimf.domain.security.synthesis.models import (
    SecurityConcentrationFact,
    SecurityConclusion,
    SecurityRecommendation,
    SecuritySynthesisResult,
    SecurityTheme,
)

__all__ = [
    "SYNTHESIS_VERSION",
    "SecurityConcentrationFact",
    "SecurityConclusion",
    "SecurityConclusionAudience",
    "SecurityConclusionKind",
    "SecurityRecommendation",
    "SecurityRecommendationKind",
    "SecuritySynthesisResult",
    "SecuritySynthesisStatus",
    "SecurityTheme",
    "SecurityThemeKind",
    "SecurityThemeScope",
    "build_concentration_fact_id",
    "build_conclusion_id",
    "build_recommendation_id",
    "build_theme_id",
]
