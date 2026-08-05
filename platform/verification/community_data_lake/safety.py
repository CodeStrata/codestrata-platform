"""Privacy contract checks for Community Data Lake verification (Slice 8.14)."""

from __future__ import annotations

import json
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.receipts import StorageReceipt
from codestrata_platform.community_cloud_api.data_lake.storage_results import (
    storage_result_to_public_dict,
)

from verification.community_data_lake.contract import FORBIDDEN_REPORT_FRAGMENTS
from verification.community_data_lake.inputs import project_all_streams, project_quarantine_object
from verification.community_data_lake.models import CheckResult

FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "object_key",
        "Authorization",
        "authorization",
        "bucket",
        "Bucket",
        "arn",
    }
)

REDACTED_SENTINEL = "REDACTED_TEST_VALUE"


def _scan_public_dict(payload: dict[str, Any], *, label: str) -> list[CheckResult]:
    checks: list[CheckResult] = []
    blob = json.dumps(payload, sort_keys=True)
    for index, key in enumerate(sorted(FORBIDDEN_PUBLIC_KEYS)):
        checks.append(
            CheckResult(
                name=f"privacy:{label}:forbidden_public_key_{index}",
                ok=key not in payload,
                detail="absent",
                category="privacy",
            )
        )
    for index, frag in enumerate(FORBIDDEN_REPORT_FRAGMENTS):
        checks.append(
            CheckResult(
                name=f"privacy:{label}:forbidden_fragment_{index}",
                ok=frag not in blob,
                detail="absent",
                category="privacy",
            )
        )
    return checks


def check_privacy() -> list[CheckResult]:
    checks: list[CheckResult] = []
    store = InMemoryCommunityDataLakeStore()
    obj = project_all_streams()["telemetry"]
    result = store.put_immutable_storage_object(obj)
    public = storage_result_to_public_dict(result)
    checks.extend(_scan_public_dict(public, label="storage_result"))

    if result.receipt is not None:
        checks.extend(_scan_public_dict(result.receipt.to_public_dict(), label="receipt"))

    receipt = StorageReceipt(
        status=StorageWriteStatus.STORED,
        object_id=obj.object_id,
        safe_event_reference=obj.safe_event_reference,
        event_stream=obj.event_stream,
        content_sha256=obj.content_sha256,
        content_length=obj.content_length,
        envelope_schema_version=obj.envelope_schema_version,
        source_schema_version=obj.source_schema_version,
        storage_policy_token=obj.storage_policy_token,
        stored_object_reference=f"lake-ref:{obj.opaque_object_id_hex[:16]}",
        object_key=obj.object_key,
    )
    checks.append(
        CheckResult(
            name="privacy:receipt_public_omits_internal_key",
            ok="object_key" not in receipt.to_public_dict(),
            detail="internal key omitted",
            category="privacy",
        )
    )

    for stream, storage_obj in project_all_streams().items():
        metadata = storage_obj.to_s3_metadata()
        for key, value in metadata.items():
            checks.append(
                CheckResult(
                    name=f"privacy:metadata:{stream}:no_event_tokens_in_{key[:20]}",
                    ok="event:" not in value and "evt-" not in value,
                    detail=key,
                    category="privacy",
                )
            )

    quarantine_obj = project_quarantine_object()
    quarantine_bytes = quarantine_obj.canonical_json_bytes.decode("utf-8")
    checks.extend(
        [
            CheckResult(
                name="privacy:quarantine:no_event_id_field",
                ok='"event_id"' not in quarantine_bytes,
                detail="no event_id key",
                category="privacy",
            ),
            CheckResult(
                name="privacy:quarantine:diagnostic_codes_only",
                ok="diagnostic_codes" in quarantine_bytes
                and REDACTED_SENTINEL not in quarantine_bytes,
                detail="bounded quarantine record",
                category="privacy",
            ),
            CheckResult(
                name="privacy:quarantine:no_raw_payload_field",
                ok='"payload"' not in quarantine_bytes,
                detail='no "payload" key',
                category="privacy",
            ),
        ]
    )

    return checks


__all__ = ["check_privacy"]
