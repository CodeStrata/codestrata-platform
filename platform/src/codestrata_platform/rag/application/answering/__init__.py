"""Grounded repository answering (Phase 5.6)."""

from codestrata_platform.rag.application.answering.deterministic import (
    DeterministicExtractiveAnswerProvider,
    create_deterministic_extractive_answer_provider,
)
from codestrata_platform.rag.application.answering.engine import (
    ANSWER_ARTIFACT_FILENAME,
    GroundedAnswerEngine,
    write_grounded_answer_artifact,
)
from codestrata_platform.rag.application.answering.factory import (
    RESERVED_UNIMPLEMENTED_PROVIDERS,
    AnswerProviderConfigurationError,
    create_answer_provider,
)
from codestrata_platform.rag.application.answering.protocol import (
    AnswerProvider,
    AnswerProviderCapabilities,
    AnswerProviderDiagnostic,
    AnswerProviderHealth,
    AnswerProviderRequest,
    AnswerProviderResult,
    AnswerProviderUsage,
)

__all__ = [
    "ANSWER_ARTIFACT_FILENAME",
    "AnswerProvider",
    "AnswerProviderCapabilities",
    "AnswerProviderConfigurationError",
    "AnswerProviderDiagnostic",
    "AnswerProviderHealth",
    "AnswerProviderRequest",
    "AnswerProviderResult",
    "AnswerProviderUsage",
    "DeterministicExtractiveAnswerProvider",
    "GroundedAnswerEngine",
    "RESERVED_UNIMPLEMENTED_PROVIDERS",
    "create_answer_provider",
    "create_deterministic_extractive_answer_provider",
    "write_grounded_answer_artifact",
]
