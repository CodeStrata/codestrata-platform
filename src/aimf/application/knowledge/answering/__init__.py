"""Grounded repository answering (Phase 5.6)."""

from aimf.application.knowledge.answering.deterministic import (
    DeterministicExtractiveAnswerProvider,
    create_deterministic_extractive_answer_provider,
)
from aimf.application.knowledge.answering.engine import (
    ANSWER_ARTIFACT_FILENAME,
    GroundedAnswerEngine,
    write_grounded_answer_artifact,
)
from aimf.application.knowledge.answering.factory import (
    RESERVED_UNIMPLEMENTED_PROVIDERS,
    AnswerProviderConfigurationError,
    create_answer_provider,
)
from aimf.application.knowledge.answering.protocol import (
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
