# Platform verification packages

Platform-only verification packages live under `platform/verification/`. None
are shipped in the `codestrata_platform` runtime wheel.

| Package | Schema | Report |
| --- | --- | --- |
| [engineering_intelligence](./engineering_intelligence/) | SV.6 | `platform/reports/verification/engineering-intelligence-verification.json` |
| [community_cloud_api](./community_cloud_api/) | SV.7 | `platform/reports/verification/community-cloud-api-verification.json` |
| [website_export](./website_export/) | SV.8 | `platform/reports/verification/website-export-verification.json` |
| [community_data_lake](./community_data_lake/) | SV.9 (data lake) | `platform/reports/verification/community-data-lake-verification.json` |
| [community_data_lake_completion](./community_data_lake_completion/) | Slice 8.15 (Epic 8 completion) | `platform/reports/verification/community-data-lake-completion-verification.json` |
| [cross_schema_compatibility](./cross_schema_compatibility/) | SV.14 | `platform/reports/verification/cross-schema-compatibility-verification.json` |
| [deterministic_outputs](./deterministic_outputs/) | SV.15 | `platform/reports/verification/deterministic-outputs-verification.json` |

Infrastructure deployment foundation verification (OpenTofu module/production
root) lives separately under `infrastructure/verification/` (also referred to
as SV.9 in infrastructure docs).

## Community Data Lake (Slice 8.14)

```bash
PYTHONPATH=platform:platform/src:platform/tests:. \
  python -m verification.community_data_lake \
  --output-dir platform/reports/verification
```

Use `--skip-opentofu` for fast CI runs. Full release runs should include
OpenTofu CLI validation when `tofu` is available.

## Community Data Lake completion (Slice 8.15)

```bash
PYTHONPATH=platform:platform/src:platform/tests:. \
  python -m verification.community_data_lake_completion \
  --output-dir platform/reports/verification
```

Reuses the SV.9 integration report. Epic 8 complete; production ingestion not
operational; Epic 9 not started.

Integration pytest coverage:
`platform/tests/community_cloud_api/data_lake/integration/`
