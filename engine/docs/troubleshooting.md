# Troubleshooting Guide

Actionable fixes for common CodeStrata failures. MCP-specific symptoms also
appear in [mcp/troubleshooting.md](mcp/troubleshooting.md).

## Installation and environment

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| `ModuleNotFoundError: No module named 'codestrata'` | Package not installed in active interpreter | Activate `.venv`, run `python -m pip install -e .` ([installation.md](installation.md)) |
| `codestrata: command not found` | Scripts dir not on `PATH` | Activate venv or run `python -m codestrata` if exposed |
| Wrong Python version | < 3.12 | Install Python 3.12+ and recreate the venv |
| Optional import / MCP missing | Extra not installed | `pip install 'codestrata[mcp]'` (or `bedrock` / `openai`) |

## Configuration

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| `Configuration file does not exist` | Missing `codestrata.toml` | Create one (see README) or pass `--config /path/to/codestrata.toml` |
| `Unknown execution profile` | Typo in `profile` | Use `community`, `local`, `enterprise`, `bedrock`, or `openai` |
| Bedrock profile requires AWS region | No region configured | Set `[aws].region` / `[ai.bedrock].region` or `AWS_REGION` |
| OpenAI profile / missing API key (`--strict`) | Env var empty | Export the name in `[ai.openai].api_key_env` (never put the secret in TOML) |
| `local` profile rejects `--with-ai` | No external LLM profile | Use `--profile bedrock` or omit `--with-ai` |

Validate:

```bash
codestrata config validate --config codestrata.toml
codestrata config effective --config codestrata.toml
```

Guide: [configuration-profiles.md](configuration-profiles.md).

## Assess / scan

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| Repository path/URL required | No `--repo` and empty `[repository]` | Pass `--repo` or set `path` / `url` in TOML |
| GitHub clone auth failed | Missing token / SSH | Set `CODESTRATA_GITHUB_TOKEN` or SSH agent; see [examples/README.md](../../examples/README.md) |
| `--model-id requires --with-ai` | Usage error | Add `--with-ai` or drop `--model-id` (exit code `2`) |
| PMD / static analysis errors | PMD missing or misconfigured | Install PMD or `--no-static-analysis` / disable in TOML |
| Long runtime on large repos | Inventory + rules cost | See [runtime-performance.md](runtime-performance.md) limits |

## Reports

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| No `report.html` | Assess failed earlier | Re-run with `--verbose`; check stderr `Fix:` lines |
| Empty / sparse findings | Tiny sample or packs disabled | Try another example; enable rule packs intentionally |
| AI section missing | Deterministic mode | Expected without `--with-ai` |

Interpretation: [report-interpretation.md](report-interpretation.md).

## MCP

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| MCP disabled | `[mcp].enabled = false` | Set `enabled = true` and restart |
| Extra missing | No mcp install | `pip install 'codestrata[mcp]'` |
| Health / tool failures | Knowledge gates off | Enable retrieval/answering as needed |

Full table: [mcp/troubleshooting.md](mcp/troubleshooting.md).

## Exit codes

* `0` — success  
* `1` — blocked / config / operational failure  
* `2` — usage or hard error (command family–specific)

## Still stuck?

1. Capture `codestrata version` and the exact command.
2. Re-run with `--verbose` when available.
3. Confirm `codestrata config effective` shows the intended profile (no secrets).
4. Search open issues or open a new one with sanitized logs (no tokens).
