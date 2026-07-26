"""AI enrichment package: narrative over deterministic findings/recommendations."""

from codestrata.ai.enrichment.artifacts import (
    AI_ENRICHMENT_FILENAME,
    AiEnrichmentArtifactWriteResult,
    try_write_ai_enrichment_artifact,
    write_ai_enrichment_artifact,
)
from codestrata.ai.enrichment.context import (
    DEFAULT_MAX_CONTEXT_CHARACTERS,
    AiEnrichmentBudgetError,
    AiEnrichmentContext,
    AiEnrichmentContextLimits,
    build_ai_enrichment_context,
)
from codestrata.ai.enrichment.prompt import (
    AiEnrichmentPromptBuilder,
    AiEnrichmentPromptBuildError,
    AiEnrichmentPromptOptions,
)
from codestrata.ai.enrichment.service import AiEnrichmentRunResult, AiEnrichmentService
from codestrata.ai.enrichment.validation import (
    AiEnrichmentValidationError,
    validate_ai_enrichment_result,
)

__all__ = [
    "AI_ENRICHMENT_FILENAME",
    "DEFAULT_MAX_CONTEXT_CHARACTERS",
    "AiEnrichmentArtifactWriteResult",
    "AiEnrichmentBudgetError",
    "AiEnrichmentContext",
    "AiEnrichmentContextLimits",
    "AiEnrichmentPromptBuildError",
    "AiEnrichmentPromptBuilder",
    "AiEnrichmentPromptOptions",
    "AiEnrichmentRunResult",
    "AiEnrichmentService",
    "AiEnrichmentValidationError",
    "build_ai_enrichment_context",
    "try_write_ai_enrichment_artifact",
    "validate_ai_enrichment_result",
    "write_ai_enrichment_artifact",
]
