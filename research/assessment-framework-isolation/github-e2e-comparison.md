# GitHub end-to-end comparison: CodeStrata 0.2.0 and isolated evidence flow

Date: 2026-08-12  
Baseline engine: `15fcc99cb6edaf7c1c5bf5b7f36a343aefdcbd8e` (`0.2.0`)  
New branch: `codex/assessment-framework-isolation`  
Mode: local deterministic execution; AI, telemetry, and external static analysis disabled

## Pinned subjects

| Repository | Language | Revision |
|---|---|---|
| `nikic/FastRoute` | PHP | `1c961398bef1ff6ecd8b273bef651d7afe90312b` |
| `pallets/markupsafe` | Python/C | `b2e4d9c7687be25695fffbe93a37622302b24fb1` |
| `sindresorhus/slugify` | JavaScript | `7c318bd1aa4b4affab29761f15a9604323fe2a3b` |

Each repository was shallow-cloned, pinned by the recorded commit, and run from
the same local checkout. The baseline command imported source from a clean
archive of the 0.2.0 commit. The compatibility command used the current branch.

## Observed results

| Repository | 0.2.0 findings | 0.2.0 recommendations | New evidence activities | New evidence records | New claim outcomes | New findings/actions |
|---|---:|---:|---:|---:|---|---:|
| FastRoute | 8 | 3 | 3/3 completed | 3 | 2 supported; 1 partial; 1 not assessed | 2/2 |
| MarkupSafe | 13 | 2 | 3/3 completed | 3 | 2 supported; 1 partial; 1 not assessed | 2/2 |
| slugify | 9 | 6 | 3/3 completed | 3 | 2 supported; 1 partial; 1 not assessed | 2/2 |

The counts are intentionally **not equivalent metrics**. The 0.2.0 workflow
applies its fixed domain heads and emits engineering findings and
recommendations. The isolated baseline asks whether the user-requested evidence
was collected with sufficient coverage; it refuses to treat that collection as
an answer to “modernization readiness.” Its one default finding/action says the
decision is not assessed and directs the user to a decision-specific profile.

## Compatibility result

The current branch's unchanged `codestrata assess` flow was run against all
three pinned repositories. Compared with the clean 0.2.0 source archive:

- `findings.json`: byte-identical on 3/3 repositories;
- `recommendations.json`: byte-identical on 3/3;
- `dependency-evidence.json`: byte-identical on 3/3; and
- repository testing evidence: byte-identical wherever the artifact was
  applicable (FastRoute and MarkupSafe; neither run emitted it for slugify).

This establishes that the new framework is additive rather than a silent
rewrite of the 0.2.0 assessment path.

## User-defined evidence result

Dependency evidence was partial in all three final runs because each repository
contained at least one recognized lockfile or ecosystem manifest that the reused
0.2.0 typed parser does not support. The report preserves the parsed evidence
and names the unsupported artifacts instead of turning an empty parser result
into “no dependencies.”

The slugify plan was edited to add this observation:

```yaml
- activity_id: transliteration-observation
  collector_id: codestrata.file-pattern
  configuration:
    patterns:
      - id: transliteration-code
        regex: '\btransliterate\b'
        globs: ['*.js']
```

Preview reported four applicable local-only activities and no execution or
off-machine transfer. The run completed with 23 normalized records, three
findings, and three actions: the three baseline envelopes, one search summary,
and 19 source locations. No matching source text was stored. The custom action
asks the user to review and disposition the 19 locations without assigning an
inherent quality meaning to the text pattern. (The custom activity's 20 records
are the summary plus 19 occurrences.)

## Determinism result

Each default plan was run twice. After sorting the evidence IDs, both runs were
identical for 3/3 repositories. Run IDs and timestamps changed, as expected;
evidence identity did not.

## What materially changed

| Concern | 0.2.0 assessment | Isolated evidence flow |
|---|---|---|
| Initiation | Fixed assessment command/config | Goal-first Studio or versioned YAML plan |
| Evidence choice | Implicit in assessment heads/settings | Explicit collector activities, imports, scope, limits, and sensitivity |
| Preflight | No unified per-activity permission preview | Reads, executables, external access, applicability, and blind spots before run |
| Evidence shape | Several domain-specific artifacts | Versioned generic envelope around typed native payloads plus raw hashes |
| Coverage | Present in selected domain artifacts | Mandatory per activity and per envelope; absence requires complete coverage |
| Assessment | Fixed heads mixed into the workflow | Separate versioned profile registry consuming only normalized evidence |
| Unknowns | Varies by head | First-class partial, insufficient, not assessed, not applicable, and failed states |
| Reporting | Engineering Assessment HTML/JSON | Canonical assessment JSON, evidence JSONL, coverage, run, HTML, and SARIF views |
| Traceability | Finding/recommendation mechanisms vary by head | Evidence → claim → finding → risk/action edges in one contract |
| Extensibility | Add a scanner/head integration | Add a collector manifest, SARIF producer/import, or assessment profile independently |

