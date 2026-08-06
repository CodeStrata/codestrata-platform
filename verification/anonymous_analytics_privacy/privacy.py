"""Base anonymous analytics contract checks (Slice 10.1)."""

from __future__ import annotations

from codestrata.telemetry.analytics.errors import AnalyticsError
from codestrata.telemetry.analytics.events import (
    FORBIDDEN_ANALYTICS_FIELD_NAMES,
    AnalyticsCategory,
    AnalyticsEvent,
    AnalyticsLifecycle,
)
from codestrata.telemetry.analytics.projection import project_analytics_from_mapping
from verification.anonymous_analytics_privacy.engine_inputs import EngineAnalyticsInventory
from verification.anonymous_analytics_privacy.models import CheckResult, Defect


def check_base_contract(
    engine: EngineAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    required_categories = {
        "runtime",
        "assessment",
        "repository_aggregates",
        "ai_usage",
        "vscode_usage",
    }
    ok_cats = required_categories <= set(engine.approved_categories)
    checks.append(
        CheckResult(
            name="base:approved_categories",
            ok=ok_cats,
            detail=",".join(sorted(engine.approved_categories)),
            category="base",
            contract="base",
        )
    )
    if not ok_cats:
        defects.append(
            Defect(
                "base-contract defect",
                "categories",
                str(sorted(required_categories)),
                str(sorted(engine.approved_categories)),
            )
        )

    checks.append(
        CheckResult(
            name="base:installation_id_forbidden",
            ok="installation_id" in engine.forbidden_fields
            and not engine.base_installation_id_allowed,
            detail="installation_id not allowed on base AnalyticsEvent",
            category="base",
            contract="base",
        )
    )
    checks.append(
        CheckResult(
            name="base:collection_disabled",
            ok=not engine.base_collection_enabled,
            category="base",
            contract="base",
        )
    )
    checks.append(
        CheckResult(
            name="base:persistence_disabled",
            ok=not engine.base_persistence_enabled,
            category="base",
            contract="base",
        )
    )
    checks.append(
        CheckResult(
            name="base:transmission_disabled",
            ok=not engine.base_transmission_enabled,
            category="base",
            contract="base",
        )
    )

    # Identity cannot enter base event projection.
    rejected = False
    try:
        project_analytics_from_mapping(
            {
                "event_type": "analytics_runtime_defined",
                "category": AnalyticsCategory.RUNTIME.value,
                "client_name": "codestrata_cli",
                "lifecycle": AnalyticsLifecycle.DEFINED.value,
                "privacy_projection_applied": True,
                "installation_id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
            }
        )
    except AnalyticsError:
        rejected = True
    checks.append(
        CheckResult(
            name="base:rejects_installation_id_field",
            ok=rejected,
            detail="projection rejects installation_id",
            category="base",
            contract="base",
        )
    )
    if not rejected:
        defects.append(
            Defect(
                "identity defect",
                "base_projection",
                "reject installation_id",
                "accepted",
            )
        )

    # Illustrative typed event remains identity-free.
    event = AnalyticsEvent(
        event_type="analytics_runtime_defined",
        category=AnalyticsCategory.RUNTIME,
        privacy_projection_applied=True,
    )
    payload = event.to_intake_dict()
    checks.append(
        CheckResult(
            name="base:event_identity_free",
            ok="installation_id" not in payload,
            category="base",
            contract="base",
        )
    )

    # Forbidden matrix sampling.
    for field in ("prompt", "repository", "source_code", "api_key", "model_id"):
        ok = field in FORBIDDEN_ANALYTICS_FIELD_NAMES
        checks.append(
            CheckResult(
                name=f"base:forbidden:{field}",
                ok=ok,
                category="privacy",
                contract="base",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    "base-contract defect",
                    field,
                    "forbidden",
                    "missing",
                )
            )

    for item in checks:
        if not item.ok and all(d.component != item.name for d in defects):
            if item.name.startswith("base:collection") or item.name.startswith(
                "base:persistence"
            ) or item.name.startswith("base:transmission") or item.name.startswith(
                "base:installation"
            ):
                defects.append(
                    Defect(
                        "base-contract defect",
                        item.name,
                        "true",
                        "false",
                    )
                )
    return checks, defects
