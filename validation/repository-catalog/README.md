# Permanent repository catalog

Single source of truth for repository-based System Verification:

`validation/repository-catalog/catalog.json`

No alternate repository list is authoritative for SV.4 / SV.6 / SV.10.

This catalog is a curated CodeStrata verification dataset. Its results describe
only the included pinned repositories and are not a product-wide accuracy or
industry benchmark claim.

## Ownership

- **Owner:** CodeStrata release / System Verification maintainers
- **Path:** `validation/repository-catalog/catalog.json` (canonical)
- **Schema:** `codestrata-repository-catalog` / `1.0.0`
- **v0.2.0 release-validation target:** exactly **22** curated repositories

The catalog may expand to **30 or more** repositories in later releases. Do not
invent repositories to force expansion during v0.2.0.

**HiveMind retirement:** `moqui/HiveMind` was removed from the v0.2.0
release-validation set because its primary language is Groovy (unsupported).
Groovy must not be relabeled as Java merely to pass validation.

**BookStack replacement:** `BookStackApp/BookStack` is the release-owner-approved
v0.2.0 replacement. It reuses the proven immutable pin from
`validation/php-bookstack.toml` / Epic 4 `remote-php-bookstack`
(`4e406c41c4c8060a5795e74c66fb96362e54f400`).

SV.10 (multi-repository validation) must not start until the SV.10A readiness
gate passes. SV.11 is out of scope for catalog readiness.

## Qualification criteria

An entry is **qualified** only when:

- public HTTPS GitHub URL (no SSH, no credentials)
- supported `language_group` (`C#/.NET`, `Java`, `JS/TS`, `PHP`, `Python`)
- license and visibility recorded
- `qualified_revision` is a full immutable commit pin
- roles and `expected_runtime_tier` are explicit

Distinctions preserved:

| State | Meaning |
| --- | --- |
| `qualification_status=qualified` | Supported language + full commit pin + metadata |
| `qualification_status=unqualified` | Not yet safely pinned / incomplete |
| `qualification_status=blocked` | Present in the curated 22 but unsafe for SV.10 (example: unsupported language) |
| `enabled_for.release_validation` | Explicit SV.10 enablement; never auto-enabled for unqualified/blocked entries |

Do **not** add Go, Rust, Ruby, Groovy, or other unsupported languages merely for
diversity. Do not invent repositories.

v0.2.0 PASS requires all 22 curated entries to be qualified, supported, fully
pinned, and `release_validation`-enabled. If any entry cannot be safely
qualified, readiness remains **BLOCKED** and the curated target stays 22 (the
run is not silently reduced).

## Revision pinning

`qualified_revision` must be either `null` or:

```json
{
  "type": "commit",
  "value": "<full 40-character lowercase commit SHA>",
  "source_tag": "<optional informational tag>"
}
```

Rejected for SV.10-enabled entries: `null`, floating names (`main`, `master`,
`HEAD`, `latest`), abbreviated SHAs, tag-only authority, SSH URLs,
credential-bearing URLs. When `source_tag` names an annotated tag, store the
**peeled commit SHA**, not the tag-object SHA.

## Roles and tiers

Roles (`enabled_for`):

| Role | Purpose |
| --- | --- |
| `smoke` | Tier 1 routine smoke |
| `regression` | Regular regression |
| `engineering_intelligence` | EI / report pipelines (SV.6) |
| `performance` | Larger / slower repositories |
| `release_validation` | SV.10 release dataset (requires full commit pin) |

Tiers (`expected_runtime_tier`):

| Tier | Use |
| --- | --- |
| `tier1` | Small / fast — routine smoke |
| `tier2` | Medium — regular regression |
| `tier3` | Larger real-world — intelligence / release |
| `tier4` | Slow / very large — explicitly scheduled only |

Do not run Tier 4 by default in local developer loops. SV.10 must support tier
filtering.

## Execution batches (SV.10 plan only)

Deterministic batches are emitted by the readiness report (not executed in
SV.10A):

1. Batch 1 — Tier 1 fast
2. Batch 2 — Tier 2 regression
3. Batch 3 — Tier 3 intelligence / release
4. Batch 4 — Tier 4 scheduled slow

Later assessments use:

```bash
codestrata assess --repo . --output reports --no-ai
```

Clone outside the CodeStrata source tree. Cache by catalog id + commit SHA.
Delete temporary clones after each repository. Do not initialize submodules or
download Git LFS unless explicitly approved.

## Validate / reports

```bash
python validation/repository-catalog/validate_catalog.py
python validation/repository-catalog/validate_catalog.py --write-report
python validation/repository-catalog/validate_catalog.py --write-readiness-report --write-import-template
```

Generated (gitignored):

- `qualification-report.json`
- `repository-catalog-readiness.json`

## Smoke-selection policy (SV.4)

1. `enabled_for.smoke == true`
2. `qualified_revision` present
3. Prefer `Small`
4. Prefer supported language groups
5. Lexicographically smallest `id`

## How to add a repository

1. Obtain release-owner approval (do not invent candidates).
2. For post-v0.2.0 expansion toward 30+, update `release_validation_target`
   only when the release owner explicitly changes it.
3. Add the entry to `catalog.json` only (never a second list).
4. Qualify a full commit SHA; optional `source_tag` is informational.
5. Set roles/tier; enable `release_validation` only after the pin is verified
   for a supported language.
6. Run `validate_catalog.py --write-readiness-report`.

## How to retire or replace a repository

1. Set `enabled_for.release_validation` (and other roles) to `false`, or remove
   the entry after release-owner approval.
2. Record the reason in `limitations`.
3. If replacing, import the replacement through the same qualification process;
   do not leave floating revisions.
4. Re-run the readiness gate. For v0.2.0 keep target at 22 unless the release
   owner explicitly changes `release_validation_target`.

## Relationship to SV.10 and SV.11

| Slice | Relationship |
| --- | --- |
| SV.10A / SV.10B | Catalog qualification + BookStack replacement; must PASS first |
| SV.10 | Full multi-repository assessment of the 22 curated repositories |
| SV.12 | Engineering Intelligence quality review of one 22-repo EIR (SV.10 inputs) |
| SV.13 | Defect remediation |

SV.10 / SV.11 / SV.12 commands:

```bash
cd engine
python -m verification.curated_repository_validation --tier tier1
python -m verification.curated_repository_validation --all
python -m verification.assessment_consistency

PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.engineering_intelligence_quality
```

## Tracking

`validation/repository-catalog/` is the only re-included tree under the
repo-root `/validation/*` gitignore. Generated qualification / readiness
reports remain ignored — regenerate with `validate_catalog.py`.
