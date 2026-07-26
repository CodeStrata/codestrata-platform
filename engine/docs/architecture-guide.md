# Architecture Guide

How CodeStrata turns a repository into evidence, findings, and reports.

Canonical deep design notes live in [ARCHITECTURE.md](../../ARCHITECTURE.md) and
[community-edition.md](community-edition.md)
(optional KG overview; Platform-only docs are not shipped in the public engine mirror).
This page is the developer-facing map.

## Design principles

1. **Deterministic analysis first** — findings and recommendations come from
   rules and evidence, not from LLM invention.
2. **AI second** — optional Bedrock enrichment adds narrative only.
3. **Configuration-driven editions** — Community vs Enterprise is gated by
   settings (see [configuration-profiles.md](configuration-profiles.md)).
4. **Artifacts are the contract** — HTML is presentation; JSON is the machine
   interface ([report-contract.md](report-contract.md)).

## Runtime pipeline

```text
CLI / codestrata.toml
        │
        ▼
  Repository scan (local path or GitHub clone)
        │
        ▼
  Phase 1 analysis (detectors + analyzers + optional PMD)
        │
        ▼
  Repository Inventory → Repository Graph
        │
        ▼
  Knowledge Pipeline ← Engineering Knowledge Graph
        │
        ▼
  Assessment Graph → Rule Engine → Recommendation Engine
        │
        ├──────────────┐
        ▼              ▼
  HTML/JSON reports   optional AI enrichment (one call)
```

Details: [runtime.md](runtime.md).

## Major subsystems

| Area | Entry | Docs |
| ---- | ----- | ---- |
| Assessment orchestration | `codestrata assess` | [runtime.md](runtime.md) |
| Rules / findings | `codestrata rules` | [rule-engine.md](rule-engine.md) |
| Recommendations | (assess) | [recommendation-engine.md](recommendation-engine.md) |
| Knowledge store | `.codestrata/knowledge` | [knowledge-store.md](knowledge-store.md) |
| Repository knowledge / RAG | `codestrata repository` | [repository-knowledge/README.md](repository-knowledge/README.md) |
| MCP | `codestrata mcp` | [mcp-server.md](mcp-server.md) |
| Agents | `codestrata agent` | [agent-framework.md](agent-framework.md) |
| Enterprise KG | `codestrata enterprise` | [community-edition.md](community-edition.md) (stub → platform docs) |
| Execution profiles | `codestrata config` | [configuration-profiles.md](configuration-profiles.md) |
| Runtime performance | `analysis.runtime` | [runtime-performance.md](runtime-performance.md) |

## Package layout

```text
src/codestrata/
  cli/                 # Typer adapters (thin)
  application/         # Use-cases / orchestration
  domain/              # Models and contracts
  services/            # Detectors, analyzers, scanners
  infrastructure/      # Stores, embeddings, AWS
  interfaces/mcp/      # FastMCP composition
  reporting/           # HTML + JSON report builders
  config/              # Settings + execution profiles
```

## Language coverage

Evidence and packs currently emphasize:

* Java (Maven/Gradle, PMD optional)
* JavaScript / TypeScript (npm)
* Python (complexity + detectors)
* PHP (Composer)
* C# / .NET (NuGet)

Sample apps for each language plus golden HTML/JSON reports:

* Samples: [examples/README.md](../../examples/README.md)
* Reports: [examples/sample-reports/README.md](../../examples/sample-reports/README.md)

## Related

* [capabilities.md](capabilities.md) — what is shipped vs gated
* [assessment-framework/methodology.md](assessment-framework/methodology.md)
* [community-enterprise-boundary.md](assessment-framework/community-enterprise-boundary.md)
