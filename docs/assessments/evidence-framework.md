---
title: Evidence Plans and Evidence Studio
description: Define, preview, collect, normalize, assess, and report repository evidence locally.
---

# Evidence Plans and Evidence Studio

The evidence workflow separates four concerns that are easy to conflate:

1. **Plan and collect** what the user actually wants to observe.
2. **Normalize and preserve** observations, provenance, coverage, and raw tool output.
3. **Assess** explicit claims with a versioned profile.
4. **Report** findings, risks, actions, limitations, and traceability for an audience.

The existing `codestrata assess` command remains the 0.2.0 Engineering
Assessment workflow. The isolated evidence workflow is additive.

## Visual local workflow

```bash
codestrata evidence studio --repo .
```

The Studio binds to loopback, uses a per-process token, and requires a review
confirmation before a plan runs. It shows repository reads, local executables,
possible off-machine access, applicability, and blind spots. No account or
hosted service is required.

The first screen also accepts a credential-free public GitHub HTTPS URL and an
optional branch or tag. CodeStrata creates a shallow, immutable snapshot in its
managed per-user cache, pins the evidence plan to the resolved commit, and then
uses the same evidence-selection flow as a local folder. Repository hooks,
submodules, Git LFS downloads, and repository code are not executed during
acquisition. Private-repository authentication is not part of this initial
boundary.

The guided editor supports:

- repository-aware evidence packs for a baseline, language structure, code
  health, security/quality imports, or a composed decision-ready review;
- detected-language selection for the existing Python, Java,
  JavaScript/TypeScript, PHP, and C# providers, with individual provider
  capabilities exposed as checkboxes;
- six transparent structural-health biomarkers with user-editable thresholds,
  plus file-level measurements for additional detected languages;
- optional RepoWise JSON enrichment when the separately installed executable
  is available; CodeStrata never auto-installs or silently substitutes it;
- inventory, dependency-declaration, and testing-structure observations;
- user-defined bounded file-pattern observations without storing matching text;
- SARIF 2.1 imports from existing analyzers and meta-frameworks;
- an optional user-installed Trivy adapter, blocked unless external access is
  explicitly allowed and its native SARIF output can be retained locally; and
- a JSON-Schema advanced editor for the complete contract.

## Portable CLI workflow

```bash
codestrata evidence init --repo . --output evidence-plan.yaml \
  --goal "What evidence supports this modernization decision?"
codestrata evidence preview --plan evidence-plan.yaml
codestrata evidence run --plan evidence-plan.yaml --output .codestrata-artifacts
```

Edit and version `evidence-plan.yaml` like any other reviewable configuration.
The default plan runs built-in read-only collectors and denies external access.

## Artifact contract

Each completed or partial run is promoted atomically under:

```text
.codestrata-artifacts/evidence/<repository>/<run>/
├── plan.yaml
├── run.json
├── evidence.jsonl
├── coverage.json
├── assessment.json
├── report.html
├── report.sarif
└── raw/sha256/
```

`evidence.jsonl` is the canonical normalized ledger. Evidence IDs are derived
from the repository revision, collector identity and version, evidence kind,
sanitized payload, and locations; collection time and run ID do not change the
identity. Raw imported artifacts are content-addressed with SHA-256.

## Interpretation boundary

The first profile, `repository-evidence-baseline@1.0`, answers whether requested
evidence was collected with declared coverage. It deliberately does **not**
infer modernization readiness, runtime behavior, test passage, exploitability,
or compliance from repository presence.

Consequently, its report distinguishes:

- supported collection claims;
- partial, failed, unavailable, or not-applicable collection;
- the user's decision question as **not assessed** until a matching profile is
  selected; and
- a guiding action to add that decision-specific profile.

This is a trust boundary, not a missing-data shortcut. “No finding” is never
reported as “clean” unless the producing activity declared complete coverage
and the assessment profile defines what that absence means.

The optional `engineering-health-review@1.0` head interprets selected
structural biomarkers and imported analyzer findings. It creates source-linked
findings, risks, prioritized actions, and re-run verification steps while
keeping measurements and producer findings separate from assessment judgment.
The report records the selected pack, every capability or biomarker override,
and the threshold used; it does not calculate a universal repository score.

## Tool strategy

SARIF is the main leverage seam. Output from CodeQL, Trivy, Gitleaks, MegaLinter,
Super-Linter, and compatible pre-commit hooks can be normalized without making
their execution models part of CodeStrata. External tools remain separately
installed, explicitly selected, and visible in preview. Their own licenses,
rules, databases, network behavior, and transitive dependencies remain distinct
from CodeStrata's contracts.

## Safety defaults

- Repository symlinks are not followed by built-in collectors.
- Relative SARIF imports cannot escape the selected repository.
- Recognized secrets are redacted from normalized payloads.
- Source snippet fields are not stored by default.
- Imported raw artifacts are local, content-addressed, and disclosed in preview.
- The Studio rejects non-loopback binding and uses CSP, no-store, no-referrer,
  and content-type hardening headers.

The normalized report is useful without AI. AI enrichment is not part of this
evidence baseline.
