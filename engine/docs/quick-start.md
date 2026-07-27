# Quick Start

Get from zero to a modernization report in under five minutes.

## Prerequisites

* Python **3.12+**
* Git (for GitHub URL acquisition)

## Canonical install (Community Engine)

From a published package (when available):

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install codestrata
codestrata version
```

From a `codestrata-engine` checkout (or monorepo `engine/`):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
codestrata version
```

> Monorepo contributors: install from `./engine`, not the repository root
> workspace package.

## Assess in three commands

```bash
codestrata init
codestrata doctor
codestrata assess --repo . --output reports --no-ai
```

Or assess the bundled sample (Engine checkout with fixtures):

```bash
codestrata assess --repo test-fixtures/sample-js-app --output reports --no-ai
```

Open the newest `reports/<repo>/<timestamp>/report.html`.

## CI (optional)

Copy [examples/github-actions/codestrata-assess.yml](../examples/github-actions/codestrata-assess.yml)
into your app’s `.github/workflows/`. It runs a deterministic assess with
`--quiet --json-summary` and uploads report artifacts.

## Useful flags

| Flag | Purpose |
| ---- | ------- |
| `--no-ai` | Deterministic only (default; no cloud provider) |
| `--with-ai` | Optional Modernization Advisor |
| `--quiet` | Suppress stage progress |
| `--json-summary` | Machine-readable completion JSON on stdout |

```bash
codestrata assess --repo . --output reports --no-ai --quiet --json-summary
```

## Next steps

* `codestrata examples` — official samples and doc links
* [installation.md](installation.md) · [cli-reference.md](cli-reference.md)
* [report-interpretation.md](report-interpretation.md)
* [troubleshooting.md](troubleshooting.md)

Legacy/advanced: `codestrata scan` (prefer `assess`).
