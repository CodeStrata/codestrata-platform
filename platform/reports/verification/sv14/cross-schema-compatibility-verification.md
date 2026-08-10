# SV.14 Cross-Schema Compatibility Verification

Verdict: **PASS_WITH_LIMITATIONS**

Repositories checked: 22
Checks: 80/80
Failures: 0
Warnings: 0

Results describe only the 22 curated pinned repositories in the v0.2.0 release-validation catalog and are not a product-wide accuracy or industry benchmark claim. Product schema 1.0 and verification schema 1.0.0 are distinct versioning namespaces.

## Contract registry

- `assessment_report` (engine) v1.2
- `findings_companion` (engine) v1.2
- `recommendations_companion` (engine) v1.2
- `validation_record` (engine_validation) v1.0
- `validation_summary` (engine_validation) v1.0
- `engineering_intelligence_report` (platform) v1.0
- `website_safe_eir_export` (platform) v1.0
- `community_cloud_api` (platform_community_cloud) v1.0
- `community_telemetry` (platform_community_cloud) v1.0
- `community_assessment_metadata` (platform_community_cloud) v1.0
- `community_cli_event` (platform_community_cloud) v1.0
- `community_extension_event` (platform_community_cloud) v1.0
- `community_ai_usage` (platform_community_cloud) v1.0
- `system_verification_reports` (verification) v1.0.0

## Checks

