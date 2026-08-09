"""Slice 12.4 — Clean Community Product Boundaries.

## Scope

Remove Cursor from **active** Community product client vocabularies while
preserving **historical** schema 1.0 deserialization of previously accepted
`cursor_extension` records (Approach A).

## Active clients

- `codestrata_cli`
- `vscode_extension`
- `other_extension` (telemetry public contract only)

## Retired historical clients

- `cursor_extension` — deserialize / historical metadata validation only

## Schema compatibility decision

**Approach A** — active policy restriction without schema removal:

- Community Cloud endpoint schemas remain `1.0`
- Schema models still deserialize historical `cursor_extension`
- Current ingestion policy / active envelope construction / active storage
  projection reject retired clients
- Independent policy: `community-retired-client-policy:1.0`

## Verification

```bash
PYTHONPATH=platform/src:. .venv/bin/python -m verification.community_client_boundary_cleanup
```

Report:

`.codestrata-artifacts/validation/suites/sv12-4/community-client-boundary-cleanup-verification.json`

Schema: `community-client-boundary-cleanup-verification:1.0.0`

## Later Epic 12 slices (complete)

Infrastructure contract/exporter/export/target/CI and Epic completion are
Slices 12.5–12.10. See
`verification/product_cleanup_repository_split_completion/`.

## Explicit non-goals (at time of Slice 12.4)

- Stored event rewrite / S3 migration
- Production Cloud or Data Lake endpoint wiring
- Commit / tag / publish / deploy
- Epic 13
