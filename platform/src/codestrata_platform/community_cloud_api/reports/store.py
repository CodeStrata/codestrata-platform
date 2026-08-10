"""Report artifact storage ports — private S3 or in-memory test adapter."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from codestrata_platform.community_cloud_api.reports.policy import (
    PRESIGN_TTL_SECONDS,
)


@runtime_checkable
class ReportArtifactStore(Protocol):
    def put_bytes(self, key: str, body: bytes, *, content_type: str) -> None: ...

    def get_bytes(self, key: str) -> bytes | None: ...

    def delete_key(self, key: str) -> None: ...

    def delete_prefix(self, prefix: str) -> None: ...

    def list_keys(self, prefix: str) -> list[str]: ...

    def put_json(self, key: str, payload: dict[str, Any]) -> None: ...

    def get_json(self, key: str) -> dict[str, Any] | None: ...

    def create_presigned_put(
        self,
        key: str,
        *,
        content_type: str,
        expires_in: int = PRESIGN_TTL_SECONDS,
    ) -> str: ...


@dataclass
class InMemoryReportArtifactStore:
    """Deterministic in-memory store for unit/verification tests."""

    objects: dict[str, bytes] = field(default_factory=dict)
    content_types: dict[str, str] = field(default_factory=dict)
    presign_base: str = "https://report-artifacts.example.invalid/presign"

    def put_bytes(self, key: str, body: bytes, *, content_type: str) -> None:
        self.objects[key] = body
        self.content_types[key] = content_type

    def get_bytes(self, key: str) -> bytes | None:
        return self.objects.get(key)

    def delete_key(self, key: str) -> None:
        self.objects.pop(key, None)
        self.content_types.pop(key, None)

    def delete_prefix(self, prefix: str) -> None:
        for key in list(self.objects):
            if key.startswith(prefix):
                self.delete_key(key)

    def list_keys(self, prefix: str) -> list[str]:
        return sorted(k for k in self.objects if k.startswith(prefix))

    def put_json(self, key: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.put_bytes(key, body, content_type="application/json")

    def get_json(self, key: str) -> dict[str, Any] | None:
        raw = self.get_bytes(key)
        if raw is None:
            return None
        return json.loads(raw.decode("utf-8"))

    def create_presigned_put(
        self,
        key: str,
        *,
        content_type: str,
        expires_in: int = PRESIGN_TTL_SECONDS,
    ) -> str:
        _ = (content_type, expires_in)
        # Test-only URL — never a public product URL and never returned as share link.
        return f"{self.presign_base}/{key}?exp={int(time.time()) + expires_in}"


class S3ReportArtifactStore:
    """Private S3-backed report artifact store."""

    def __init__(
        self,
        *,
        bucket_name: str,
        region_name: str | None = None,
        client: Any | None = None,
    ) -> None:
        import boto3
        from botocore.config import Config

        self._bucket = bucket_name
        self._client = client or boto3.client(
            "s3",
            region_name=region_name,
            config=Config(s3={"addressing_style": "virtual"}),
        )

    def put_bytes(self, key: str, body: bytes, *, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )

    def get_bytes(self, key: str) -> bytes | None:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except Exception as exc:  # noqa: BLE001
            code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "404", "NotFound"}:
                return None
            # botocore ClientError 404
            if "NoSuchKey" in type(exc).__name__ or "404" in str(exc):
                return None
            raise
        return response["Body"].read()

    def delete_key(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def delete_prefix(self, prefix: str) -> None:
        continuation: str | None = None
        while True:
            kwargs: dict[str, Any] = {
                "Bucket": self._bucket,
                "Prefix": prefix,
                "MaxKeys": 100,
            }
            if continuation:
                kwargs["ContinuationToken"] = continuation
            page = self._client.list_objects_v2(**kwargs)
            contents = page.get("Contents") or []
            for item in contents:
                key = item.get("Key")
                if key:
                    self.delete_key(key)
            if not page.get("IsTruncated"):
                break
            continuation = page.get("NextContinuationToken")

    def list_keys(self, prefix: str) -> list[str]:
        out: list[str] = []
        continuation: str | None = None
        while True:
            kwargs: dict[str, Any] = {
                "Bucket": self._bucket,
                "Prefix": prefix,
                "MaxKeys": 100,
            }
            if continuation:
                kwargs["ContinuationToken"] = continuation
            page = self._client.list_objects_v2(**kwargs)
            for item in page.get("Contents") or []:
                key = item.get("Key")
                if key:
                    out.append(key)
            if not page.get("IsTruncated"):
                break
            continuation = page.get("NextContinuationToken")
        return sorted(out)

    def put_json(self, key: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.put_bytes(key, body, content_type="application/json")

    def get_json(self, key: str) -> dict[str, Any] | None:
        raw = self.get_bytes(key)
        if raw is None:
            return None
        return json.loads(raw.decode("utf-8"))

    def create_presigned_put(
        self,
        key: str,
        *,
        content_type: str,
        expires_in: int = PRESIGN_TTL_SECONDS,
    ) -> str:
        return self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )


__all__ = [
    "InMemoryReportArtifactStore",
    "ReportArtifactStore",
    "S3ReportArtifactStore",
]
