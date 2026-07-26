# Metadata and traceability

## KnowledgeMetadata

Filterable facets attached to documents, chunks, and (as a flat dict) vector
records:

| Field | Purpose |
| ----- | ------- |
| `tenant_id` | Multi-tenant isolation |
| `repository_id` | Repository isolation |
| `scan_id` | Assessment / scan isolation |
| `branch` / `commit_sha` | Revision context |
| `language` / `framework` | Tech stack facets |
| `source_type` | Stable knowledge origin kind |
| `intelligence_pack` | Rule/assessment pack identity |
| `assessment_version` | Assessment schema/version |
| `finding_id` / `rule_id` | Finding lineage |
| `severity` / `confidence` | Risk facets |
| `file_path` / `symbol_name` | Code location |
| `content_hash` | Content identity |
| `extra` | Non-colliding extension map |

`as_filter_dict()` flattens reserved fields (omit `None`) and merges `extra`
for vector metadata filtering. Extension keys must not collide with reserved
names.

## KnowledgeSource

Provenance pointers: `source_type`, `repository_id`, `scan_id`, `commit_sha`,
`branch`, `file_path`, `assessment_type`, `finding_id`, `rule_id`,
`evidence_id`, `report_section`.

## KnowledgeTraceability

Audit binding:

- `source` — `KnowledgeSource`
- `source_id` — upstream artifact identity
- optional `assessment_version`, `parent_document_id`, `notes`

Documents and chunks carry both **metadata** (query facets) and
**traceability** (audit lineage). Serialization is byte-stable via sorted-key
JSON (`dumps_stable_json` / domain fingerprint helpers).
