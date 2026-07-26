"""Tests for Repository Knowledge Layer domain contracts (Phase 5.1)."""

from __future__ import annotations

import json

import pytest

from aimf.domain.knowledge import (
    KNOWLEDGE_CHUNK_SCHEMA_VERSION,
    KNOWLEDGE_DOCUMENT_SCHEMA_VERSION,
    VECTOR_RECORD_SCHEMA_VERSION,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeMetadata,
    KnowledgeSource,
    KnowledgeSourceType,
    KnowledgeTraceability,
    VectorRecord,
    build_chunk_id,
    build_document_id,
    content_hash,
    knowledge_chunk_payload,
    knowledge_document_payload,
)
from aimf.services.artifact_serialization import dumps_stable_json


def _trace(*, source_id: str = "src-1") -> KnowledgeTraceability:
    return KnowledgeTraceability(
        source=KnowledgeSource(
            source_type=KnowledgeSourceType.FINDING,
            repository_id="repo-1",
            scan_id="scan-1",
            finding_id="finding-1",
            rule_id="RULE-001",
        ),
        source_id=source_id,
        assessment_version="1.0.0",
    )


def test_stable_document_ids() -> None:
    left = KnowledgeDocument.create(
        source_type=KnowledgeSourceType.ARCHITECTURE,
        source_id="arch-summary-1",
        title="Architecture",
        content="layered services",
        traceability=_trace(source_id="arch-summary-1"),
        metadata=KnowledgeMetadata(repository_id="repo-1", language="java"),
    )
    right = KnowledgeDocument.create(
        source_type=KnowledgeSourceType.ARCHITECTURE,
        source_id="arch-summary-1",
        title="Architecture",
        content="layered services",
        traceability=_trace(source_id="arch-summary-1"),
        metadata=KnowledgeMetadata(repository_id="repo-1", language="java"),
    )
    assert left.document_id == right.document_id
    assert left.document_id.startswith("kd:")
    assert left.fingerprint == right.fingerprint
    assert left.schema_version == KNOWLEDGE_DOCUMENT_SCHEMA_VERSION

    expected = build_document_id(
        source_type="architecture",
        source_id="arch-summary-1",
        content_digest=content_hash("layered services"),
    )
    assert left.document_id == expected


def test_stable_chunk_ids() -> None:
    doc = KnowledgeDocument.create(
        source_type=KnowledgeSourceType.EVIDENCE,
        source_id="ev-1",
        title="Evidence",
        content="full document body",
        traceability=_trace(source_id="ev-1"),
    )
    left = KnowledgeChunk.create(
        document_id=doc.document_id,
        sequence=0,
        content="chunk body",
        traceability=_trace(source_id="ev-1"),
        token_count=2,
    )
    right = KnowledgeChunk.create(
        document_id=doc.document_id,
        sequence=0,
        content="chunk body",
        traceability=_trace(source_id="ev-1"),
        token_count=2,
    )
    assert left.chunk_id == right.chunk_id
    assert left.chunk_id.startswith("kc:")
    assert left.schema_version == KNOWLEDGE_CHUNK_SCHEMA_VERSION
    assert left.char_count == len("chunk body")
    assert (
        build_chunk_id(
            document_id=doc.document_id,
            sequence=0,
            content_digest=content_hash("chunk body"),
        )
        == left.chunk_id
    )


def test_metadata_serialization_byte_identical() -> None:
    meta = KnowledgeMetadata(
        tenant_id="t1",
        repository_id="repo-1",
        scan_id="scan-1",
        branch="main",
        commit_sha="abc123",
        language="python",
        framework="fastapi",
        source_type=KnowledgeSourceType.SECURITY,
        intelligence_pack="security.core",
        assessment_version="1.2.0",
        finding_id="f-1",
        rule_id="SEC-001",
        severity="high",
        confidence="high",
        file_path="src/app.py",
        symbol_name="main",
        content_hash="sha256:deadbeef",
        extra={"custom": "value"},
    )
    left = dumps_stable_json(meta.model_dump(mode="json"))
    right = dumps_stable_json(meta.model_dump(mode="json"))
    assert left == right
    assert json.loads(left)["extra"]["custom"] == "value"
    flat = meta.as_filter_dict()
    assert flat["tenant_id"] == "t1"
    assert flat["custom"] == "value"
    assert "extra" not in flat


def test_traceability_round_trip() -> None:
    trace = _trace()
    document = KnowledgeDocument.create(
        source_type=KnowledgeSourceType.REPORT_SECTION,
        source_id="report.security",
        title="Security",
        content="section body",
        traceability=trace,
    )
    payload = knowledge_document_payload(document)
    restored = KnowledgeDocument.model_validate(payload)
    assert restored.traceability.source.finding_id == "finding-1"
    assert restored.traceability.source.rule_id == "RULE-001"
    assert dumps_stable_json(payload) == dumps_stable_json(knowledge_document_payload(restored))


def test_chunk_payload_byte_identical() -> None:
    chunk = KnowledgeChunk.create(
        document_id="kd:abc",
        sequence=1,
        content="slice",
        traceability=_trace(),
        metadata=KnowledgeMetadata(scan_id="scan-1"),
    )
    left = dumps_stable_json(knowledge_chunk_payload(chunk))
    right = dumps_stable_json(knowledge_chunk_payload(chunk))
    assert left == right


def test_vector_record_validation_and_stable_id() -> None:
    left = VectorRecord.create(
        entity_id="kc:chunk-1",
        embedding=[1.0, 0.0, 0.0],
        metadata={"tenant_id": "t1", "repository_id": "r1"},
        text="hello",
    )
    right = VectorRecord.create(
        entity_id="kc:chunk-1",
        embedding=[1.0, 0.0, 0.0],
        metadata={"tenant_id": "t1", "repository_id": "r1"},
        text="hello",
    )
    assert left.record_id == right.record_id
    assert left.record_id.startswith("vr:")
    assert left.schema_version == VECTOR_RECORD_SCHEMA_VERSION
    assert left.metadata["namespace"] == "default"
    assert left.fingerprint == right.fingerprint

    with pytest.raises(ValueError, match="embedding must not be empty"):
        VectorRecord.create(entity_id="x", embedding=[])


def test_all_source_types_are_stable() -> None:
    values = {item.value for item in KnowledgeSourceType}
    assert values == {
        "repository_file",
        "architecture",
        "technical_debt",
        "dependency",
        "security",
        "test",
        "cloud",
        "ai_readiness",
        "performance",
        "finding",
        "evidence",
        "recommendation",
        "report_section",
    }
