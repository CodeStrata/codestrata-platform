# MCP

Additive **CodeStrata Platform** tools for the Engineering Knowledge Graph
(tool names retain the `enterprise_` prefix for wire stability):

1. validate_enterprise_workspace
2. build_enterprise_knowledge_graph
3. get_enterprise_graph
4. get_enterprise_entity
5. query_enterprise_entities
6. get_enterprise_entity_neighborhood
7. trace_enterprise_dependency_path
8. get_repository_enterprise_context
9. get_finding_enterprise_impact
10. get_recommendation_enterprise_impact
11. explain_enterprise_relationship
12. compare_enterprise_graph_versions

Not available on Community Engine alone. Inject services via
`create_mcp_server(...)` for tests.

Community vs Platform catalog: [engine MCP tools](../../../engine/docs/mcp/tools.md) ·
[API & MCP experience](../product-experience/API_MCP_EXPERIENCE.md).

## Resources (when enterprise query service is configured)

- `codestrata://enterprise/graphs/latest`
- `codestrata://enterprise/graphs/{graph_id}`
- `codestrata://enterprise/entities/{entity_id}`
- `codestrata://enterprise/entities/{entity_id}/relationships`
- `codestrata://enterprise/repositories/{repository_id}/context`
- `codestrata://enterprise/findings/{finding_id}/impact`
- `codestrata://enterprise/recommendations/{recommendation_id}/impact`
