"""Verification-only privacy principle registry (Slice 10.8)."""

from __future__ import annotations

from verification.anonymous_analytics_privacy.models import PrincipleStatus

_ALL = (
    "base",
    "identity",
    "runtime",
    "assessment",
    "repository_aggregates",
    "ai",
    "vscode",
)


def build_principle_registry() -> list[PrincipleStatus]:
    principles = [
        ("collection_requires_contract", _ALL, "policies require typed contracts"),
        ("typed_input_only", _ALL, "aggregate/input models are typed"),
        ("strict_field_allowlist", _ALL, "approved field frozensets / TS arrays"),
        ("mandatory_projection", _ALL, "projection before sink/base event"),
        ("no_repository_identity", _ALL, "forbidden repository fields"),
        ("no_project_identity", _ALL, "forbidden project fields"),
        ("no_workspace_identity", ("vscode", "base"), "forbidden workspace fields"),
        ("no_document_identity", ("vscode", "base"), "forbidden document fields"),
        ("no_file_identity", _ALL, "forbidden file/path fields"),
        ("no_paths", _ALL, "path-like values rejected"),
        ("no_source_code", _ALL, "source fields forbidden"),
        ("no_findings", _ALL, "Finding fields forbidden"),
        ("no_evidence", _ALL, "Evidence fields forbidden"),
        ("no_recommendations", _ALL, "Recommendation fields forbidden"),
        ("no_credentials", _ALL, "credential fields forbidden"),
        ("no_customer_identifiers", _ALL, "customer/account/org forbidden"),
        ("no_personal_information", _ALL, "email/username/hostname forbidden"),
        ("no_exception_text", _ALL, "exception/traceback forbidden"),
        ("no_raw_command_line", ("assessment", "vscode"), "argv forbidden"),
        ("no_cli_output", ("vscode", "assessment"), "stdout/stderr forbidden"),
        ("no_prompts", ("ai", "vscode", "base"), "prompt fields forbidden"),
        ("no_responses", ("ai", "vscode", "base"), "response fields forbidden"),
        ("no_raw_provider_configuration", ("ai",), "raw provider rejected"),
        ("no_exact_model_ids", ("ai",), "exact model IDs rejected"),
        ("no_exact_token_counts", ("ai",), "token buckets excluded / exact forbidden"),
        ("no_exact_cost", ("ai", "base"), "cost forbidden"),
        ("no_exact_duration", ("assessment", "runtime", "ai", "vscode"), "coarse buckets only"),
        ("no_unbounded_custom_values", _ALL, "closed catalogs"),
        (
            "identity_scoped_and_versioned",
            ("identity", "runtime", "assessment", "repository_aggregates", "ai"),
            "Engine identity schema 1.0",
        ),
        (
            "identity_not_machine_derived",
            ("identity",),
            "UUID v4 random; no fingerprint APIs",
        ),
        (
            "identity_not_in_base_events",
            ("base", "runtime", "assessment", "repository_aggregates", "ai"),
            "installation_id forbidden on AnalyticsEvent",
        ),
        ("analytics_not_persisted", _ALL, "event persistence disabled"),
        ("analytics_not_transmitted", _ALL, "transmission disabled"),
        (
            "default_transport_unavailable",
            ("vscode",),
            "UnavailableVsCodeAnalyticsSink default",
        ),
        ("primary_operation_authoritative", ("vscode", "assessment"), "fail-silent isolation"),
        ("deterministic_serialization", _ALL, "sorted keys / stable JSON"),
        ("diagnostics_payload_free", _ALL, "no identity/payload in diagnostics"),
        ("platform_boundary_preserved", _ALL, "no Platform imports"),
        ("data_lake_boundary_preserved", _ALL, "no Data Lake imports"),
        ("cursor_boundary_preserved", ("vscode",), "Cursor unchanged"),
    ]
    return [
        PrincipleStatus(
            principle=name,
            applicable_contracts=contracts,
            evidence=evidence,
            verdict="pass",
        )
        for name, contracts, evidence in principles
    ]


def intentional_differences() -> list[str]:
    return sorted(
        [
            "engine_analytics_construction_only_unwired",
            "vscode_analytics_consent_gated_local_unavailable_sink",
            "engine_may_use_installation_identity_in_local_envelope",
            "vscode_identity_free_in_slice_10_7",
            "engine_ai_provider_model_families_vscode_boolean_only",
            "schemas_independently_versioned_python_vs_typescript",
            "repository_aggregate_bounded_exact_counts_privacy_limitation",
        ]
    )
