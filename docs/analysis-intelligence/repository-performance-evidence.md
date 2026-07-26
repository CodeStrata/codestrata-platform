# Repository Performance Evidence (Phase 4.9.2)

Platform evidence for repository-observable performance signals.
**Not** owned by Performance Intelligence assessment.

## Ownership

| Concern | Owner |
| ------- | ----- |
| Discovery / data access / blocking / caching / concurrency / resource / frontend / observability / configuration facts | Platform `repository_performance` evidence |
| Performance Intelligence interpretation | Deferred (future Performance rules) |
| Findings / severity / performance scores | Not in this phase |

Collectors must not import `aimf.domain.performance` /
`aimf.application.performance` and must not emit Findings.

## Contract

| Constant | Value |
| -------- | ----- |
| Schema | `repository-performance-evidence` **1.0.0** |
| Artifact | `repository-performance-evidence.json` |
| Schema ID | `codestrata.repository_performance_evidence` |
| Provider | `repository_performance.discovery` @ `1.0.0` |
| Aggregate | `AggregatedRepositoryPerformanceEvidence` |

## Detected families

1. **Data access** — JPA/Hibernate/Spring Data, JDBC, EF/Dapper, Prisma, Sequelize
2. **Blocking operations** — `Thread.sleep`, sync HTTP clients, blocking file I/O
3. **Caching** — Spring Cache, Caffeine, Redis, Ehcache, CacheManager
4. **Concurrency / async** — CompletableFuture, ExecutorService, virtual threads, Reactor, RxJava, async/await, TPL
5. **Resource management** — HikariCP, Apache DBCP, try-with-resources, IDisposable
6. **Frontend performance** — webpack/vite/next/angular bundle config, lazy loading, code splitting
7. **Observability / profiling** — Micrometer, OpenTelemetry, Prometheus, tracing
8. **Configuration controls** — thread pool, executor, cache, datasource, timeout settings

## Configuration

```toml
[evidence.repository_performance]
enabled = false
# max_files = 500
# max_file_chars = 500000
# max_file_bytes = 2000000
```

Independent of `[analysis.performance]` and future report/rules gates.

## Explicit non-claims

Zero candidates does not mean performance risks are absent. Presence of
candidates does not mean the repository is performant, scalable, or free of
latency risk under load.
