# Report Interpretation Guide

How to read CodeStrata HTML and JSON assessment outputs.

## Where files land

```text
reports/<repository-name>/<YYYYMMDD-HHMMSS>/
  report.html              # Human-readable HTML Report v2
  report.json              # Machine-readable assessment document
  findings.json            # Deterministic findings
  recommendations.json     # Deterministic recommendations
  graphs/                  # Repository + assessment graphs
  ai-enrichment.json       # Present only after successful --with-ai
  dependency-evidence.json # When dependency evidence ran
  …
```

## Start with the HTML report

Open `report.html` in a browser (self-contained; no CDN).

Typical reading order:

1. **Executive overview** — repository identity, mode (deterministic vs AI),
   high-level posture.
2. **Technologies** — detected languages, frameworks, and build systems.
3. **Findings** — deterministic issues with severity and evidence.
4. **Recommendations** — actionable next steps linked to findings.
5. **Domain sections** (when enabled) — architecture, technical debt,
   dependency, security, testing, cloud, AI readiness, performance.
6. **AI narrative** (AI mode only) — interpretive text; must not invent new
   findings.

Generation details: [report-generation.md](report-generation.md).

## Findings vs recommendations

| Artifact | Meaning |
| -------- | ------- |
| Finding | Observed issue or risk backed by evidence |
| Recommendation | Suggested remediation or modernization step |
| AI enrichment | Optional prose summarizing deterministic results |

If HTML and JSON disagree, trust **`findings.json` / `recommendations.json`**
and `report.json` — they are the contract
([report-contract.md](report-contract.md)).

## Severity and priority

Findings carry severity (for example `critical` / `high` / `medium` / `low` /
`info`). Recommendations may include effort/risk/priority fields. Treat these
as prioritization aids for engineering planning, not as automated remediation.

## Deterministic vs AI mode

| Mode | Flag | Provider calls | Enrichment file |
| ---- | ---- | -------------- | --------------- |
| Deterministic | `--no-ai` (default) | 0 | absent |
| AI-enhanced | `--with-ai` | exactly 1 (Bedrock) | `ai-enrichment.json` on success |

AI enrichment is **interpretive only**. It must not invent findings IDs or
recommendations that are absent from deterministic artifacts.

## Inspecting JSON quickly

```bash
# Latest run directory (example)
ls reports/sample-js-app/

# Count findings
python -c "import json,pathlib; p=sorted(pathlib.Path('reports').rglob('findings.json'))[-1]; print(len(json.load(p.open())['findings']))"

# Validate report contract
codestrata report validate --path reports/sample-js-app/<timestamp>/report.json
```

## Common questions

**Why are there few findings on a tiny sample?**  
Samples are intentionally small. Dogfood repos under `.codestrata/workspace/`
exercise denser evidence.

**Why is a domain section missing?**  
Many assessment/report sections are feature-gated and disabled by default.
Check `codestrata.toml` / `codestrata config effective`.

**Why is PMD absent?**  
PMD is Java-oriented and optional (`[static_analysis]`). Non-Java samples keep
it off.

## Related

* [quick-start.md](quick-start.md)
* [tutorial.md](tutorial.md)
* [capabilities.md](capabilities.md)
