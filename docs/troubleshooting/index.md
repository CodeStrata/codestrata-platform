---
title: Troubleshooting
description: Common CodeStrata Engine and extension issues and how to resolve them.
---

# Troubleshooting

## `codestrata: command not found`

- Confirm install completed
- Ensure the install location is on `PATH`
- Or activate the virtualenv where Engine was installed
- Re-run `codestrata version`

## Extension cannot find Engine

1. Run **Check CodeStrata Environment**
2. Set `codestrata.engine.executable` to an absolute path if needed
3. Run `codestrata doctor` in a terminal

## Assessment fails early

```bash
codestrata doctor
codestrata assess --repo . --output reports --no-ai
```

Inspect the Output channel (IDE) or CLI stderr.

## AI failures

```bash
codestrata ai
codestrata ai doctor
```

- Confirm you intended `--with-ai`
- Verify provider extras (`codestrata[bedrock]` / `codestrata[openai]`) and credentials in **Engine** config
- Typical doctor messages: AWS credentials missing, `OPENAI_API_KEY` missing, unsupported provider
- Fall back to `--no-ai` for deterministic results
- Full guide: [AI Providers](/ai-providers/)

## Report missing

Confirm the output directory and timestamp folder under `reports/`.

## Telemetry / privacy FAQ

| Question | Answer |
| --- | --- |
| Is telemetry on by default? | No |
| How do I enable it? | Answer **y** at the first-run prompt, or `codestrata telemetry enable` |
| How do I disable it? | `codestrata telemetry disable` or `CODESTRATA_TELEMETRY=0` |
| How do I inspect payloads? | `codestrata telemetry show` |
| How do I reset the anonymous id? | `codestrata telemetry reset` |
| Does offline telemetry block assess? | No — events queue locally |

Details: [Privacy](/security/privacy).
