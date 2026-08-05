"""Strict fake S3 client for Data Lake verification (no network, no boto3)."""

from __future__ import annotations

from typing import Any


class FakeClientError(Exception):
    """Mimics botocore ClientError enough for map_s3_exception / adapter paths."""

    def __init__(self, code: str, operation_name: str = "PutObject") -> None:
        super().__init__(operation_name)
        self.response = {"Error": {"Code": code, "Message": "synthetic verification error"}}
        self.operation_name = operation_name


def client_error(code: str) -> FakeClientError:
    return FakeClientError(code)


class FakeS3Client:
    """Records every call and enforces IfNoneMatch semantics like real S3."""

    def __init__(self, *, put_behavior: Any = None) -> None:
        self.objects: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._put_behavior = put_behavior
        self._put_call_count = 0

    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("put_object", dict(kwargs)))
        self._put_call_count += 1
        if self._put_behavior is not None:
            outcome = self._put_behavior(self._put_call_count, kwargs)
            if outcome is not None:
                raise outcome

        if kwargs.get("IfNoneMatch") != "*":
            raise AssertionError("PutObject must always set IfNoneMatch='*'")
        key = kwargs["Key"]
        if key in self.objects:
            raise client_error("PreconditionFailed")
        self.objects[key] = {
            "Body": kwargs["Body"],
            "Metadata": dict(kwargs.get("Metadata", {})),
            "ContentLength": kwargs.get("ContentLength"),
            "ContentType": kwargs.get("ContentType"),
            "ServerSideEncryption": kwargs.get("ServerSideEncryption"),
            "ChecksumSHA256": kwargs.get("ChecksumSHA256"),
        }
        return {"ETag": '"fake-etag"'}

    def head_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("head_object", dict(kwargs)))
        key = kwargs["Key"]
        if key not in self.objects:
            raise client_error("404")
        stored = self.objects[key]
        return {"Metadata": dict(stored["Metadata"]), "ContentLength": stored["ContentLength"]}

    def put_object_call_count(self) -> int:
        return sum(1 for name, _ in self.calls if name == "put_object")

    def head_object_call_count(self) -> int:
        return sum(1 for name, _ in self.calls if name == "head_object")

    def last_put_kwargs(self) -> dict[str, Any]:
        for name, kwargs in reversed(self.calls):
            if name == "put_object":
                return kwargs
        raise AssertionError("no put_object call recorded")


__all__ = ["FakeClientError", "FakeS3Client", "client_error"]