## Current boundary

The isolated flow is a complete repository-evidence baseline, not yet a library
of modernization decision profiles. It proves user-defined collection,
normalization, provenance, coverage, conservative reasoning, standardized
reporting, and action traceability. A future profile can reuse the same evidence
without changing collectors or reports; it must declare researched claims,
thresholds, contradiction behavior, and limitations rather than inheriting an
arbitrary score.

## Post-review decision-ready run

Date: 2026-08-13  
Flow: `decision-ready-review@1.0` plus
`engineering-health-review@1.0`

The same three pinned GitHub repositories were run again after adding the
language-provider catalog, configurable structural biomarkers, pack
recommendations, and engineering-health assessment head.

| Repository | Auto-selected language collector | Normalized evidence | Biomarker findings | Report findings/actions | Report-quality gates |
|---|---|---:|---:|---:|---|
| FastRoute | PHP | 328 | 7 | 8/8 | 9/9 passed |
| MarkupSafe | Python | 138 | 2 | 3/3 | 9/9 passed |
| slugify | JavaScript/TypeScript | 9 | 0 | 2/2 | 9/9 passed |

All 15 selected activities completed, and preview confirmed that nothing left
the machine. FastRoute's selected structural analysis found one complex
callable, one large type, four long callables, and one parameter-bloat case.
MarkupSafe produced one deep-nesting and one large-type case. Slugify received
file-level measurements, but none crossed the selected defaults; the system did
not manufacture a code-health finding from that partial language depth.

The nine executable report gates cover choice and producer fidelity, typed
separation, coverage honesty, action quality, traceability, interoperability,
failure isolation, and the prohibition on false universal scoring. The tenth
gate—usable visual initiation—is verified separately through the local Studio
browser flow.

The original 0.2.0 deterministic assessment was also rerun from its detached
commit, and the current branch's unchanged `codestrata assess` command was run
against the same subjects and baseline configuration. Findings,
recommendations, and dependency evidence were byte-identical on 3/3; testing
evidence was byte-identical where emitted (FastRoute and MarkupSafe). Therefore
the isolated flow remains additive and does not silently change the 0.2.0
compatibility path.

The benchmark is repeatable with
`benchmark_selected_repositories.py`; it exits non-zero when a report gate
fails and emits a compact JSON reconciliation for every subject.

## Local Studio browser acceptance

The production Studio bundle was exercised through a real browser and local
HTTP server, not only component or API tests:

1. The MarkupSafe repository rendered with detected C and Python languages and
   no console error or framework overlay.
2. Selecting `decision-ready-review@1.0` added the applicable Python provider
   and structural-health collector.
3. The user-visible controls deselected one Python capability and one
   structural biomarker; the run preview showed five applicable, local-only
   activities and required explicit confirmation.
4. The run completed with 138 normalized records, three findings, and three
   actions. The opened report reproduced the pack, engineering assessment head,
   tuned capability/biomarker list, coverage, findings, risks, actions, and
   trace edges.
5. A browser-discovered bug that dropped pack provenance after a manual override
   was corrected and the flow repeated. A second issue where local artifacts
   marked the observed Git revision dirty was isolated with a regression test;
   the final Studio bootstrap reported the clean pinned revision even with prior
   `.codestrata-artifacts` present.
6. Finally, the public URL `https://github.com/sindresorhus/slugify` was pasted
   into the UI. CodeStrata created a new bounded cached snapshot at pinned
   revision `7c318bd1aa4b4affab29761f15a9604323fe2a3b`, detected JavaScript and
   TypeScript, and displayed the applicable JavaScript/TypeScript provider,
   code-health pack, individual collectors, SARIF import, and custom-observation
   controls without a console error.

This passes the tenth report-quality gate: a user can initiate the actual
URL-to-language-aware-selection flow without editing YAML.
