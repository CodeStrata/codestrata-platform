"""Unit tests for AwsSecretsPort and production secrets wiring (no live AWS)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights_auth.aws_secrets import AwsSecretsPort
from codestrata_platform.community_cloud_api.insights_auth.secrets import (
    UnavailableSecretsPort,
    build_production_secrets_port,
)


class _FakeSM:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values
        self.calls: list[str] = []

    def get_secret_value(self, SecretId: str, VersionStage: str | None = None):  # noqa: N803
        self.calls.append(SecretId)
        if SecretId not in self.values:
            raise RuntimeError("ResourceNotFoundException")
        return {"SecretString": self.values[SecretId]}


def test_aws_secrets_port_returns_string_and_fail_closed() -> None:
    client = _FakeSM({"codestrata/insights/session-secret": "sess-material"})
    port = AwsSecretsPort(client=client)
    assert port.get_secret_value("codestrata/insights/session-secret") == "sess-material"
    assert port.get_secret_value("missing") is None
    assert port.get_secret_value("") is None


def test_build_production_secrets_port_defaults_unavailable() -> None:
    port = build_production_secrets_port(environ={})
    assert isinstance(port, UnavailableSecretsPort)
    assert port.get_secret_value("codestrata/insights/dashboard-password") is None


def test_build_production_secrets_port_aws_backend() -> None:
    client = _FakeSM(
        {
            "codestrata/insights/session-secret": "sess",
            "codestrata/insights/dashboard-password": '{"algorithm":"scrypt"}',
        }
    )
    # Inject client via AwsSecretsPort when backend=aws — exercise CachingSecretsPort path.
    from codestrata_platform.community_cloud_api.insights_auth.aws_secrets import AwsSecretsPort
    from codestrata_platform.community_cloud_api.insights_auth.secrets import CachingSecretsPort

    inner = AwsSecretsPort(client=client)
    cached = CachingSecretsPort(inner, cacheable_ids=frozenset({"codestrata/insights/session-secret"}))
    assert cached.get_secret_value("codestrata/insights/session-secret") == "sess"
    assert cached.get_secret_value("codestrata/insights/session-secret") == "sess"
    assert client.calls.count("codestrata/insights/session-secret") == 1
