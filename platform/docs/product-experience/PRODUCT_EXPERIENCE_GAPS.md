# Product Experience Gaps

**Phase:** 9.1 audit  
**Priority:** P0 blocks install/scan/report/truthfulness; P1 harms adoption/credibility; P2 consistency; P3 polish.

## P0

| ID | Gap | User | Current | Evidence | Impact | Correction | Target | Scope |
| -- | --- | ---- | ------- | -------- | ------ | ---------- | ------ | ----- |
| PE-P0-01 | Blank `ai.bedrock.answer_model` aborts assess | Community developer | Mid-run Pydantic error; no reports; misleading success signals possible depending on path | Assess with repo `codestrata.toml` (`answer_model=""`); `BedrockSettings` validator returns `None` for `str` field | Blocks first scan in monorepo / copied configs | Coerce blank→default empty-safe string; fail closed with exit≠0 if unrecoverable | 9.2 config/CLI | Community |
| PE-P0-02 | Assess can surface raw validation errors | Community developer | Stack/validation text in terminal | Same run | Undermines trust; not actionable | Map to doctor-style Fix: messages; nonzero exit | 9.2 | Community |

## P1

| ID | Gap | User | Current | Evidence | Impact | Correction | Target | Scope |
| -- | --- | ---- | ------- | -------- | ------ | ---------- | ------ | ----- |
| PE-P1-01 | Brand “CodeStrata AI” in HTML | All report readers | Title/footer/alt text | `branding.py`; golden HTML | Violates Governance branding | Use **CodeStrata** | 9.3 branding/reports | Community |
| PE-P1-02 | CLI `enterprise` vs Platform | Integrators / leaders | Enterprise KG CLI group | CLI help; Platform extension | Wrong product mental model | Relabel Platform-scoped | 9.3 | Platform+CLI |
| PE-P1-03 | Incomplete OpenAPI tags | API integrator | Tags subset of routers | `api/app.py` | Poor discovery | Complete tag metadata | 9.5 API | Platform |
| PE-P1-04 | Community vs Platform not in root help | New users | Help lists Platform commands when installed | `codestrata --help` | Confusion / false expectations | Tiered help + boundary blurb | 9.2 | Both |
| PE-P1-05 | Source-retention messaging unclear | Security-conscious buyers | Implicit only | Docs sparse | Credibility | Explicit Community vs Platform statement | 9.6 docs | Both |
| PE-P1-06 | Engine `roadmap` vs Platform Strategic Roadmap | Leaders | Homonyms | CLI + API tags | Mis-navigation | Disambiguate names in help/API | 9.3/9.5 | Both |
| PE-P1-07 | MCP disabled by default without clear next step | MCP integrator | `mcp tools` blocked | Golden path | Adoption friction | Doctor + enable guidance | 9.2 | Community |

## P2

| ID | Gap | Notes | Target |
| -- | --- | ----- | ------ |
| PE-P2-01 | Modernization Assessment vs Engineering Assessment titles | CLI default vs HTML brand | 9.3 |
| PE-P2-02 | Phase numbers in customer CLI help | `rules`, `evidence`, … | 9.2 |
| PE-P2-03 | `version` shows Bedrock default for non-AI users | Noise | 9.2 |
| PE-P2-04 | OpenAPI “Commercial Platform” wording | Align to CodeStrata Platform | 9.5 |
| PE-P2-05 | Design System not wired to report assets package | Inline CSS vs `governance/assets` | 9.4 |
| PE-P2-06 | Exit-code contract incomplete across commands | Document + align | 9.2 |
| PE-P2-07 | AI failure paths sometimes label provider bedrock | Accuracy | 9.2 |
| PE-P2-08 | Advanced maintainer commands in root help | acceptance/release | 9.2 |

## P3

| ID | Gap | Target |
| -- | --- | ------ |
| PE-P3-01 | Cost/token visibility for advisor | Later AI UX |
| PE-P3-02 | Shell completion discoverability | Polish |
| PE-P3-03 | Public SDK packaging | After API freeze |
| PE-P3-04 | Documentation portal IA | Phase 12-oriented |

## Related catalogs

- Rules: [`knowledge/RULE_CATALOG.md`](../../../knowledge/RULE_CATALOG.md)
- Traceability: [`knowledge/TRACEABILITY.md`](../../../knowledge/TRACEABILITY.md)
