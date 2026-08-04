"""SV.12 — Engineering Intelligence Quality Review

Verification-only package. Builds one 22-repository Engineering Intelligence
Report from preserved SV.10 assessments (via SV.6 pipeline builders) and
website-safe export (via SV.8), then reviews commercial usefulness, credibility,
provenance, wording, and safety.

## Scope

- Catalog: `validation/repository-catalog/catalog.json` (22 release_validation)
- Inputs: `engine/reports/verification/sv10/` + SV.11 consistency gate
- Does **not** clone or reassess by default
- Does **not** overwrite `platform/demo/`
- After SV.13: expects **22/22** population (no `unsafe_metadata` exclusions)
- Does **not** start SV.14
- Not an industry benchmark or product-wide accuracy claim

## Command

```bash
PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.engineering_intelligence_quality
```

No network required when SV.10 artifacts are present.

## Outputs (gitignored)

```
platform/reports/verification/sv12/
  engineering-intelligence-report.json
  engineering-intelligence-report.html
  export-manifest.json
  engineering-intelligence-quality-review.json
  engineering-intelligence-quality-review.md
```

## Intended audiences

- CTO / VP Engineering
- Engineering Council reviewer
- PE technology diligence team
- CodeStrata design partner

## Relationship

| Slice | Role |
| --- | --- |
| SV.10 | 22 pinned assessments |
| SV.11 | Contract consistency + EI input readiness |
| SV.12 | This quality / editorial review |
| SV.13 | Defect remediation (not started here) |
