# Current User Journeys

**Phase:** 9.1 audit  
**Evidence:** CLI help, `doctor`, assess golden paths, Platform API/MCP code.

## Personas

### 1. Community Developer

**Goal:** Install Engine, assess a local repo, get HTML/JSON without Platform.

**Current happy path (when config is healthy):**

1. `pip install` / editable `engine[dev]` (see `engine/docs/installation.md`)
2. `codestrata init` → minimal `codestrata.toml`
3. `codestrata doctor`
4. `codestrata assess --repo . --output reports --no-ai`
5. Open `report.html` / `report.json`

**Works without:** Platform, RAG, Portfolio, EI, PostgreSQL.

**Friction observed:**

- Root monorepo `codestrata.toml` with `answer_model = ""` causes assess to abort mid-pipeline with a raw Pydantic error (golden path fail).
- Help points to `docs/quick-start.md` relative paths that assume Engine checkout layout.
- `enterprise` / `ai` / `repository` CLI groups appear when Platform is installed; confusing without clear Community labeling.
- HTML brand says **CodeStrata AI** while CLI `version`/`about` say **CodeStrata**.

### 2. Engineering Leader

**Goal:** Trustworthy assessment narrative, priorities, portfolio/executive views.

**Community today:** Engineering Assessment HTML (leadership sections + findings). AI advisor optional (`--with-ai`).

**Platform today:** Portfolio → EI → Presentation → Strategic Roadmap (feature-flagged, on-read presentation/roadmap). Requires ingestion + Postgres + API key in production.

**Friction:** Platform journey not discoverable from Engine CLI help; “Enterprise” CLI naming vs “Platform” product name.

### 3. Platform Administrator

**Goal:** Run Commercial Platform API safely.

**Current:** FastAPI app; `CODESTRATA_DATABASE_URL` (PostgreSQL only); `CODESTRATA_PLATFORM_API_KEY`; `/health` `/ready`; feature flags for answering/EI/presentation/roadmap.

**Friction:** OpenAPI tag list incomplete vs routers; many flags undocumented for operators in one place.

### 4. API / MCP Integrator

**Goal:** Automate assess / query knowledge.

**MCP:** `codestrata mcp serve|tools|health` (needs `[mcp].enabled=true`). Community tools in Engine; RAG/enterprise tools via Platform extensions.

**API:** `/api/v1/...` Commercial Platform only.

**Friction:** Default MCP disabled; Integrator must distinguish Engine MCP vs Platform REST.

### 5. AI-enabled User

**Goal:** Optional Modernization Advisor + (Platform) grounded answering.

**Community AI:** `--with-ai` + `[ai].provider` bedrock|openai. Missing creds → deterministic reports retained, `AI status: fallback`.

**Platform AI:** Embedding/answer providers for retrieval/answering (separate from assess advisor).

### 6. Non-AI User

**Goal:** Fully offline / no cloud credentials.

**Supported:** `--no-ai` (default). Deterministic findings/recommendations/reports.

**Friction:** Default `ai.provider` still shows as bedrock in `codestrata version` even for non-AI users (noise).

## Journey map (canonical product flow)

Community typically stops at Assessment → reports.  
Platform continues through CEIM → KG → Retrieval → Answering → Portfolio → EI → Presentation → Roadmap.

See Governance architecture principles and Knowledge traceability for meaning of each stage.
