"""In-memory and filesystem artifact content storage."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from codestrata_platform.domain.artifact.value_objects import ArtifactReference
from codestrata_platform.domain.errors import InvalidValueError

_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "application/json",
        "text/html",
        "text/plain",
        "application/octet-stream",
    }
)


class InMemoryArtifactStorage:
    """Temporary content store for tests and local memory mode."""

    def __init__(self) -> None:
        self._items: dict[str, bytes] = {}

    def put(self, *, key: str, content: bytes, content_type: str) -> ArtifactReference:
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise InvalidValueError(
                f"Unsupported content type: {content_type}",
                reason_code="unsupported_content_type",
            )
        reference = ArtifactReference(key)
        self._items[reference.value] = content
        return reference

    def get(self, reference: ArtifactReference) -> bytes:
        try:
            return self._items[reference.value]
        except KeyError as error:
            raise FileNotFoundError(f"Artifact content not found: {reference.value}") from error

    def exists(self, reference: ArtifactReference) -> bool:
        return reference.value in self._items

    def delete(self, reference: ArtifactReference) -> None:
        self._items.pop(reference.value, None)


class FileSystemArtifactStorage:
    """Filesystem-backed artifact store with path traversal protection."""

    def __init__(self, root: Path) -> None:
        self._root = root.expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def put(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
        expected_checksum: str | None = None,
    ) -> ArtifactReference:
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise InvalidValueError(
                f"Unsupported content type: {content_type}",
                reason_code="unsupported_content_type",
            )
        if expected_checksum is not None:
            digest = hashlib.sha256(content).hexdigest()
            if digest != expected_checksum.strip().lower():
                raise InvalidValueError(
                    "Stored content checksum does not match expected value",
                    reason_code="checksum_mismatch",
                )
        reference = ArtifactReference(key)
        target = self._resolve(reference.value)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=".upload-", dir=str(target.parent))
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, target)
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        # Verify on disk after atomic replace.
        written = target.read_bytes()
        if hashlib.sha256(written).hexdigest() != hashlib.sha256(content).hexdigest():
            target.unlink(missing_ok=True)
            raise InvalidValueError(
                "Filesystem write verification failed",
                reason_code="checksum_mismatch",
            )
        return reference

    def get(self, reference: ArtifactReference) -> bytes:
        path = self._resolve(reference.value)
        if not path.is_file():
            raise FileNotFoundError(f"Artifact content not found: {reference.value}")
        return path.read_bytes()

    def exists(self, reference: ArtifactReference) -> bool:
        return self._resolve(reference.value).is_file()

    def delete(self, reference: ArtifactReference) -> None:
        path = self._resolve(reference.value)
        if path.is_file():
            path.unlink()

    def _resolve(self, key: str) -> Path:
        compact = key.strip().lstrip("/")
        if not compact or ".." in compact.replace("\\", "/").split("/"):
            raise InvalidValueError(
                "Invalid artifact storage key",
                reason_code="path_traversal",
            )
        candidate = (self._root / compact).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError as error:
            raise InvalidValueError(
                "Artifact storage key escapes configured root",
                reason_code="path_traversal",
            ) from error
        return candidate
