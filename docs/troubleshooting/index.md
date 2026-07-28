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

- Confirm you intended `--with-ai`
- Verify provider extras and credentials in **Engine** config
- Fall back to `--no-ai` for deterministic results

## Report missing

Confirm the output directory and timestamp folder under `reports/`.
