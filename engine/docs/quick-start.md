# Quick Start

Get from zero to a modernization report in a few minutes.

For a full walkthrough (install → scan → report → findings → MCP), see
[tutorial.md](tutorial.md).

## Prerequisites

* Python **3.12+**
* Git
* A local clone of CodeStrata (or an installed wheel)

## 1. Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
codestrata version
```

Details: [installation.md](installation.md).

## 2. Assess a sample repository

Default `codestrata.toml` points at `test-fixtures/sample-js-app`:

```bash
codestrata config validate --config codestrata.toml
codestrata assess --config codestrata.toml --output reports
```

Or assess any sample directly:

```bash
codestrata assess --repo test-fixtures/sample-js-app --output reports
codestrata assess --repo test-fixtures/sample-python-app --output reports
codestrata assess --repo test-fixtures/sample-java-app --output reports
codestrata assess --repo test-fixtures/sample-php-app --output reports
codestrata assess --repo test-fixtures/sample-csharp-app --output reports
```

## 3. Open the report

Each run writes:

```text
reports/<repo-name>/<YYYYMMDD-HHMMSS>/
  report.html
  report.json
  findings.json
  recommendations.json
  graphs/
```

Open `report.html` in a browser. How to read it:
[report-interpretation.md](report-interpretation.md).

## 4. Optional next steps

```bash
# Show active execution profile (no secrets)
codestrata config profile --config codestrata.toml

# Enable MCP (edit [mcp].enabled = true), then:
codestrata mcp tools --config codestrata.toml
codestrata mcp health --config codestrata.toml
```

MCP guide: [mcp/setup.md](mcp/setup.md). Profiles:
[configuration-profiles.md](configuration-profiles.md).

## If something fails

* Missing package → [installation.md](installation.md)
* Config errors → [configuration-profiles.md](configuration-profiles.md)
* General symptoms → [troubleshooting.md](troubleshooting.md)
