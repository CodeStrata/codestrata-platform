"""Retrieval document and source reference value objects."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.retrieval.identifiers import RetrievalDocumentId, RetrievalIndexId
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType

_MAX_TITLE = 256
_MAX_SUMMARY = 4000
_MAX_METADATA = 40
_SECRET_MARKERS = ("password", "secret", "token", "api_key", "private_key", "credential")
_CODE_MARKERS = ("```", "def ", "class ", "#!/", "package ", "import ")


def _bounded(value: str, *, field_name: str, max_length: int) -> str:
    compact = value.strip()
    if not compact:
        raise InvalidValueError(
            f"{field_name} must be non-blank",
            reason_code=f"empty_{field_name}",
        )
    if len(compact) > max_length:
        raise InvalidValueError(
            f"{field_name} exceeds maximum length",
            reason_code=f"{field_name}_too_long",
        )
    return compact


def sanitize_retrieval_text(text: str, *, max_length: int = 8000) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if any(marker in compact.lower() for marker in _SECRET_MARKERS):
        raise InvalidValueError(
            "Retrieval text contains prohibited secret markers",
            reason_code="secret_bearing_retrieval_text",
        )
    if any(marker in compact for marker in _CODE_MARKERS) and "finding" not in compact.lower()[:40]:
        # Allow short mentions; reject fenced/code-like payloads.
        if "```" in compact or compact.startswith("#!/"):
            raise InvalidValueError(
                "Raw source code is not allowed in retrieval content",
                reason_code="raw_source_code_prohibited",
            )
    if len(compact) > max_length:
        compact = compact[:max_length].rstrip()
    return compact


@dataclass(frozen=True, slots=True)
class RetrievalSourceReference:
    source_kind: str
    source_id: str
    snapshot_id: str | None = None
    graph_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_kind",
            _bounded(self.source_kind, field_name="source_kind", max_length=64),
        )
        object.__setattr__(
            self,
            "source_id",
            _bounded(self.source_id, field_name="source_id", max_length=160),
        )


@dataclass(frozen=True, slots=True)
class RetrievalDocument:
    document_id: RetrievalDocumentId
    index_id: RetrievalIndexId
    content_type: RetrievalContentType
    canonical_type: str
    canonical_id: str
    title: str
    summary: str
    structured_content: Mapping[str, str] = field(default_factory=dict)
    source_references: tuple[RetrievalSourceReference, ...] = ()
    graph_node_ids: tuple[str, ...] = ()
    graph_edge_ids: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
    checksum: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_type",
            _bounded(self.canonical_type, field_name="canonical_type", max_length=64),
        )
        object.__setattr__(
            self,
            "canonical_id",
            _bounded(self.canonical_id, field_name="canonical_id", max_length=160),
        )
        object.__setattr__(
            self,
            "title",
            _bounded(self.title, field_name="title", max_length=_MAX_TITLE),
        )
        object.__setattr__(
            self,
            "summary",
            sanitize_retrieval_text(self.summary, max_length=_MAX_SUMMARY),
        )
        if not self.source_references:
            raise InvalidValueError(
                "Retrieval documents require source references",
                reason_code="missing_source_references",
            )
        structured = {
            str(key).strip(): sanitize_retrieval_text(str(value), max_length=2000)
            for key, value in dict(self.structured_content).items()
            if str(key).strip() and str(value).strip()
        }
        if len(structured) > _MAX_METADATA:
            raise InvalidValueError(
                "structured_content exceeds maximum keys",
                reason_code="structured_content_too_large",
            )
        metadata = {
            str(key).strip(): str(value).strip()[:256]
            for key, value in dict(self.metadata).items()
            if str(key).strip() and str(value).strip()
        }
        if len(metadata) > _MAX_METADATA:
            raise InvalidValueError(
                "metadata exceeds maximum keys",
                reason_code="metadata_too_large",
            )
        object.__setattr__(self, "structured_content", dict(sorted(structured.items())))
        object.__setattr__(self, "metadata", dict(sorted(metadata.items())))
        digest = self.checksum.strip().lower() or self.compute_checksum()
        object.__setattr__(self, "checksum", digest)

    def compute_checksum(self) -> str:
        payload = "|".join(
            [
                self.content_type.value,
                self.canonical_type,
                self.canonical_id,
                self.title,
                self.summary,
                repr(sorted(self.structured_content.items())),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
