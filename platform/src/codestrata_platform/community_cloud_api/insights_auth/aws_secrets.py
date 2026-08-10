"""AWS Secrets Manager SecretsPort — values never logged."""

from __future__ import annotations

from typing import Any


class AwsSecretsPort:
    """Read secret string values by identifier via Secrets Manager.

    Fail-closed: missing/denied secrets return None. Never logs secret values.
    """

    def __init__(self, *, client: Any | None = None, region_name: str | None = None) -> None:
        self._client = client
        self._region_name = region_name

    def _sm(self) -> Any:
        if self._client is not None:
            return self._client
        import boto3

        kwargs: dict[str, str] = {}
        if self._region_name:
            kwargs["region_name"] = self._region_name
        self._client = boto3.client("secretsmanager", **kwargs)
        return self._client

    def get_secret_value(self, secret_id: str) -> str | None:
        if not secret_id or not str(secret_id).strip():
            return None
        try:
            # Explicit AWSCURRENT — never pin AWSPENDING/legacy stages for login.
            response = self._sm().get_secret_value(
                SecretId=secret_id,
                VersionStage="AWSCURRENT",
            )
        except Exception:
            # Fail-closed — do not leak exception detail that may include ARNs/values.
            return None
        if "SecretString" in response and response["SecretString"] is not None:
            return str(response["SecretString"])
        binary = response.get("SecretBinary")
        if binary is None:
            return None
        if isinstance(binary, (bytes, bytearray)):
            return bytes(binary).decode("utf-8")
        return None
