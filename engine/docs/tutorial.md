# End-to-end tutorial

Minimal path: **install → assess → inspect findings → try MCP**.

Assumes you are in the CodeStrata repository root with network available only
for `pip` (assessment of local examples needs no cloud).

## 1. Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,mcp]"
codestrata version
```

## 2. Validate configuration

```bash
codestrata config validate --config codestrata.toml
codestrata config profile --config codestrata.toml
```

Expected: profile `community` (or whatever you set), `"ok": true`.

## 3. Assess a sample repository

```bash
codestrata assess --repo examples/sample-js-app --output reports --no-ai
```

Wait for `Modernization assessment completed` and note the run directory under
`reports/sample-js-app/<timestamp>/`.

## 4. Inspect findings and the HTML report

```bash
ls reports/sample-js-app/
# open the newest report.html in a browser
```

Inspect machine-readable findings:

```bash
python - <<'PY'
from pathlib import Path
import json
paths = sorted(Path("reports/sample-js-app").glob("*/findings.json"))
assert paths, "no findings.json — did assess succeed?"
data = json.loads(paths[-1].read_text(encoding="utf-8"))
findings = data.get("findings") or data
print(f"run={paths[-1].parent.name} findings={len(findings)}")
PY
```

Reading guide: [report-interpretation.md](report-interpretation.md).

## 5. Optional — enable MCP and list tools

Edit `codestrata.toml`:

```toml
[mcp]
enabled = true
```

Then:

```bash
codestrata mcp tools --config codestrata.toml
codestrata mcp health --config codestrata.toml
```

To serve (stdio; typically launched by an MCP client):

```bash
codestrata mcp serve --config codestrata.toml
```

Setup details: [mcp/setup.md](mcp/setup.md).

## 6. Try another language sample

```bash
codestrata assess --repo examples/sample-python-app --output reports --no-ai
codestrata assess --repo examples/sample-java-app --output reports --no-ai
codestrata assess --repo examples/sample-php-app --output reports --no-ai
codestrata assess --repo examples/sample-csharp-app --output reports --no-ai
```

## Done

You now have deterministic reports, inspected findings, and (optionally) a
working MCP surface. Next:

* [configuration-profiles.md](configuration-profiles.md)
* [cli-reference.md](cli-reference.md)
* [architecture-guide.md](architecture-guide.md)
