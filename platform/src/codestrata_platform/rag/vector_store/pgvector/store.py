"""PostgreSQL + pgvector VectorStore provider (Phase 5.4)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from codestrata_platform.rag.domain.vector import (
    IndexScope,
    VectorFilter,
    VectorQuery,
    VectorRecord,
    VectorSearchResult,
)
from codestrata_platform.rag.vector_store.pgvector.capabilities import (
    PgVectorCapabilities,
    PgVectorStoreHealth,
    build_pgvector_capabilities,
    build_pgvector_health,
)
from codestrata_platform.rag.vector_store.pgvector.connection import (
    connect,
    postgres_server_version,
    verify_vector_extension,
)
from codestrata_platform.rag.vector_store.pgvector.migrations import apply_migrations
from codestrata_platform.rag.vector_store.pgvector.schema import (
    SCHEMA_VERSION,
    quoted_ident,
)
from codestrata.security.database_url import sanitize_exception_message

# Columns projected from VectorRecord.metadata for filtering / isolation.
_METADATA_COLUMNS = (
    "document_id",
    "chunk_id",
    "tenant_id",
    "repository_id",
    "scan_id",
    "branch",
    "commit_sha",
    "source_type",
    "intelligence_pack",
    "assessment_version",
    "finding_id",
    "rule_id",
    "severity",
    "confidence",
    "file_path",
    "symbol_name",
    "content_hash",
)


def _optional_str(metadata: Mapping[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(metadata: Mapping[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = metadata.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value.strip())
    return None


def _json_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _embedding_to_tuple(embedding: Any) -> tuple[float, ...]:
    """Normalize a pgvector ``Vector`` / sequence into a float tuple."""

    if embedding is None:
        raise ValueError("embedding is required")
    if hasattr(embedding, "to_list"):
        values = embedding.to_list()
    elif hasattr(embedding, "tolist"):
        values = embedding.tolist()
    elif isinstance(embedding, (list, tuple)):
        values = embedding
    else:
        values = list(embedding)
    return tuple(float(v) for v in values)


class PgVectorStore:
    """Production dense vector store backed by PostgreSQL + pgvector.

    Implements cosine similarity search with metadata filters, tenant /
    repository / scan isolation, transaction-safe upserts, and deterministic
    tie-breaking (score descending, then ``record_id`` ascending).
    """

    def __init__(
        self,
        *,
        connection_string: str,
        schema: str = "codestrata",
        dimension: int = 384,
        hnsw: bool = True,
        migrate: bool = True,
        connect_timeout_seconds: int = 10,
        connection: Any | None = None,
    ) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self._schema_name = schema.strip().lower()
        self._schema = quoted_ident(self._schema_name)
        self._dimension = dimension
        self._hnsw = hnsw
        self._owns_connection = connection is None
        self._connection = connection or connect(
            connection_string,
            connect_timeout_seconds=connect_timeout_seconds,
        )
        if migrate:
            apply_migrations(
                self._connection,
                schema=self._schema_name,
                dimension=dimension,
                hnsw=hnsw,
            )
        # Fail fast when the extension is unavailable after migrate attempts.
        verify_vector_extension(self._connection)

    @property
    def schema(self) -> str:
        return self._schema_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def connection(self) -> Any:
        """Underlying DB connection (for health / verification helpers)."""

        return self._connection

    def close(self) -> None:
        if self._owns_connection and self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> PgVectorStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        try:
            with self._connection.cursor() as cur:
                for record in records:
                    if len(record.embedding) != self._dimension:
                        raise ValueError(
                            f"embedding dimension {len(record.embedding)} does not "
                            f"match store dimension {self._dimension}"
                        )
                    self._upsert_document_stub(cur, record)
                    self._upsert_chunk_stub(cur, record)
                    self._upsert_vector(cur, record)
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def search(self, query: VectorQuery) -> Sequence[VectorSearchResult]:
        if len(query.embedding) != self._dimension:
            raise ValueError(
                f"query embedding dimension {len(query.embedding)} does not "
                f"match store dimension {self._dimension}"
            )
        where_sql, params = self._filter_clause(query.filter)
        sql = f"""
            SELECT
                record_id,
                embedding,
                document_id,
                chunk_id,
                entity_id,
                namespace,
                tenant_id,
                repository_id,
                scan_id,
                branch,
                commit_sha,
                source_type,
                intelligence_pack,
                assessment_version,
                finding_id,
                rule_id,
                severity,
                confidence,
                file_path,
                symbol_name,
                content_hash,
                sequence,
                fingerprint,
                text,
                metadata,
                (1.0 - (embedding <=> %s::vector)) AS score
            FROM {self._schema}.knowledge_vectors
            {where_sql}
            ORDER BY (embedding <=> %s::vector) ASC, record_id ASC
            LIMIT %s
        """
        query_params: list[Any] = [
            list(query.embedding),
            *params,
            list(query.embedding),
            query.top_k,
        ]
        with self._connection.cursor() as cur:
            cur.execute(sql, query_params)
            rows = cur.fetchall()
        return tuple(self._row_to_search_result(row) for row in rows)

    def fetch_filtered(
        self,
        vector_filter: VectorFilter | None = None,
        *,
        limit: int,
        require_text: bool = True,
    ) -> Sequence[VectorRecord]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        where_sql, params = self._filter_clause(vector_filter)
        text_clause = "text IS NOT NULL AND BTRIM(text) <> ''" if require_text else "TRUE"
        if where_sql:
            where_sql = f"{where_sql} AND {text_clause}"
        else:
            where_sql = f"WHERE {text_clause}"
        sql = f"""
            SELECT
                record_id,
                embedding,
                document_id,
                chunk_id,
                entity_id,
                namespace,
                tenant_id,
                repository_id,
                scan_id,
                branch,
                commit_sha,
                source_type,
                intelligence_pack,
                assessment_version,
                finding_id,
                rule_id,
                severity,
                confidence,
                file_path,
                symbol_name,
                content_hash,
                sequence,
                fingerprint,
                text,
                metadata,
                0.0 AS score
            FROM {self._schema}.knowledge_vectors
            {where_sql}
            ORDER BY record_id ASC
            LIMIT %s
        """
        with self._connection.cursor() as cur:
            cur.execute(sql, [*params, limit])
            rows = cur.fetchall()
        return tuple(self._row_to_search_result(row).record for row in rows)

    def delete_scope(self, scope: IndexScope) -> int:
        clauses = ["namespace = %s"]
        params: list[Any] = [scope.namespace]
        if scope.tenant_id is not None:
            clauses.append("tenant_id = %s")
            params.append(scope.tenant_id)
        if scope.repository_id is not None:
            clauses.append("repository_id = %s")
            params.append(scope.repository_id)
        if scope.scan_id is not None:
            clauses.append("scan_id = %s")
            params.append(scope.scan_id)
        where = " AND ".join(clauses)
        try:
            with self._connection.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self._schema}.knowledge_vectors WHERE {where}",
                    params,
                )
                deleted = int(cur.rowcount or 0)
            self._connection.commit()
            return deleted
        except Exception:
            self._connection.rollback()
            raise

    def delete_ids(self, record_ids: Sequence[str]) -> int:
        ids = [str(item) for item in record_ids if str(item).strip()]
        if not ids:
            return 0
        try:
            with self._connection.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self._schema}.knowledge_vectors "
                    f"WHERE record_id = ANY(%s)",
                    (ids,),
                )
                deleted = int(cur.rowcount or 0)
            self._connection.commit()
            return deleted
        except Exception:
            self._connection.rollback()
            raise

    def health(self) -> PgVectorStoreHealth:
        try:
            with self._connection.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
                cur.execute(
                    f"SELECT COUNT(*) FROM {self._schema}.knowledge_vectors"
                )
                count_row = cur.fetchone()
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_indexes
                        WHERE schemaname = %s
                          AND indexname = 'knowledge_vectors_embedding_hnsw_idx'
                    )
                    """,
                    (self._schema_name,),
                )
                hnsw_row = cur.fetchone()
            extension_version = verify_vector_extension(self._connection)
            server_version = postgres_server_version(self._connection)
            return build_pgvector_health(
                healthy=True,
                message="pgvector store ready",
                detail={
                    "connectivity": True,
                    "persistent": True,
                    "record_count": int(count_row[0]) if count_row else 0,
                    "schema": self._schema_name,
                    "schema_version": SCHEMA_VERSION,
                    "dimension": self._dimension,
                    "postgres_version": server_version,
                    "pgvector_extension": True,
                    "pgvector_version": extension_version,
                    "extension_vector": True,
                    "hnsw_index": bool(hnsw_row and hnsw_row[0]),
                },
            )
        except Exception as exc:  # noqa: BLE001 - health must never raise
            message = sanitize_exception_message(str(exc))
            return build_pgvector_health(
                healthy=False,
                message=f"pgvector store unhealthy: {message}",
                detail={
                    "connectivity": False,
                    "persistent": True,
                    "schema": self._schema_name,
                    "dimension": self._dimension,
                    "schema_version": SCHEMA_VERSION,
                },
            )

    def capabilities(self) -> PgVectorCapabilities:
        return build_pgvector_capabilities(
            dimension=self._dimension,
            schema=self._schema_name,
            hnsw=self._hnsw,
        )

    def count(self) -> int:
        with self._connection.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self._schema}.knowledge_vectors")
            row = cur.fetchone()
        return int(row[0]) if row else 0

    def __len__(self) -> int:
        return self.count()

    def _upsert_document_stub(self, cur: Any, record: VectorRecord) -> None:
        document_id = _optional_str(record.metadata, "document_id")
        if document_id is None:
            return
        cur.execute(
            f"""
            INSERT INTO {self._schema}.knowledge_documents (
                document_id, tenant_id, repository_id, scan_id, fingerprint, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (document_id) DO UPDATE SET
                tenant_id = EXCLUDED.tenant_id,
                repository_id = EXCLUDED.repository_id,
                scan_id = EXCLUDED.scan_id,
                fingerprint = EXCLUDED.fingerprint,
                metadata = EXCLUDED.metadata
            """,
            (
                document_id,
                _optional_str(record.metadata, "tenant_id"),
                _optional_str(record.metadata, "repository_id"),
                _optional_str(record.metadata, "scan_id"),
                _optional_str(record.metadata, "chunk_fingerprint") or record.fingerprint,
                _json_dumps({"source": "vector_upsert"}),
            ),
        )

    def _upsert_chunk_stub(self, cur: Any, record: VectorRecord) -> None:
        chunk_id = _optional_str(record.metadata, "chunk_id")
        document_id = _optional_str(record.metadata, "document_id")
        if chunk_id is None or document_id is None:
            return
        sequence = _optional_int(record.metadata, "chunk_sequence", "sequence") or 0
        cur.execute(
            f"""
            INSERT INTO {self._schema}.knowledge_chunks (
                chunk_id, document_id, sequence, fingerprint,
                tenant_id, repository_id, scan_id, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (chunk_id) DO UPDATE SET
                document_id = EXCLUDED.document_id,
                sequence = EXCLUDED.sequence,
                fingerprint = EXCLUDED.fingerprint,
                tenant_id = EXCLUDED.tenant_id,
                repository_id = EXCLUDED.repository_id,
                scan_id = EXCLUDED.scan_id,
                metadata = EXCLUDED.metadata
            """,
            (
                chunk_id,
                document_id,
                sequence,
                _optional_str(record.metadata, "chunk_fingerprint") or record.fingerprint,
                _optional_str(record.metadata, "tenant_id"),
                _optional_str(record.metadata, "repository_id"),
                _optional_str(record.metadata, "scan_id"),
                _json_dumps({"source": "vector_upsert"}),
            ),
        )

    def _upsert_vector(self, cur: Any, record: VectorRecord) -> None:
        meta = record.metadata
        sequence = _optional_int(meta, "chunk_sequence", "sequence")
        cur.execute(
            f"""
            INSERT INTO {self._schema}.knowledge_vectors (
                record_id, embedding, document_id, chunk_id, entity_id, namespace,
                tenant_id, repository_id, scan_id, branch, commit_sha, source_type,
                intelligence_pack, assessment_version, finding_id, rule_id,
                severity, confidence, file_path, symbol_name, content_hash,
                sequence, fingerprint, text, metadata
            ) VALUES (
                %s, %s::vector, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s::jsonb
            )
            ON CONFLICT (record_id) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                document_id = EXCLUDED.document_id,
                chunk_id = EXCLUDED.chunk_id,
                entity_id = EXCLUDED.entity_id,
                namespace = EXCLUDED.namespace,
                tenant_id = EXCLUDED.tenant_id,
                repository_id = EXCLUDED.repository_id,
                scan_id = EXCLUDED.scan_id,
                branch = EXCLUDED.branch,
                commit_sha = EXCLUDED.commit_sha,
                source_type = EXCLUDED.source_type,
                intelligence_pack = EXCLUDED.intelligence_pack,
                assessment_version = EXCLUDED.assessment_version,
                finding_id = EXCLUDED.finding_id,
                rule_id = EXCLUDED.rule_id,
                severity = EXCLUDED.severity,
                confidence = EXCLUDED.confidence,
                file_path = EXCLUDED.file_path,
                symbol_name = EXCLUDED.symbol_name,
                content_hash = EXCLUDED.content_hash,
                sequence = EXCLUDED.sequence,
                fingerprint = EXCLUDED.fingerprint,
                text = EXCLUDED.text,
                metadata = EXCLUDED.metadata
            """,
            (
                record.record_id,
                list(record.embedding),
                _optional_str(meta, "document_id"),
                _optional_str(meta, "chunk_id"),
                record.entity_id,
                record.namespace,
                _optional_str(meta, "tenant_id"),
                _optional_str(meta, "repository_id"),
                _optional_str(meta, "scan_id"),
                _optional_str(meta, "branch"),
                _optional_str(meta, "commit_sha"),
                _optional_str(meta, "source_type"),
                _optional_str(meta, "intelligence_pack"),
                _optional_str(meta, "assessment_version"),
                _optional_str(meta, "finding_id"),
                _optional_str(meta, "rule_id"),
                _optional_str(meta, "severity"),
                _optional_str(meta, "confidence"),
                _optional_str(meta, "file_path"),
                _optional_str(meta, "symbol_name"),
                _optional_str(meta, "content_hash"),
                sequence,
                record.fingerprint,
                record.text,
                _json_dumps(meta),
            ),
        )

    def _filter_clause(
        self, vector_filter: VectorFilter | None
    ) -> tuple[str, list[Any]]:
        if vector_filter is None:
            return "", []
        clauses: list[str] = []
        params: list[Any] = []
        if vector_filter.tenant_id is not None:
            clauses.append("tenant_id = %s")
            params.append(vector_filter.tenant_id)
        if vector_filter.repository_id is not None:
            clauses.append("repository_id = %s")
            params.append(vector_filter.repository_id)
        if vector_filter.scan_id is not None:
            clauses.append("scan_id = %s")
            params.append(vector_filter.scan_id)
        for key, expected in sorted(vector_filter.equals.items()):
            if key in _METADATA_COLUMNS or key == "namespace":
                clauses.append(f"{key} = %s")
                params.append(expected)
            elif expected is None:
                clauses.append("(metadata ->> %s) IS NULL")
                params.append(key)
            else:
                clauses.append("(metadata ->> %s) = %s")
                params.append(key)
                params.append(expected if isinstance(expected, str) else str(expected))
        if not clauses:
            return "", []
        return "WHERE " + " AND ".join(clauses), params

    def _row_to_search_result(self, row: Sequence[Any]) -> VectorSearchResult:
        (
            record_id,
            embedding,
            document_id,
            chunk_id,
            entity_id,
            namespace,
            tenant_id,
            repository_id,
            scan_id,
            branch,
            commit_sha,
            source_type,
            intelligence_pack,
            assessment_version,
            finding_id,
            rule_id,
            severity,
            confidence,
            file_path,
            symbol_name,
            content_hash,
            sequence,
            fingerprint,
            text,
            metadata,
            score,
        ) = row
        meta: dict[str, Any]
        if isinstance(metadata, Mapping):
            meta = dict(metadata)
        elif isinstance(metadata, str):
            meta = json.loads(metadata)
        else:
            meta = {}
        # Ensure projected columns remain available even if JSON was sparse.
        for key, value in (
            ("document_id", document_id),
            ("chunk_id", chunk_id),
            ("tenant_id", tenant_id),
            ("repository_id", repository_id),
            ("scan_id", scan_id),
            ("branch", branch),
            ("commit_sha", commit_sha),
            ("source_type", source_type),
            ("intelligence_pack", intelligence_pack),
            ("assessment_version", assessment_version),
            ("finding_id", finding_id),
            ("rule_id", rule_id),
            ("severity", severity),
            ("confidence", confidence),
            ("file_path", file_path),
            ("symbol_name", symbol_name),
            ("content_hash", content_hash),
            ("namespace", namespace),
        ):
            if value is not None and key not in meta:
                meta[key] = value
        if sequence is not None and "chunk_sequence" not in meta:
            meta["chunk_sequence"] = sequence
        vector = _embedding_to_tuple(embedding)
        record = VectorRecord(
            record_id=str(record_id),
            namespace=str(namespace),
            entity_id=str(entity_id),
            embedding=vector,
            metadata=meta,
            text=text,
            fingerprint=str(fingerprint),
        )
        return VectorSearchResult(
            record_id=str(record_id),
            score=float(score),
            record=record,
        )


def create_pgvector_store(
    *,
    connection_string: str,
    schema: str = "codestrata",
    dimension: int = 384,
    hnsw: bool = True,
    migrate: bool = True,
    connect_timeout_seconds: int = 10,
) -> PgVectorStore:
    """Factory for the PostgreSQL + pgvector provider."""

    return PgVectorStore(
        connection_string=connection_string,
        schema=schema,
        dimension=dimension,
        hnsw=hnsw,
        migrate=migrate,
        connect_timeout_seconds=connect_timeout_seconds,
    )
