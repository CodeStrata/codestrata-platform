"""Production posture and dependency isolation scenarios (Slice 8.14)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_POLICY_VERSION,
)
from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.community_cloud_api.data_lake.schema_compatibility import (
    ENVELOPE_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.deployment import (
    create_production_foundation_app,
    load_deployment_settings,
)
from fastapi.testclient import TestClient

from verification.community_data_lake.contract import (
    COMMUNITY_DATA_LAKE_VERIFICATION_VERSION,
)
from verification.community_data_lake.models import CheckResult

REPO = Path(__file__).resolve().parents[3]
ENGINE_SRC = REPO / "engine" / "src" / "codestrata"
DATA_LAKE_PKG = (
    REPO / "platform" / "src" / "codestrata_platform" / "community_cloud_api" / "data_lake"
)
DATA_LAKE_INFRA = DATA_LAKE_PKG / "infrastructure"
APP_PY = REPO / "platform" / "src" / "codestrata_platform" / "community_cloud_api" / "app.py"
WIRING_PY = (
    REPO / "platform" / "src" / "codestrata_platform" / "community_cloud_api" / "deployment" / "wiring.py"
)


def check_production_fail_closed() -> list[CheckResult]:
    client = TestClient(create_production_foundation_app(settings=load_deployment_settings({})))
    health = client.get("/api/v1/health")
    app = create_production_foundation_app(settings=load_deployment_settings({}))
    registry = app.state.community_cloud_route_registry
    wiring_text = WIRING_PY.read_text(encoding="utf-8")
    app_text = APP_PY.read_text(encoding="utf-8")

    return [
        CheckResult(
            name="production:health_ok",
            ok=health.status_code == 200 and health.json().get("status") == "ok",
            detail=f"status={health.status_code}",
            category="production",
        ),
        CheckResult(
            name="production:ingestion_and_insights_routes",
            ok=registry.diagnostics().registered_route_count == 19,
            detail=f"count={registry.diagnostics().registered_route_count}",
            category="production",
        ),
        CheckResult(
            name="production:wiring_ingestion_gated",
            ok=(
                "ingestion_enabled" in wiring_text
                and "UnavailableCommunityCredentialVerifier" in wiring_text
                and "create_community_data_lake_store" in wiring_text
                and "InMemoryTelemetryEventSink" not in wiring_text
            ),
            detail="gated_wiring",
            category="production",
        ),
        CheckResult(
            name="production:app_no_storage_factory",
            ok="storage_factory" not in app_text
            and "create_community_data_lake_store" not in app_text,
            detail="unwired",
            category="production",
        ),
    ]


def check_schema_versions() -> list[CheckResult]:
    from codestrata_platform.community_cloud_api.data_lake.access_policy import (
        COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION,
    )
    from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
        COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION,
    )
    from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
        COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION,
    )
    from codestrata_platform.community_cloud_api.data_lake.retention_policy import (
        COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION,
    )
    from codestrata_platform.community_cloud_api.data_lake.storage import (
        COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION,
    )
    from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
        AI_USAGE_PARTITION_POLICY_VERSION,
    )
    from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
        ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
    )
    from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
        CLI_EVENT_PARTITION_POLICY_VERSION,
    )
    from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
        EXTENSION_EVENT_PARTITION_POLICY_VERSION,
    )
    from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
        TELEMETRY_PARTITION_POLICY_VERSION,
    )

    return [
        CheckResult(
            name="schema:data_lake_policy_1_0",
            ok=COMMUNITY_DATA_LAKE_POLICY_VERSION == "1.0",
            detail=COMMUNITY_DATA_LAKE_POLICY_VERSION,
            category="schema",
        ),
        CheckResult(
            name="schema:envelope_1_0",
            ok=ENVELOPE_SCHEMA_VERSION == "1.0"
            and COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION == "1.0",
            detail=ENVELOPE_SCHEMA_VERSION,
            category="schema",
        ),
        CheckResult(
            name="schema:assessment_report_1_2",
            ok=ASSESSMENT_JSON_SCHEMA_VERSION == "1.2",
            detail=ASSESSMENT_JSON_SCHEMA_VERSION,
            category="schema",
        ),
        CheckResult(
            name="schema:verification_1_0_0",
            ok=COMMUNITY_DATA_LAKE_VERIFICATION_VERSION == "1.0.0",
            detail=COMMUNITY_DATA_LAKE_VERIFICATION_VERSION,
            category="schema",
        ),
        CheckResult(
            name="schema:quarantine_policy_1_0",
            ok=COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION == "1.0",
            detail=COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION,
            category="schema",
        ),
        CheckResult(
            name="schema:retention_policy_1_0",
            ok=COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION == "1.0",
            detail=COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION,
            category="schema",
        ),
        CheckResult(
            name="schema:encryption_policy_1_0",
            ok=COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION == "1.0",
            detail=COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION,
            category="schema",
        ),
        CheckResult(
            name="schema:access_policy_1_0",
            ok=COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION == "1.0",
            detail=COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION,
            category="schema",
        ),
        CheckResult(
            name="schema:storage_policy_1_0",
            ok=COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION == "1.0",
            detail=COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION,
            category="schema",
        ),
        CheckResult(
            name="schema:partition_policies_1_0",
            ok=all(
                version == "1.0"
                for version in (
                    TELEMETRY_PARTITION_POLICY_VERSION,
                    ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
                    CLI_EVENT_PARTITION_POLICY_VERSION,
                    EXTENSION_EVENT_PARTITION_POLICY_VERSION,
                    AI_USAGE_PARTITION_POLICY_VERSION,
                )
            ),
            detail="all 1.0",
            category="schema",
        ),
    ]


def check_dependency_isolation() -> list[CheckResult]:
    domain_modules = [
        path
        for path in DATA_LAKE_PKG.rglob("*.py")
        if DATA_LAKE_INFRA not in path.parents
    ]
    boto_offenders: list[str] = []
    for path in domain_modules:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "boto3" in node.module or "botocore" in node.module:
                    boto_offenders.append(path.name)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in {"boto3", "botocore"}:
                        boto_offenders.append(path.name)

    engine_offenders: list[str] = []
    import_hit = re.compile(
        r"^(?:from|import)\s+\S*data_lake",
        re.MULTILINE,
    )
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if import_hit.search(text) or "community_cloud_api.data_lake" in text:
            engine_offenders.append(str(path.relative_to(ENGINE_SRC)))

    return [
        CheckResult(
            name="isolation:data_lake_domain_no_boto3",
            ok=not boto_offenders,
            detail=",".join(sorted(set(boto_offenders))) or "clean",
            category="isolation",
        ),
        CheckResult(
            name="isolation:engine_no_data_lake",
            ok=not engine_offenders,
            detail=",".join(engine_offenders) or "clean",
            category="isolation",
        ),
    ]


__all__ = [
    "check_dependency_isolation",
    "check_production_fail_closed",
    "check_schema_versions",
]
