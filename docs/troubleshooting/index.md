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
codestrata assess --repo . --no-ai
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

Confirm
`.codestrata-artifacts/assessments/<repository-id>/current/`
(and `previous/` if you expected an earlier successful run).

## Telemetry / privacy FAQ

| Question | Answer |
| --- | --- |
| Is telemetry on by default? | No |
| How do I allow it for assess? | `codestrata assess --telemetry-allow`, or answer **y** at an eligible interactive prompt (default **N**) |
| How do I deny it for assess? | `codestrata assess --telemetry-deny` (non-interactive runs never prompt) |
| Do legacy enable/disable authorize assess? | No — `codestrata telemetry enable\|disable` is compatibility-only |
| Does telemetry opt-in publish reports? | No — publish requires an explicit confirm action |
| Does telemetry failure block assess? | No |

Details: [Privacy](/security/privacy).
