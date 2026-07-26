"""Register Platform embedding and answer providers on the Engine registry."""

from __future__ import annotations

from typing import Any


def register_rag_ai_providers(registry: Any) -> None:
    """Populate embedding/answer factories used by Platform RAG."""

    from codestrata_platform.rag.application.answering.bedrock import (
        create_bedrock_answer_provider,
    )
    from codestrata_platform.rag.application.answering.deterministic import (
        create_deterministic_extractive_answer_provider,
    )
    from codestrata_platform.rag.application.answering.openai_provider import (
        create_openai_answer_provider,
    )
    from codestrata_platform.rag.embedding.bedrock import create_bedrock_embedding_provider
    from codestrata_platform.rag.embedding.deterministic import (
        create_deterministic_embedding_provider,
    )
    from codestrata_platform.rag.embedding.openai_provider import (
        create_openai_embedding_provider,
    )

    registry.register_embedding("deterministic", create_deterministic_embedding_provider)
    registry.register_embedding("bedrock", create_bedrock_embedding_provider)
    registry.register_embedding("openai", create_openai_embedding_provider)
    registry.register_answer(
        "deterministic_extractive",
        create_deterministic_extractive_answer_provider,
    )
    registry.register_answer("bedrock", create_bedrock_answer_provider)
    registry.register_answer("openai", create_openai_answer_provider)
