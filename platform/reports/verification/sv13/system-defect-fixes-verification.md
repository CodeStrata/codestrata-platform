# SV.13 System Defect Fix Verification

Verdict: **PASS**

Repository population: 22

Results describe only the 22 curated pinned repositories in the v0.2.0 release-validation catalog and are not a product-wide accuracy or industry benchmark claim.

## Checks

- [PASS] `classification_complete` — classified=3
- [PASS] `safe_descriptive_phrases_accepted` — phrases=7 failures=[]
- [PASS] `unsafe_fixtures_rejected` — fixtures=8 issues=[]
- [PASS] `ingest_dubbo` — included=1 rejected=0 ids_stable=True
- [PASS] `ingest_juice-shop` — included=1 rejected=0 ids_stable=True
- [PASS] `ingest_nodegoat` — included=1 rejected=0 ids_stable=True
- [PASS] `sv11_ei_input_ready_22` — ready=22/22 defects=0
- [PASS] `sv12_dataset_population_22` — included=22 rejected=0
- [PASS] `sv12_drilldowns_22` — drilldowns=22
- [PASS] `sv12_no_unsafe_metadata_rejections` — rejected_reasons=[]
- [PASS] `website_export_safety` — defects=0 summary_ok=True
- [PASS] `order_independent_dataset_id` — forward=dataset:3da1c591fcef727714304861 reverse=dataset:3da1c591fcef727714304861
- [PASS] `order_independent_aggregation_id` — forward=aggregation:016d8960799e133ee200c252 reverse=aggregation:016d8960799e133ee200c252
- [PASS] `order_independent_report_id` — forward=eir:1eda169bfe4b7041265b253e reverse=eir:1eda169bfe4b7041265b253e

## Identities

- dataset_id: `dataset:3da1c591fcef727714304861`
- aggregation_id: `aggregation:016d8960799e133ee200c252`
- eir_report_id: `eir:1eda169bfe4b7041265b253e`
- interpretation_policy_bundle_id: `interp-bundle:c719915c68cf94601a0e8f0b`
- website_export_id: `eir-export:ca01b398f777e20ef75ea1f2`

