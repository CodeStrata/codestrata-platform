# Monorepo Extraction Hardening

**Status:** Phase 14.2 Workstream B  
**Authority:** Release engineering  
**Manifest:** [`public-export-manifest.yaml`](../../public-export-manifest.yaml)

Community and private destination repositories are **generated mirrors**. The
monorepo (`codestrata-platform`) is the single source of truth. Extraction must
be safe for both **first-time repository creation** and **repeatable updates**.

Public destinations: `codestrata-engine`, `codestrata-examples`.
Private destinations: `codestrata-vscode`, `codestrata-docs`.
(Cursor private mirror `codestrata-cursor` retired in Slice 12.2.)

## Modes

| Mode | When | Behavior |
| --- | --- | --- |
| `first_time` | Staging destination empty / new | Full allowlist copy into `.export-staging/<export>/` |
| `update` | Staging destination already populated | Re-export overwrites allowlisted files; snapshot records `mode: update` |

Marker file written after each successful export:

- `.codestrata-export-snapshot.json` (tooling version, manifest version, content fingerprint)

## Commands

```bash
# Clean first-time staging
python scripts/export-public-repos.py --clean

# Repeatable update (idempotent content for allowlisted paths)
python scripts/export-public-repos.py

# Validate structure / legal files / forbid globs (no install)
python scripts/validate-public-exports.py --skip-install --skip-export

# Full release gate (includes export + secret scan + SBOM + provenance)
python scripts/validate_release.py
```

## Idempotency expectations

Re-running export without source changes must not alter allowlisted file
contents (excluding the snapshot metadata timestamp/fingerprint fields).

Helpers: `scripts/release/extraction.py`

- `tree_fingerprint`
- `assert_idempotent_export`
- `write_export_snapshot`
- `bootstrap_status`

## Forbidden in every staged mirror

- `platform/` (commercial)
- `governance/` (internal)
- `knowledge/` (internal)
- `.env` / credentials
- `.codestrata-test-knowledge/` synthetic secrets
- caches, `.venv/`, `.git/`, build/dist outputs
- private governance notes / proprietary architecture drafts

Allowlist wins: absence from a denylist is never sufficient.

## Destination validation

`validate-public-exports.py` enforces per-export `require_files` and
`forbid_globs` from the manifest. Release validation also runs a deterministic
secret scan on staging and fails on blocking findings.

## Per-product extraction notes

- Engine: [`engine/`](../../engine/) + [`docs/EXTRACTION.md`](../../docs/EXTRACTION.md)
- VS Code: [`vscode-plugin/EXTRACTION.md`](../../vscode-plugin/EXTRACTION.md)

## Safety guarantees

Extraction scripts:

- do **not** create GitHub remotes
- do **not** push
- do **not** publish Marketplace packages
- do **not** use signing credentials

## Publishing mirrors (separate intentional step)

Use [`scripts/publish-repository-mirrors.py`](../../scripts/publish-repository-mirrors.py)
only after export + validation. Repository creation on GitHub is **manual** and
must precede the first publish.

| Destination | Visibility |
| --- | --- |
| `CodeStrata/codestrata-engine` | public |
| `CodeStrata/codestrata-examples` | public |
| `CodeStrata/codestrata-vscode` | private |
| `CodeStrata/codestrata-docs` | private |

```bash
# Dry-run (default): selected repositories
python scripts/publish-repository-mirrors.py --repo codestrata-engine

# Dry-run all destinations (explicit --all)
python scripts/publish-repository-mirrors.py --all

# Real push (requires clean tree, matching snapshot, verified visibility)
python scripts/publish-repository-mirrors.py --repo codestrata-engine --push --confirm
```

Policy:

- Default is **dry-run**; `--push` alone is insufficient — also pass `--confirm`
- **No force-push** ( `--force` is rejected )
- Does **not** create GitHub repositories
- Does **not** tag or create releases
- Excludes `.codestrata-export-snapshot.json` from mirror commits
- **Bootstrap** (empty existing remote): single initial commit on `main`
- **Update** (existing `main`): replace tracked content, normal commit, fast-forward push only
- Private destinations refuse publish when visibility cannot be verified
- Public destinations refuse publish when GitHub visibility is not public
- Source monorepo working tree must be clean; staging snapshot `source_commit` must match `HEAD`
