# Website-safe static export (Slice 6.10)

Deterministic, self-contained JSON and HTML export of a commercial
`EngineeringIntelligenceReport`.

The website-safe export is a sanitized projection of the commercial Engineering
Intelligence Report. It is not the canonical repository assessment artifact and
does not include source code, raw Evidence, private paths, or unrestricted
repository metadata.

Public exports must not be presented as industry benchmarks unless the dataset
and methodology independently support that claim.

## Boundary

| Concern | Location |
| --- | --- |
| Export policy / projection / validation / manifest | `application/website_export/` |
| Self-contained HTML renderer | `presentation/static_html/` |
| Path-safe writer | `infrastructure/static_export_writer.py` |

Platform-only. Engine and Community Edition do not expose EIR website export.

## Pipeline

```text
EngineeringIntelligenceReport
  → WebsiteSafeExportDocument   (allowlisted projection)
  → engineering-intelligence-report.json
  → engineering-intelligence-report.html  (from the same projection)
  → export-manifest.json
```

Do not serialize the internal EIR and strip fields afterward.

## Export scopes

Explicit `ExportScope` values (never inferred from title/URL):

- `public_oss` — PUBLIC + publication-permitted identities only
- `customer_private` — private labels allowed; labeled non-public
- `internal` — internal labels allowed; labeled non-public
- `anonymized_external` — stable aliases only; original IDs/names prohibited

## WebsiteExportBuildPolicy

Deterministic `policy_token` participates in `IntelligenceInterpretationPolicyBundle`
as `website_export_policy_token`. Changing export policy changes:

- interpretation-policy bundle ID
- report ID (when quality is rebuilt with the new token)
- export ID / artifact digests

Dataset ID is unchanged. External assets are prohibited.

## Export schema

`WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION = "1.0"` — projection contract only.

Commercial EIR schema remains **1.0**. Engine assessment schema remains **1.2**.

## Export identity

`eir-export:{sha256[:24]}` from source report ID, interpretation-policy bundle ID,
export policy token, export schema version, and artifact-template version.
Timestamps and filesystem paths are excluded.

## Artifacts

| File | Role |
| --- | --- |
| `engineering-intelligence-report.json` | Sorted-key UTF-8 website-safe JSON |
| `engineering-intelligence-report.html` | Offline HTML5, embedded CSS, restrictive CSP, no JavaScript |
| `export-manifest.json` | Artifact list + SHA-256 digests of JSON/HTML (not recursive) |

## Safety

Fail-closed validation rejects absolute paths, `file://`, secret-like strings,
scripts/forms/iframes, external assets (unless policy later permits public source
links), unresolved anchors, duplicate IDs, and identity leaks in
public/anonymized scopes.

Repository drill-downs remain bounded navigation subsets with visible truncation.

## CSP / offline

Default CSP matches Engine report conventions (`default-src 'none'`,
`script-src 'none'`, `style-src 'unsafe-inline'`, no remote fonts/connect).
Print CSS keeps authoritative content available. Accessibility: one `h1`,
`main`, TOC `nav`, skip link, logical headings.

## Relationship to Slice 6.11

Slice 6.11 uses this exporter to publish the public OSS demonstration artifacts
under `platform/demo/`. Hosting, branding, and SaaS delivery remain out of scope.
