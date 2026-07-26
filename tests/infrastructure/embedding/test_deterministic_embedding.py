"""Tests for DeterministicEmbeddingProvider (Phase 5.3)."""

from __future__ import annotations

import math

import pytest

from aimf.domain.knowledge.embedding import EmbeddingRequest
from aimf.infrastructure.embedding import DeterministicEmbeddingProvider


def test_deterministic_same_text_same_vector() -> None:
    provider = DeterministicEmbeddingProvider(dimension=32)
    left = provider.embed_text("hello world", request_id="a")
    right = provider.embed_text("hello world", request_id="b")
    assert left.embedding == right.embedding
    assert left.dimension == 32
    assert len(left.embedding) == 32


def test_embedding_is_l2_normalized() -> None:
    provider = DeterministicEmbeddingProvider(dimension=64)
    result = provider.embed_text("normalize me")
    norm = math.sqrt(sum(value * value for value in result.embedding))
    assert norm == pytest.approx(1.0, abs=1e-9)


def test_different_text_different_vector() -> None:
    provider = DeterministicEmbeddingProvider(dimension=32)
    left = provider.embed_text("alpha")
    right = provider.embed_text("beta")
    assert left.embedding != right.embedding


def test_batch_ordering_preserved() -> None:
    provider = DeterministicEmbeddingProvider(dimension=16)
    requests = [
        EmbeddingRequest(request_id="c", text="three"),
        EmbeddingRequest(request_id="a", text="one"),
        EmbeddingRequest(request_id="b", text="two"),
    ]
    batch = provider.embed_batch(requests)
    assert [item.request_id for item in batch.results] == ["c", "a", "b"]
    assert batch.failure_count == 0


def test_empty_and_oversized_inputs() -> None:
    provider = DeterministicEmbeddingProvider(dimension=8, max_input_characters=10)
    batch = provider.embed_batch(
        [
            EmbeddingRequest(request_id="empty", text="   "),
            EmbeddingRequest(request_id="big", text="x" * 20),
            EmbeddingRequest(request_id="ok", text="ok"),
        ]
    )
    assert batch.failed_request_ids == ("empty", "big")
    assert [item.request_id for item in batch.results] == ["ok"]
    assert {item.code for item in batch.diagnostics} == {"empty_input", "input_too_large"}


def test_model_identity_and_capabilities() -> None:
    provider = DeterministicEmbeddingProvider(dimension=384)
    identity = provider.model_identity()
    assert identity.provider_id == "deterministic"
    assert identity.dimension == 384
    caps = provider.capabilities()
    assert caps.is_deterministic is True
    assert caps.is_production_semantic is False
    assert provider.health().healthy is True


def test_embed_text_raises_on_invalid() -> None:
    provider = DeterministicEmbeddingProvider(max_input_characters=5)
    with pytest.raises(ValueError, match="exceeds"):
        provider.embed_text("too-long-input")
