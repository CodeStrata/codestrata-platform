"""No committed secrets / unsafe artifacts beyond pattern scans."""

from __future__ import annotations

from pathlib import Path

from infrastructure.verification.state import is_empty_s3_backend

INFRA = Path(__file__).resolve().parents[1]


def test_no_env_files() -> None:
    for path in INFRA.rglob(".env*"):
        assert path.name.endswith(".example") or False, path


def test_backend_example_only() -> None:
    assert (INFRA / "production" / "backend.tf.example").is_file()
    assert is_empty_s3_backend(INFRA / "production" / "backend.tf")


def test_scripts_refuse_hidden_credentials() -> None:
    needle = "AWS_SECRET_ACCESS_" + "KEY="
    for name in ("build-community-cloud-api.sh", "plan-production.sh", "validate.sh"):
        text = (INFRA / "scripts" / name).read_text(encoding="utf-8")
        assert needle not in text
        assert "aws_access_key_id" not in text.lower()


def test_smoke_script_health_only() -> None:
    text = (INFRA / "scripts" / "smoke-health.sh").read_text(encoding="utf-8")
    assert "/api/v1/health" in text
    assert "telemetry" not in text
    assert "assessment-metadata" not in text
    assert "cli-events" not in text
    assert "extension-events" not in text
    assert "ai-usage" not in text
    assert "Authorization" not in text
