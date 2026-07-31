# MCP

Report MCP tools inspect presentation-layer content from `report.json`.

Assessment MCP:

- Structured engineering assessment data (`architecture-assessment.json`)

Report MCP:

- Audience-oriented presentation (`assessment.architecture` in `report.json`)
- Canonical Epic 2 traceability collections via `inspect_assessment_report*`
  (`assessment.evidence`, findings, recommendations, Priority Actions, roadmap)

Tools:

- `list_report_sections`
- `inspect_architecture_report_section`
- `inspect_architecture_report_executive_summary`
- `inspect_architecture_report_conclusions`
- `inspect_architecture_report_recommendations`
- `inspect_architecture_report_findings`
- `inspect_architecture_report_coverage`
- `inspect_architecture_report_limitations`
- `inspect_architecture_report_traceability`
- `inspect_assessment_report`
- `get_assessment_report_entity`
- `inspect_assessment_report_traceability`

Does not expose source code, absolute paths, unbounded evidence, or stack traces.
Does not regenerate Priority Actions, roadmap initiatives, or Evidence IDs.
