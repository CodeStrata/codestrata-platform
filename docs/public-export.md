# Public export and synchronization

**codestrata-platform** is the private single source of truth for Community and
Commercial development.

Public GitHub repositories are **generated mirrors**. They must not be edited
independently.

## Actively developed repositories

| Repository | Visibility | Role |
| ---------- | ---------- | ---- |
| `codestrata-platform` | Private | Source of truth (this monorepo) |
| `codestrata-ui` | Private | Commercial UI (separate) |
| `codestrata-site` | Public | Marketing site (separate) |

## Generated public mirrors

| Monorepo path | Public repository |
| ------------- | ----------------- |
| `engine/` | `codestrata-engine` |
| `examples/` | `codestrata-examples` |
| `cursor-plugin/` | `codestrata-cursor` |
| `vscode-plugin/` | `codestrata-vscode` |

Mapping, includes, excludes, and validation commands:
[`public-export-manifest.yaml`](../public-export-manifest.yaml).

## How to export (staging only)

```bash
# All mirrors → .export-staging/<name>/
python scripts/export-public-repos.py

# One mirror
python scripts/export-public-repos.py --repo codestrata-engine

# Preview without writing
python scripts/export-public-repos.py --dry-run
```

The export script **does not** create remotes, push, or publish.

## How to validate

```bash
python scripts/validate-public-exports.py
python scripts/validate-public-exports.py --repo codestrata-examples --skip-install
```

Validation checks:

* no `platform/` or private artifacts in exports
* required packaging / governance files present
* engine fresh-venv install + CLI assess smoke
* examples language samples + sample reports
* plugin placeholders only contain allowed files

## How to review diffs

1. Run export into `.export-staging/`
2. Diff against a previous staging directory or a local clone of the public mirror
3. Review added / changed / deleted counts printed by the export script

## How to publish later

Publishing is an intentional follow-up (not part of Phase 5.23):

1. Validate exports
2. Sync staging trees into the public mirror clones (scripted in a later phase)
3. Open PRs on the public mirrors from the sync bot/account
4. Tag releases from mirror repos only after the platform commit is reviewed

## Emergency fixes without divergence

If a critical fix is needed in a public mirror:

1. **Still land the fix in `codestrata-platform` first**
2. Re-export and re-validate
3. Publish the mirror from staging

Do **not** commit directly to `codestrata-engine` / `examples` / plugin mirrors
except as a last-resort hotfix, and immediately backport to this monorepo in the
same incident window.

## Engine / platform boundary

* `engine/` must not import or require `platform/` at runtime
* Boundary tests: `tests/architecture/test_engine_platform_boundary.py`
* Implemented Platform capabilities live under `platform/src/codestrata_platform/`
  (`rag/`, `knowledge_graph/`) and register via Engine entry points