- [PASS] `catalog_release_validation_22` — catalog_count=22
- [PASS] `assessment_artifact_count_22` — count=22
- [PASS] `assessment_product_constant_1_2` — ASSESSMENT_JSON_SCHEMA_VERSION=1.2
- [PASS] `assessment_schema_version_all_1_2` — 22/22
- [PASS] `assessment_platform_ingestion_safety` — 22/22 after customer-safe projection
- [PASS] `assessment_finding_ids_stable_under_safe_projection` — 22/22
- [PASS] `assessment_findings_companion_reconcile` — 22/22
- [PASS] `validation_record_product_constant_1_0` — RECORD_SCHEMA_VERSION=1.0
- [PASS] `validation_records_schema_1_0` — 5/5 loaded
- [PASS] `validation_records_not_rewritten` — SV.14 loads historical records read-only
- [PASS] `validation_summary_product_constant_1_0` — SUMMARY_SCHEMA_VERSION=1.0
- [PASS] `validation_summary_schema_1_0` — summary_schema_version=1.0
- [PASS] `validation_summary_has_disclaimer` — disclaimer present
- [PASS] `validation_summary_no_absolute_paths` — absolute_path_scan
- [PASS] `ingestion_supported_assessment_schema_1_2` — SUPPORTED_ASSESSMENT_SCHEMA_VERSION=1.2
- [PASS] `ingestion_sample_accepted` — included=3 rejected=0 sample=3
- [PASS] `eir_product_constant_1_0` — EIR_SCHEMA=1.0
- [PASS] `eir_schema_version_1_0` — schema_version=1.0
- [PASS] `eir_roundtrip_identities` — report_id=eir:1eda169bfe4b7041265b253e drilldowns=22
- [PASS] `eir_future_version_rejected` — schema_version=2.0
- [PASS] `website_export_product_constant_1_0` — export_schema=1.0
- [PASS] `website_export_schema_1_0` — export_schema_version=1.0
- [PASS] `website_export_not_deserialized_as_full_eir` — from_stable_dict rejects website-safe projection
- [PASS] `website_export_no_source_or_pem` — hits=[]
- [PASS] `website_export_manifest_digests` — no_artifact_digests
- [PASS] `website_export_uses_export_schema_fields` — export_schema_version / report_schema_version (dataset_id omission intentional)
- [PASS] `website_export_ids_present` — export_id=eir-export:ca01b398f777e20ef75ea1f2 source_report_id=eir:1eda169bfe4b7041265b253e
- [PASS] `community_api_contract_1_0` — api=1.0
- [PASS] `community_endpoint_schemas_1_0` — {'telemetry': '1.0', 'assessment_metadata': '1.0', 'cli': '1.0', 'extension': '1.0', 'ai_usage': '1.0'}
- [PASS] `community_assessment_metadata_allows_1_2` — ALLOWED_ASSESSMENT_SCHEMA_VERSIONS=('1.2',)
- [PASS] `community_policy_versions_distinct` — rate_limit_policy=1.1 credential_format=1 auth_policy=1.0
- [PASS] `community_endpoint_schemas_not_interchangeable` — telemetry_vs_cli_vs_extension_vs_ai
- [PASS] `verification_vs_product_version_semantics` — verification reports use 1.0.0; product schemas use 1.0 / 1.2
- [PASS] `verification_reports_present` — present=4/4
- [PASS] `verification_reports_schema_1_0_0` — 4/4
- [PASS] `verification_verdict_vocabulary` — 4/4
- [PASS] `verification_not_product_runtime_input` — verification reports are review-only by contract
- [PASS] `identifier_domain_finding_prefix` — sample_domain_id_prefix=finding
- [PASS] `identifier_report_finding_ids_present` — count=22 repository=aspnetcore
- [PASS] `identifier_eir_report_id_prefix` — report_id=eir:1eda169bfe4b7041265b253e
- [PASS] `identifier_dataset_id_prefix` — dataset:3da1c591fcef727714304861
- [PASS] `identifier_export_id_prefix` — export_id=eir-export:ca01b398f777e20ef75ea1f2
- [PASS] `identifier_builders_callable` — build_dataset_id/build_report_id importable
- [PASS] `identifier_platform_does_not_require_engine_entity_regen` — ingestion preserves Engine finding IDs in report documents
- [PASS] `enum_confidence_core_vocab` — platform_ei=['high', 'limited', 'moderate', 'unavailable']
- [PASS] `enum_coverage_core_vocab` — platform_ei=['complete', 'disabled', 'insufficient_evidence', 'partial', 'unavailable']
- [PASS] `enum_severity_assessment_contract` — allowed=['critical', 'high', 'info', 'informational', 'low', 'medium']
- [PASS] `enum_visibility_present` — visibility=['anonymized', 'customer_private', 'internal', 'public']
- [PASS] `enum_contracts_remain_separate` — confidence/coverage/severity/priority/visibility/verdict remain contract-owned; no silent cross-defaulting verified via negative scenarios
- [PASS] `optional_assessment_coverage_present` — 22/22
- [PASS] `optional_assessment_head_confidence_present` — 22/22
- [PASS] `optional_finding_correlations_key_present` — 22/22 (may be empty list)
- [PASS] `optional_eir_interpretation_bundle_present` — interpretation_policy_bundle_id=interp-bundle:c719915c68cf94601a0e8f0b
- [PASS] `optional_missing_fields_do_not_alter_schema_version` — minimal fixture retains schema_version 1.2
- [PASS] `privacy_engine_redacts_pem_header` — header_only → [REDACTED]
- [PASS] `privacy_customer_safe_then_platform_accepts` — unsafe_before=True safe_after=True
- [PASS] `privacy_safe_descriptive_phrases_accepted` — phrases=7
- [PASS] `privacy_unsafe_fixtures_rejected` — fixtures=8
- [PASS] `privacy_sec002_categorical_evidence` — PRIVATE_KEY_FINDING_EVIDENCE categorical
- [PASS] `privacy_sanitize_customer_text_stable` — redacted marker stable
- [PASS] `roundtrip_assessment_json_ids` — findings=22 repository=aspnetcore
- [PASS] `roundtrip_eir_report_id` — report_id=eir:1eda169bfe4b7041265b253e
- [PASS] `roundtrip_eir_schema_version` — schema_version=1.0
- [PASS] `roundtrip_registry_order_stable` — contracts=14
- [PASS] `negative_assessment_future_2_0_rejected` — assessment schema 2.0
- [PASS] `negative_assessment_missing_version_rejected` — REQUIRE_1_2_COMPLETE
- [PASS] `negative_assessment_1_1_not_silently_1_2` — 1.1 rejected by REQUIRE_1_2_COMPLETE
- [PASS] `negative_unknown_confidence_not_defaulted` — ConfidenceLevel rejects unknown
- [PASS] `negative_eir_future_rejected` — schema_version=9.9
- [PASS] `negative_website_export_not_full_eir` — SV.12 JSON is allowlisted export projection
- [PASS] `negative_website_export_schema_distinct` — export schema is separate allowlisted projection
- [PASS] `negative_community_assessment_schema_2_0_not_allowed` — allowlist=('1.2',)
- [PASS] `negative_pem_does_not_survive_safe_projection` — customer-safe projection
- [PASS] `negative_safe_phrase_not_rejected` — Hardcoded credential detected.
- [PASS] `negative_compatibility_registry_order_independent` — n=14
- [PASS] `negative_null_schema_version_rejected` — schema_version=null
- [PASS] `negative_redact_secrets_clears_begin_fence` — redact_secrets
- [PASS] `sv11_ei_ready_22` — ready=22
- [PASS] `sv13_ledger_closed` — closure_status=closed
- [PASS] `sv14_no_product_schema_bump` — verification-only; no product schema versions changed

## Limitations

- SV.12 on-disk engineering-intelligence-report.json is the website-safe export projection (export_schema_version 1.0), not the full EIR domain document; SV.14 rebuilds full EIR from SV.10 for EIR round-trip checks.
- Website export may intentionally omit dataset_id; omission is allowlisted.
- Product schema 1.0 and verification schema 1.0.0 are distinct namespaces.
- Results describe only the 22 curated pinned repositories in the v0.2.0 release-validation catalog and are not a product-wide accuracy or industry benchmark claim. Product schema 1.0 and verification schema 1.0.0 are distinct versioning namespaces.

