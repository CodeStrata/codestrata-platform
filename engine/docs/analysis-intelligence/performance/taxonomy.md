# Performance Taxonomy

Phase 4.9.1 methodology identifiers only. No detection or scoring is performed.

| Category | Value |
| -------- | ----- |
| Inefficient data access / query patterns | `performance.inefficient_data_access` |
| Blocking synchronous execution | `performance.blocking_operations` |
| Unbounded collection processing | `performance.unbounded_collection_processing` |
| Excessive object / resource creation | `performance.excessive_resource_creation` |
| Caching foundations | `performance.caching` |
| Batching / pagination | `performance.batching_pagination` |
| Concurrency / async | `performance.concurrency` |
| Connection / resource management | `performance.resource_management` |
| Frontend rendering / bundle | `performance.frontend_rendering_bundle` |
| Observability / profiling | `performance.observability_profiling` |
| Configuration controls | `performance.configuration_controls` |
| Serialization | `performance.serialization` |
| Hot-path coupling | `performance.hot_path_coupling` |
| Miscellaneous | `performance.miscellaneous` |
| Unknown | `performance.unknown` |

Aliases such as `query_patterns`, `blocking_synchronous_execution`, and
kebab-case forms (`performance.blocking-operations`) coerce to the matching
canonical value. Unknown or malformed inputs coerce to
`performance.unknown`.
