# CLI Reference

Primary commands for CodeStrata. Run `codestrata COMMAND --help` for full
options. Global: `codestrata --help`, `codestrata version`, `codestrata about`.

## Exit codes

| Code | Meaning |
| ---- | ------- |
| `0` | Success |
| `1` | Blocked / validation failure / expected operational failure |
| `2` | Usage error or unexpected error (command-specific; agent/enterprise/incremental use `2` for hard errors) |

Config and assess usage mistakes (for example `--model-id` without `--with-ai`)
exit `2`. Missing config files and most load failures exit `1` with a `Fix:`
hint.

## Core workflow

| Command | Purpose |
| ------- | ------- |
| `codestrata assess` | Full modernization assessment → HTML/JSON reports |
| `codestrata scan` | Clone + analyze the GitHub URL in `codestrata.toml` |
| `codestrata onboard` | Onboard a repository into the knowledge store |
| `codestrata config profile` | Show active execution profile |
| `codestrata config validate` | Validate configuration / profile compatibility |
| `codestrata config effective` | Show effective non-secret settings |
| `codestrata config show` | Alias for `effective` |

### Assess (canonical)

```bash
codestrata assess --config codestrata.toml --output reports
codestrata assess --repo test-fixtures/sample-js-app --output reports --no-ai
codestrata assess --config codestrata.toml --profile local --output reports
codestrata assess --config codestrata.toml --output reports --with-ai
```

Important options:

* `--repo` / `-r` — local path or GitHub URL (overrides config)
* `--output` / `-o` — report root directory (default `reports`)
* `--with-ai` / `--no-ai` — AI enrichment (default `--no-ai`)
* `--profile` / `-p` — execution profile override
* `--config` / `-c` — path to `codestrata.toml`
* `--model-id` — Bedrock model (requires `--with-ai`)

### Config

```bash
codestrata config profile --config codestrata.toml
codestrata config validate --config codestrata.toml --profile bedrock
codestrata config effective --config codestrata.toml
```

See [configuration-profiles.md](configuration-profiles.md).

## Knowledge and MCP

| Command | Purpose |
| ------- | ------- |
| `codestrata repository search` | Grounded retrieval |
| `codestrata repository answer` | Grounded answering |
| `codestrata mcp serve` | Start FastMCP server |
| `codestrata mcp tools` | List tools |
| `codestrata mcp health` | Sanitized health (no secrets) |

Requires `[mcp].enabled = true` and usually `pip install 'codestrata[mcp]'`.
Guide: [mcp/setup.md](mcp/setup.md).

## AI providers

| Command | Purpose |
| ------- | ------- |
| `codestrata ai providers` | List embedding/answer providers |
| `codestrata ai config` | Show AI settings (no secrets) |
| `codestrata ai health` | Config / optional live health |

## Analysis intelligence helpers

| Command group | Purpose |
| ------------- | ------- |
| `codestrata rules` | Shared Rule Platform discovery |
| `codestrata evidence` | Language evidence providers |
| `codestrata architecture` | Architecture conclusions / assessment / report helpers |
| `codestrata report validate` | Validate report contract JSON |

## Platform / ops

| Command group | Purpose |
| ------------- | ------- |
| `codestrata agent` | Agent Framework workflows |
| `codestrata incremental` | Incremental assessment (opt-in) |
| `codestrata enterprise` | Enterprise Knowledge Graph |
| `codestrata roadmap` | Modernization roadmap helpers |
| `codestrata acceptance` | MVP acceptance harness |
| `codestrata release` | Release readiness helpers |

## First-run tips

1. Prefer `codestrata assess --repo …` before editing a large `codestrata.toml`.
2. Run `codestrata config validate` after changing profiles or AI providers.
3. Keep secrets in the environment (`.env`), never in TOML values.
4. When a command fails, read the `Fix:` line in the error message.

Troubleshooting: [troubleshooting.md](troubleshooting.md).
