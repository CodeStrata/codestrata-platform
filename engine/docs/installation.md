# Installation Guide

Install CodeStrata for local development or day-to-day assessment use.

## Requirements

| Requirement | Notes |
| ----------- | ----- |
| Python 3.12+ | Required |
| Git | Required for GitHub clones (`codestrata scan`) |
| AWS credentials | Only for `assess --with-ai` / Bedrock knowledge providers |
| OpenAI API key | Only for `profile = "openai"` knowledge providers |
| Optional extras | `bedrock`, `openai`, `mcp`, `dev` |

## Clone and editable install (recommended)

```bash
git clone https://github.com/sknampally/codestrata.git
cd codestrata

python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

Verify:

```bash
codestrata version
codestrata about
```

If you see `ModuleNotFoundError: No module named 'codestrata'`, the package is
not installed in the active environment. Activate `.venv` and re-run
`python -m pip install -e .`.

## Optional extras

```bash
# Tests + linters
python -m pip install -e ".[dev]"

# Amazon Bedrock (AI enrichment / Bedrock knowledge providers)
python -m pip install -e ".[bedrock]"

# OpenAI knowledge providers
python -m pip install -e ".[openai]"

# FastMCP server
python -m pip install -e ".[mcp]"

# Everything commonly needed for contributors
python -m pip install -e ".[dev,bedrock,openai,mcp]"
```

Missing optional dependencies produce actionable CLI errors (for example MCP
commands print the `pip install 'codestrata[mcp]'` hint and exit `1`).

## Environment file

Copy `.env.example` to `.env` for local overrides. Shell environment variables
always win over `.env`. Never commit real secrets.

```bash
cp .env.example .env
```

Common variables: `CODESTRATA_PROFILE`, `AWS_PROFILE`, `AWS_REGION`,
`OPENAI_API_KEY`, `CODESTRATA_GITHUB_TOKEN`. See
[configuration-profiles.md](configuration-profiles.md).

## First configuration

A starter `codestrata.toml` ships in the repository root. Minimum required:

```toml
profile = "community"

[repository]
path = "examples/sample-js-app"
```

Validate:

```bash
codestrata config validate --config codestrata.toml
```

## Quality gates (contributors)

```bash
pytest
ruff check .
ruff format --check .
mypy src
```

See [contributor-guide.md](contributor-guide.md).

## Uninstall

```bash
python -m pip uninstall codestrata
```

Remove the virtualenv directory (`.venv`) if you created one.
