# CodeStrata Rename (Phase 5.16)

Complete pre-v1.0 rename from AIMF / AI Modernization Factory to **CodeStrata**.

## What changed

| Before | After |
| ------ | ----- |
| Package `aimf` | `codestrata` |
| CLI `aimf` | `codestrata` |
| Config `aimf.toml` | `codestrata.toml` |
| Defaults `aimf.defaults.toml` | `codestrata.defaults.toml` |
| Runtime dir `.aimf/` | `.codestrata/` |
| Env `AIMF_*` | `CODESTRATA_*` |
| Dist name `ai-modernization-factory` | `codestrata` |
| Settings type `AimfSettings` | `CodestrataSettings` |
| Knowledge DB column `aimf_version` | `codestrata_version` (schema v3) |

## Intentional remaining references

| Reference | Reason |
| --------- | ------ |
| `codestrata.io` schema namespaces | Historical public schema IDs; do not rename |
| Local checkout folder `ai-modernization-factory` | Filesystem path until you rename the GitHub repo / clone directory |
| Shell env `AIMF_*` if still exported | Clear or re-export as `CODESTRATA_*` in your shell profile |

No `aimf` Python package, CLI entry point, or config filename remains in source.

## Public CLI after rename

```bash
codestrata --help
codestrata version
codestrata onboard <repository>
codestrata report validate <report.json>
codestrata repository answer <repository> "<question>"
codestrata mcp serve
codestrata mcp health
codestrata acceptance run
codestrata release check
```

The legacy `aimf` entry point is removed.

Opening an existing `.codestrata/knowledge` (formerly `.aimf/knowledge`) database
applies schema migration **v3**, which renames `aimf_version` →
`codestrata_version`. If migration is undesirable, delete
`.codestrata/knowledge` and re-onboard.

## Manual GitHub repository rename

Do **not** automate the remote rename. After merging this work:

1. On GitHub: **Settings → General → Repository name** → set to `codestrata`.
2. Update local remotes:

```bash
git remote -v
git remote set-url origin git@github.com:sknampally/codestrata.git
# or HTTPS:
# git remote set-url origin https://github.com/sknampally/codestrata.git
```

3. Optionally rename the local clone directory:

```bash
cd ..
mv ai-modernization-factory codestrata
cd codestrata
```

4. Reinstall editable:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[development]'
codestrata version
```

PyPI project URLs in `pyproject.toml` already point at
`https://github.com/sknampally/codestrata` (update after the GitHub rename
succeeds).
