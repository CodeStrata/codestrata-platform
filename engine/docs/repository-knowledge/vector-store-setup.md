# Vector store setup (Phase 5.4.1)

Local operations for the Repository Knowledge `VectorStore`: default memory mode,
Docker Compose pgvector, environment configuration, and hosted PostgreSQL notes.

## 1. Default memory mode

```toml
[knowledge.vector_store]
provider = "memory"
```

- Zero external dependencies
- Non-persistent (`health().detail["persistent"] == false`)
- No Docker, no database URL, no optional Python extras required

## 2. Local Docker pgvector mode

PostgreSQL is **not** installed on the developer machine. Use Docker Compose.

```bash
docker compose up -d postgres
docker compose ps
docker compose logs postgres
```

Service defaults (developer-only credentials):

- Image: `pgvector/pgvector:pg16`
- Database / user / password: `codestrata`
- Port: `5432`
- Named volume: `codestrata_pgdata` (survives ordinary stop/down)

## 3. Optional Python dependency

```bash
pip install 'codestrata[pgvector]'
# or: pip install 'psycopg[binary]' pgvector
```

## 4. Copy environment template

```bash
cp .env.example .env
```

Edit `.env` (never commit it):

```bash
CODESTRATA_VECTOR_STORE_PROVIDER=pgvector
CODESTRATA_DATABASE_URL=postgresql://codestrata:codestrata@localhost:5432/codestrata
CODESTRATA_DATABASE_SCHEMA=codestrata
```

Local example credentials are for developer Docker only.

OS environment variables always win over `.env` values.

## 5. Start Docker

```bash
docker compose up -d postgres
```

Wait until healthy (`docker compose ps`).

## 6. Verify database health

With pgvector selected and the URL set, create a store and call `health()`:

- `healthy == true`
- `detail.persistent == true`
- `detail.pgvector_extension == true`
- `detail.schema` / `schema_version` present
- No passwords in health output

## 7. Enable pgvector in configuration

Preferred: environment (`CODESTRATA_VECTOR_STORE_PROVIDER=pgvector`).

Optional codestrata.toml (no secrets):

```toml
[knowledge.vector_store]
provider = "pgvector"
connection_string_env = "CODESTRATA_DATABASE_URL"
schema = "codestrata"
hnsw = true
connect_timeout_seconds = 10
```

**Do not** put a real connection string in `codestrata.toml`.

### Precedence

| Setting | Order |
| ------- | ----- |
| Provider | `CODESTRATA_VECTOR_STORE_PROVIDER` → codestrata.toml → `memory` |
| Schema | `CODESTRATA_DATABASE_SCHEMA` → codestrata.toml → `codestrata` |
| Database URL | `CODESTRATA_DATABASE_URL` → deprecated `CODESTRATA_PGVECTOR_URL` → programmatic test override → deprecated TOML `connection_string` |

There is **no** silent fallback from pgvector to memory.

## 8. Running indexing

Enable knowledge embedding + indexing as in Phase 5.3, with the vector store
provider set to `pgvector`. `KnowledgeIndexer` is unchanged — only the store
backend differs.

## 9. Stopping Docker safely

```bash
docker compose stop postgres
# or
docker compose down
```

`docker compose down` **preserves** the named volume `codestrata_pgdata`.

## 10. Deleting local data intentionally

```bash
docker compose down -v
```

`-v` deletes the volume and **all** locally indexed knowledge data. Ordinary
shutdown instructions must not include `-v`.

## 11. Troubleshooting connection failures

| Symptom | Fix |
| ------- | --- |
| Missing URL | Set `CODESTRATA_DATABASE_URL` |
| Connection refused | `docker compose up -d postgres` and wait for healthy |
| Extension error | Use `pgvector/pgvector` image or `CREATE EXTENSION vector` |
| Import error | `pip install 'codestrata[pgvector]'` |
| Wrong schema | Check `CODESTRATA_DATABASE_SCHEMA` / codestrata.toml `schema` |

Errors and diagnostics redact passwords (`postgresql://user:***@host/...`).

## 12. Switching later to AWS RDS or Aurora

AWS is **not** required today and creates **no** AWS charges for local Docker.

The same `PgVectorStore` works with any compatible hosted PostgreSQL that has
the `pgvector` extension. Change only the environment:

```bash
CODESTRATA_VECTOR_STORE_PROVIDER=pgvector
CODESTRATA_DATABASE_URL=postgresql://username:password@host:5432/codestrata?sslmode=require
CODESTRATA_DATABASE_SCHEMA=codestrata
```

## 13. SSL for hosted PostgreSQL

Hosted databases normally require TLS (`sslmode=require` or stricter). Local
Docker typically does not.

## 14. Secret handling

- Prefer platform / secret-manager injection in real deployments
- Never commit `.env` with real credentials
- Never log raw connection strings
- Health, diagnostics, exceptions, reports, and manifests must not expose passwords

Deprecated: `CODESTRATA_PGVECTOR_URL` and TOML `connection_string` (compat only).
