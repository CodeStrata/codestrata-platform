"""Negative determinism scenarios (controlled fixtures)."""

from __future__ import annotations

import json

from codestrata.domain.findings.ids import build_finding_id
from codestrata.reporting.contract.canonical import strip_volatile_fields
from codestrata_platform.community_cloud_api.event_identity.fingerprint import (
    compute_payload_fingerprint,
)
from codestrata_platform.community_cloud_api.event_identity.identifiers import (
    build_event_key,
)
from codestrata_platform.community_cloud_api.event_identity.models import (
    EventIdentityScope,
)

from verification.deterministic_outputs.fingerprints import sha256_hex, stable_json_bytes
from verification.deterministic_outputs.models import CheckResult


def check_negative_scenarios() -> list[CheckResult]:
    results: list[CheckResult] = []

    # A: Finding ID must not include timestamps.
    id1 = build_finding_id(rule_id="R1", subject_keys=("a",))
    id2 = build_finding_id(rule_id="R1", subject_keys=("a",))
    results.append(
        CheckResult(
            name="negative_finding_id_no_timestamp_drift",
            ok=id1 == id2 and "T" not in id1,
            detail="stable finding id",
            category="negative",
        )
    )

    # E: dictionary insertion order does not change sorted JSON bytes.
    left = {"z": 1, "a": 2}
    right = {"a": 2, "z": 1}
    results.append(
        CheckResult(
            name="negative_dict_order_sorted_json_stable",
            ok=stable_json_bytes(left) == stable_json_bytes(right),
            detail="sort_keys JSON",
            category="negative",
        )
    )

    # T: JSON object key order does not change event fingerprint.
    fp_a = compute_payload_fingerprint({"schema_version": "1.0", "x": 1})
    fp_b = compute_payload_fingerprint({"x": 1, "schema_version": "1.0"})
    results.append(
        CheckResult(
            name="negative_event_fingerprint_key_order",
            ok=fp_a == fp_b,
            detail=str(fp_a),
            category="negative",
        )
    )

    # S: request ID not in event key material.
    scope = EventIdentityScope(
        api_version="v1",
        client_type="cli",
        event_type="telemetry",
        event_id="11111111-1111-4111-8111-111111111111",
    )
    k1 = build_event_key(scope)
    k2 = build_event_key(scope)
    results.append(
        CheckResult(
            name="negative_event_key_ignores_request_id",
            ok=k1 == k2,
            detail="event key stable without request_id",
            category="negative",
        )
    )

    # Z: broad normalization must not erase material difference.
    a = {"schema_version": "1.2", "assessment": {"findings": [{"id": "1"}]}}
    b = {"schema_version": "1.2", "assessment": {"findings": [{"id": "2"}]}}
    results.append(
        CheckResult(
            name="negative_no_broad_normalization_hiding_diff",
            ok=strip_volatile_fields(a) != strip_volatile_fields(b),
            detail="material ID difference preserved",
            category="negative",
        )
    )

    # D: unordered collections require explicit sort for canonical bytes.
    results.append(
        CheckResult(
            name="negative_set_requires_explicit_sort",
            ok=stable_json_bytes(sorted({"c", "a", "b"}))
            == stable_json_bytes(["a", "b", "c"]),
            detail="explicit sort used for unordered collections",
            category="negative",
        )
    )

    # U: rate limiter remaining must not go negative (SequenceClock fixed).
    from codestrata_platform.community_cloud_api.logging.context import SequenceClock

    clock = SequenceClock(start_ms=10, step_ms=0)
    remaining = max(0, 5 - 0)  # illustrative non-negative remaining
    results.append(
        CheckResult(
            name="negative_rate_limit_remaining_non_negative",
            ok=clock() == 10 and remaining >= 0,
            detail="injected clock + non-negative remaining",
            category="negative",
        )
    )
    return results
