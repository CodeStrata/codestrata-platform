# SV.15 Deterministic Output Verification

Verdict: **PASS_WITH_LIMITATIONS**

Repositories: 22
Checks: 82/82
Defects: 0
Warnings: 0

Results describe only the 22 curated pinned repositories in the v0.2.0 release-validation catalog and are not a product-wide accuracy or industry benchmark claim.

## Approved volatile fields

- `assessment.generated_at` — execution timing / generation metadata
- `assessment.timing` — execution timing / generation metadata
- `assessment.ai.latency_ms` — execution timing / generation metadata
- `assessment.static_analysis` — execution timing / generation metadata
- `manifest.generated_at` — execution timing / generation metadata
- `manifest.scan_id` — per-run scan identifier (live acceptance extra path)
- `ValidationSummaryArtifact.generated_at` — summary generation timestamp
- `CommunityCloud.request_id` — transport request id; not event identity material
- `verification.execution_environment_labels` — optional local labels; not identity

## Checks

- [PASS] `catalog_release_validation_22` — count=22
- [PASS] `inputs_determinism_samples_loaded` — samples=4
- [PASS] `engine_sv10_determinism_samples_present` — missing=none
- [PASS] `engine_sv10_determinism_samples_ok` — cleanarchitecture/django/bookstack/aspnetcore
- [PASS] `engine_finding_id_builder_stable` — prefix=finding
- [PASS] `engine_recommendation_id_builder_stable` — prefix=recommendation
- [PASS] `engine_sample_fingerprint_stable_cleanarchitecture` — sha256=66114b724b7f7d89…
- [PASS] `engine_sample_finding_ids_present_cleanarchitecture` — count=17
- [PASS] `engine_sample_fingerprint_stable_django` — sha256=896b318d91f73f11…
- [PASS] `engine_sample_finding_ids_present_django` — count=202
- [PASS] `engine_sample_fingerprint_stable_bookstack` — sha256=0ff606e1c6ea4298…
- [PASS] `engine_sample_finding_ids_present_bookstack` — count=166
- [PASS] `engine_sample_fingerprint_stable_aspnetcore` — sha256=446965d888dcaad3…
- [PASS] `engine_sample_finding_ids_present_aspnetcore` — count=22
- [PASS] `html_fingerprint_stable_cleanarchitecture` — sha256=adac525c977983ed… len=171618
- [PASS] `html_anchor_ids_unique_cleanarchitecture` — anchors=66 duplicates=0
- [PASS] `html_fingerprint_stable_django` — sha256=94524855e1709387… len=836275
- [PASS] `html_anchor_ids_unique_django` — anchors=403 duplicates=0
- [PASS] `html_fingerprint_stable_bookstack` — sha256=a9b68bd0a9c19997… len=693073
- [PASS] `html_anchor_ids_unique_bookstack` — anchors=393 duplicates=0
- [PASS] `html_fingerprint_stable_aspnetcore` — sha256=cc726c436873ad9f… len=217116
- [PASS] `html_anchor_ids_unique_aspnetcore` — anchors=72 duplicates=0
- [PASS] `validation_record_schema_1_0` — RECORD_SCHEMA_VERSION=1.0
- [PASS] `validation_summary_schema_1_0` — SUMMARY_SCHEMA_VERSION=1.0
- [PASS] `validation_fp_id_stable` — fp_id_prefix=fp
- [PASS] `validation_fn_id_stable` — fn_id_prefix=fn
- [PASS] `validation_summary_fingerprint_stable` — sha256=9070ea544f1b7128…
- [PASS] `ei_order_invariant_catalog` — dataset=dataset:3da1c591fcef727714304861 report=eir:1eda169bfe4b7041265b253e
- [PASS] `ei_order_invariant_reverse` — dataset=dataset:3da1c591fcef727714304861 report=eir:1eda169bfe4b7041265b253e
- [PASS] `ei_order_invariant_language` — dataset=dataset:3da1c591fcef727714304861 report=eir:1eda169bfe4b7041265b253e
- [PASS] `ei_order_invariant_tier_proxy` — dataset=dataset:3da1c591fcef727714304861 report=eir:1eda169bfe4b7041265b253e
- [PASS] `ei_order_invariant_shuffled` — dataset=dataset:3da1c591fcef727714304861 report=eir:1eda169bfe4b7041265b253e
- [PASS] `ei_technology_distribution_present` — technology_distribution section
- [PASS] `ei_capability_comparisons_present` — capability_comparisons section
- [PASS] `ei_population_22` — included=22 drilldowns=22
- [PASS] `eir_roundtrip_report_id` — report_id=eir:1eda169bfe4b7041265b253e
- [PASS] `eir_roundtrip_interpretation_bundle` — bundle=interp-bundle:c719915c68cf94601a0e8f0b
- [PASS] `eir_schema_version_1_0` — schema_version=1.0
- [PASS] `website_json_bytes_identical` — sha256=265134fc56ac2990…
- [PASS] `website_html_bytes_identical` — sha256=25ad4f32244277b7…
- [PASS] `website_manifest_bytes_identical` — sha256=3ecf193a0f1b7139…
- [PASS] `website_export_id_stable` — export_id=eir-export:ca01b398f777e20ef75ea1f2
- [PASS] `website_output_dir_independent` — two temp dirs (incl. spaces) byte-identical
- [PASS] `website_sv12_export_present` — sv12 json/html/manifest present
- [PASS] `community_fingerprint_key_order_invariant` — fingerprint=fp:64e14eb2da550acb657a0eac13483a6d1da233d857eb38c54ce09228380498ca
- [PASS] `community_event_key_stable` — event_key=event:c514d85bb01a9b28916357ff
- [PASS] `community_safe_reference_stable` — safe_ref=evt-c514d85bb01a
- [PASS] `community_sequence_clock_stable` — t1=1000000 t2=1000000
- [PASS] `infrastructure_verdict_stable` — verdict=pass
- [PASS] `infrastructure_ok_stable` — ok=True
- [PASS] `infrastructure_defects_stable` — defects=0
- [PASS] `infrastructure_no_home_path_a` — hits=none
- [PASS] `infrastructure_no_home_path_b` — hits=none
- [PASS] `verification_reports_present` — present=5
- [PASS] `verification_report_fingerprint_curated-repository-validation` — sha256=ff086aa9dd1ccad0… file=curated-repository-validation.json
- [PASS] `verification_report_schema_curated-repository-validation` — schema_version=1.0.0
- [PASS] `verification_report_no_home_path_curated-repository-validation` — hits=none
- [PASS] `verification_report_fingerprint_assessment-consistency-verification` — sha256=2a3966d4b638a845… file=assessment-consistency-verification.json
- [PASS] `verification_report_schema_assessment-consistency-verification` — schema_version=1.0.0
- [PASS] `verification_report_no_home_path_assessment-consistency-verification` — hits=none
- [PASS] `verification_report_fingerprint_engineering-intelligence-quality-review` — sha256=287c7815549ab905… file=engineering-intelligence-quality-review.json
- [PASS] `verification_report_schema_engineering-intelligence-quality-review` — schema_version=1.0.0
- [PASS] `verification_report_no_home_path_engineering-intelligence-quality-review` — hits=none
- [PASS] `verification_report_fingerprint_system-defect-fixes-verification` — sha256=f5fdfe748265501e… file=system-defect-fixes-verification.json
- [PASS] `verification_report_schema_system-defect-fixes-verification` — schema_version=1.0.0
- [PASS] `verification_report_no_home_path_system-defect-fixes-verification` — hits=none
- [PASS] `verification_report_fingerprint_cross-schema-compatibility-verification` — sha256=472313502563964c… file=cross-schema-compatibility-verification.json
- [PASS] `verification_report_schema_cross-schema-compatibility-verification` — schema_version=1.0.0
- [PASS] `verification_report_no_home_path_cross-schema-compatibility-verification` — hits=none
- [PASS] `paths_no_home_or_users_in_canonical_reports` — hits=none
- [PASS] `roundtrip_assessment_fingerprint` — sha256=66114b724b7f7d89…
- [PASS] `roundtrip_eir_subset_report_id` — report_id=eir:0149f95f4446f856a935e703
- [PASS] `roundtrip_python_hashseed_stable_json` — digests=['e6106728ec59', 'e6106728ec59', 'e6106728ec59']
- [PASS] `negative_finding_id_no_timestamp_drift` — stable finding id
- [PASS] `negative_dict_order_sorted_json_stable` — sort_keys JSON
- [PASS] `negative_event_fingerprint_key_order` — fp:ebb2ba42c3805c73c790fd3b93c5937a486ca7f10409aae0e8bb4f6357d220c8
- [PASS] `negative_event_key_ignores_request_id` — event key stable without request_id
- [PASS] `negative_no_broad_normalization_hiding_diff` — material ID difference preserved
- [PASS] `negative_set_requires_explicit_sort` — explicit sort used for unordered collections
- [PASS] `negative_rate_limit_remaining_non_negative` — injected clock + non-negative remaining
- [PASS] `sv15_no_full_22_reassess` — preserved artifacts only
- [PASS] `sv15_no_product_id_scheme_change` — verification-only; no ID redesign

## Limitations

- Full 22-repository reassessment was not performed; preserved SV.10 artifacts and SV.10 determinism samples were reused.
- Locale variants are reported only when available in the environment.
- Results describe only the 22 curated pinned repositories in the v0.2.0 release-validation catalog and are not a product-wide accuracy or industry benchmark claim.

