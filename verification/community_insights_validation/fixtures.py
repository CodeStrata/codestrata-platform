"""Synthetic Data Lake fixtures for offline validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from verification.community_insights_validation._common import ensure_platform_importable

DAY = "2026-08-01"

# Poison values that must never appear in MetricResult, API JSON, or frontend scans.
POISON_INSTALLATION = "poison-install-7f3a9c"
POISON_MODEL = "poison-model-x9-leak"
POISON_S3 = "raw/stream=secret/poison-key"
POISON_PROMPT = "poison-prompt-leak-text"
POISON_REPOSITORY = "poison-repo-name"
POISON_FILE_PATH = "/secret/poison/path.py"
POISON_SOURCE = "poison-source-code-body"
POISON_CREDENTIAL = "poison-credential-token"

REDACTED_INSTALL = "[redacted_install]"


def envelope(*, stream: str, payload: dict, day: str = DAY) -> bytes:
    body = {
        "acceptance": {"accepted_at": f"{day}T12:00:00Z", "partition_date": day},
        "client": {"client_type": "cli"},
        "envelope_schema_version": "1.0",
        "event_stream": stream,
        "identity": {"event_key": "event:x", "safe_event_reference": "evt-x"},
        "payload": payload,
        "source_contract": {
            "policy_id": "p",
            "schema_name": "s",
            "schema_version": "1.0",
        },
    }
    return json.dumps(body, sort_keys=True).encode("utf-8")


def object_key(stream: str, day: str, name: str) -> str:
    y, m, d = day.split("-")
    return (
        f"raw/stream={stream}/schema_version=1.0/"
        f"year={y}/month={m}/day={d}/{name}.json"
    )


def poison_payload(*, stream: str, event_id: str, installation_suffix: str) -> dict:
    base = {
        "schema_version": "1.0",
        "event_id": event_id,
        "installation_id": f"{POISON_INSTALLATION}-{installation_suffix}",
        "client": {"name": "cli", "version": "0.2.0"},
        "context": {
            "repository_name": POISON_REPOSITORY,
            "file_path": POISON_FILE_PATH,
            "source_code": POISON_SOURCE,
            "prompt": POISON_PROMPT,
            "credential": POISON_CREDENTIAL,
            "s3_key": POISON_S3,
            "model_id": POISON_MODEL,
        },
    }
    if stream == "cli_event":
        base["event"] = {"operation": "assess"}
    elif stream == "ai_usage":
        base["usage"] = {
            "provider_family": "aws_bedrock",
            "model_family": "gpt_family",
            "model_id": POISON_MODEL,
        }
    elif stream == "assessment_metadata":
        base.update(
            {
                "assessment": {
                    "assessment_status": "completed",
                    "executed_heads": ["security"],
                },
                "repository": {"primary_language": "python"},
                "execution": {"result": "succeeded"},
                "artifacts": {},
            }
        )
    return base


@dataclass(frozen=True, slots=True)
class ValidationFixtures:
    objects: dict[str, bytes]
    expected_installations: int
    expected_events: int
    poison_strings: tuple[str, ...]


def build_fixtures() -> ValidationFixtures:
    """Synthetic lake objects covering installs vs events and suppression cohorts."""
    objects: dict[str, bytes] = {}

    # Three events, two distinct installations (inst-a appears twice).
    for idx, suffix in enumerate(("a", "a", "b")):
        objects[object_key("cli_event", DAY, f"evt-{idx}")] = envelope(
            stream="cli_event",
            payload=poison_payload(
                stream="cli_event",
                event_id=f"e{idx}",
                installation_suffix=suffix,
            ),
        )

    # Suppression cohorts: counts 1, 2, 3+ for provider families.
    provider_counts = {"solo_provider": 1, "duo_provider": 2, "trio_provider": 3}
    ai_idx = 0
    for provider, count in provider_counts.items():
        for _ in range(count):
            payload = poison_payload(
                stream="ai_usage",
                event_id=f"ai{ai_idx}",
                installation_suffix=str(ai_idx),
            )
            payload["usage"] = {
                "provider_family": provider,
                "model_family": "gpt_family",
                "model_id": POISON_MODEL,
            }
            objects[object_key("ai_usage", DAY, f"ai-{ai_idx}")] = envelope(
                stream="ai_usage",
                payload=payload,
            )
            ai_idx += 1

    return ValidationFixtures(
        objects=objects,
        expected_installations=2,
        expected_events=3,
        poison_strings=(
            POISON_INSTALLATION,
            POISON_MODEL,
            POISON_S3,
            POISON_PROMPT,
            POISON_REPOSITORY,
            POISON_FILE_PATH,
            POISON_SOURCE,
            POISON_CREDENTIAL,
        ),
    )


def bounded_reader(monorepo, fixtures: ValidationFixtures | None = None):
    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights_storage.fake_s3 import (
        FakeInsightsS3Client,
    )
    from codestrata_platform.community_cloud_api.insights_storage.reader import (
        BoundedS3Reader,
    )

    fx = fixtures or build_fixtures()
    client = FakeInsightsS3Client()
    for key, body in fx.objects.items():
        client.put_bytes(key, body)
    return BoundedS3Reader(bucket="validation-fixture-bucket", client=client), fx


def metric_window():
    return date(2026, 8, 1), date(2026, 8, 1)
