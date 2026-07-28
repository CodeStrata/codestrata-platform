# Naming Conventions

**Status:** Foundation  
**Authority:** Standards

## Objective

Keep identifiers, paths, and customer terminology consistent.

## Scope

Product terminology, API paths, Python packages/modules, CLI commands, and
artifacts. Does not rename internal packages in this phase.

## 1. Customer-facing terminology (canonical)

| Term | Notes |
| ---- | ----- |
| Repository | Assessed codebase unit |
| Portfolio | Group of repositories |
| Assessment | Engine assessment run / Platform assessment record |
| Engineering Assessment | Customer report name (prefer over Modernization Assessment) |
| Engineering Intelligence | Product capability family |
| Engineering Knowledge | Domain knowledge corpus |
| Engineering Knowledge Graph | Platform graph capability (CLI group may remain `enterprise`) |
| Engineering Snapshot | Customer term for CEIM |
| Knowledge Graph | Graph of engineering entities |
| Repository Intelligence | Repo-scoped intelligence |
| Portfolio Intelligence | Portfolio-scoped intelligence |
| Executive Intelligence | Executive rollup |
| Strategic Roadmap | Portfolio roadmap presentation |
| Finding | Deterministic issue |
| Recommendation | Deterministic recommended action |
| Evidence | Supporting proof |
| Citation | Answer grounding reference |
| Confidence | Stated confidence |
| Coverage | Stated coverage |
| Limitation | Explicit limitation |

<!-- Prefer Engineering Assessment (not Modernization Assessment) for customer reports. -->

## 2. Technical naming

| Kind | Convention |
| ---- | ---------- |
| Python packages | `codestrata`, `codestrata_platform` |
| Modules | snake_case |
| Classes | PascalCase |
| REST paths | kebab-case resource segments |
| Env vars | `CODESTRATA_*` |
| Feature flags | Explicit `CODESTRATA_*_ENABLED` (document intentional flags) |

## 3. CLI

- Primary workflow command: `assess`
- Legacy: `scan` (document as legacy/advanced)

## 4. References

- [BRANDING_GUIDELINES.md](BRANDING_GUIDELINES.md)
- [API_STANDARDS.md](API_STANDARDS.md)
- [004_PRODUCT_PRINCIPLES.md](../constitution/004_PRODUCT_PRINCIPLES.md)
