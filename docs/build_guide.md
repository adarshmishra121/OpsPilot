# OpsPilot — Complete Build Guide (Learning Reference)

> This document captures every detail from the build process — what each file does, why it exists, how it works internally, and key concepts a beginner needs to understand. Use this as your study guide for interviews.

---

## Progress Tracker

| Phase | Steps | Status | Git Commit |
|-------|-------|--------|------------|
| Phase 1: Foundation & Scaffolding | Steps 1-5 | ✅ Complete | `feat: scaffold project structure, configs, and Docker stack` |
| Phase 2: API Skeleton + Observability | Steps 6-10 | ✅ Complete | `feat: add API skeleton with schemas, health check, and observability` |
| Phase 3: Data Download Scripts | Step 11 | ✅ Complete | (batched with Phase 4) |
| Phase 4: RAG Pipeline | Steps 12-19 | ✅ Complete | `feat: add data pipeline, embeddings, and hybrid RAG retriever` |
| Phase 5: Anomaly Detection | Steps 20-25 | ✅ Complete | `feat: add anomaly detection pipeline with Drain3, IsolationForest, and MLflow` |
| Phase 6: Storage (SQL + Feedback) | Steps 26-28 | ✅ Complete | `feat: add database storage and feedback endpoint` |
| Phase 7: Agent Orchestration | Steps 29-33 | ⬜ Not started | |
| Phase 8: Auth + Admin | Steps 34-35 | ⬜ Not started | |
| Phase 9: Streamlit UI | Step 36 | ⬜ Not started | |
| Phase 10: Evaluation + DVC | Steps 37-39 | ⬜ Not started | |
| Phase 11: Prefect Workflows | Steps 40-41 | ⬜ Not started | |
| Phase 12: Tests + CI/CD | Steps 42-45 | ⬜ Not started | |
| Phase 13: Documentation | Steps 46-50 | ⬜ Not started | |
| Phase 14: Verification & Ship | Steps 51-57 | ⬜ Not started | |

---

## File Location Rules

```
src/opspilot/...    ← Importable Python package code (libraries, classes)
scripts/...         ← Standalone runnable scripts (download, train, build)
ui/...              ← Streamlit frontend
tests/...           ← pytest test files
data/...            ← Datasets ONLY (gitignored, DVC-tracked)
artifacts/          ← Built indexes, vocab files (gitignored)
models/             ← Trained .pkl model files (gitignored)
docker/             ← Dockerfiles + monitoring configs
docs/               ← Documentation
```

---

# PHASE 1: Foundation & Scaffolding

---

## Step 1: Directory Structure

### What
Created the entire folder tree (25+ directories) and 10 empty `__init__.py` files.

### Why
- A clean folder structure is the foundation of a professional project
- `__init__.py` files tell Python: "this folder is a package, you can import from it"
- Without `__init__.py`, `from opspilot.api.main import app` would fail with `ModuleNotFoundError`
- Having the full skeleton upfront means no surprises later

### Full Structure
```
OpsPilot/
├── src/opspilot/                ← Main Python package (ALL your code lives here)
│   ├── __init__.py              ← "OpsPilot — production-grade incident response copilot."
│   ├── api/                     ← FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py              ← App factory (Step 6)
│   │   ├── schemas.py           ← Pydantic models (Step 7)
│   │   ├── deps.py              ← Auth dependencies (Step 34)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py        ← GET /health (Step 8)
│   │       ├── incident.py      ← POST /incident/analyze (Step 33)
│   │       ├── rag.py           ← POST /rag/search (Step 19)
│   │       ├── anomaly.py       ← POST /anomaly/score (Step 25)
│   │       ├── feedback.py      ← POST /feedback (Step 28)
│   │       └── admin.py         ← Admin endpoints (Step 35)
│   ├── agent/                   ← LangGraph agent
│   │   ├── __init__.py
│   │   ├── graph.py             ← State machine (Step 32)
│   │   ├── prompts.py           ← System prompt (Step 29)
│   │   ├── safety.py            ← Groundedness validation (Step 30)
│   │   └── tools.py             ← Agent tool functions (Step 31)
│   ├── rag/                     ← RAG pipeline
│   │   ├── __init__.py
│   │   ├── chunking.py          ← Text chunker (Step 13)
│   │   ├── index.py             ← FAISS store (Step 14)
│   │   ├── docstore.py          ← Document lookup (Step 15)
│   │   ├── bm25.py              ← Keyword search (Step 16)
│   │   └── retriever.py         ← Hybrid fusion (Step 17)
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── encoder.py           ← Text → vectors (Step 12)
│   ├── anomaly/
│   │   ├── __init__.py
│   │   ├── features.py          ← Online featurizer (Step 23)
│   │   └── infer.py             ← Anomaly scorer (Step 24)
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── db.py                ← Database engine (Step 26)
│   │   └── models.py            ← Table models (Step 27)
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── logging.py           ← JSON logging (Step 9)
│   │   └── metrics.py           ← Prometheus (Step 10)
│   └── workflows/
│       ├── __init__.py
│       ├── prefect_flows.py     ← Scheduled jobs (Step 40)
│       └── drift.py             ← Drift detection (Step 41)
├── scripts/
│   ├── data/download_all.py     ← Download datasets (Step 11)
│   ├── features/
│   │   ├── parse_logs.py        ← Drain3 parsing (Step 20)
│   │   └── build_features.py    ← Feature vectors (Step 21)
│   ├── train/train_anomaly.py   ← Train model (Step 22)
│   ├── rag/build_index.py       ← Build FAISS index (Step 18)
│   └── eval/run_eval.py         ← Evaluate RAG (Step 37)
├── ui/streamlit_app.py          ← Frontend (Step 36)
├── tests/                       ← pytest tests
├── docker/                      ← Docker configs
├── data/                        ← DVC-tracked data
├── artifacts/                   ← FAISS index files
├── models/                      ← Trained models
└── docs/                        ← Documentation
```

### What each `__init__.py` contains
Each has a one-line module docstring (PEP 257 best practice):
- `opspilot/__init__.py` → `"OpsPilot — production-grade incident response copilot."`
- `api/__init__.py` → `"FastAPI application and route handlers."`
- `agent/__init__.py` → `"LangGraph agent orchestrator for incident triage and response."`
- `rag/__init__.py` → `"RAG pipeline: hybrid retrieval over runbook knowledge base."`
- etc.

---

## Step 2: `pyproject.toml`

### What
The single config file that tells Python what your project is, what dependencies it needs, and how to install it.

### Key dependency groups and why each library exists

| Library | What it does | Why OpsPilot needs it |
|---------|-------------|----------------------|
| `fastapi` | Web framework | Our API backend — handles HTTP requests |
| `uvicorn[standard]` | ASGI server | Actually **runs** FastAPI — listens on port 8000 |
| `pydantic` | Data validation | Defines request/response shapes, auto-validates input |
| `sqlmodel` | ORM (database toolkit) | Maps Python classes to database tables |
| `psycopg[binary]` | PostgreSQL driver | Connects Python to Postgres (falls back to SQLite locally) |
| `httpx` | HTTP client | Agent calls the Ollama LLM API |
| `numpy` | Numerical arrays | FAISS and scikit-learn need it for vector math |
| `pandas` | DataFrames | Read/write parquet files for log processing |
| `scikit-learn` | ML library | `IsolationForest` for anomaly detection |
| `joblib` | Model serialization | Saves/loads trained models (.pkl files) |
| `structlog` | Structured logging | JSON logs (production-grade, not messy print statements) |
| `prometheus-fastapi-instrumentator` | Metrics | Auto-adds Prometheus metrics to every endpoint |
| `diskcache` | Disk-based cache | Caches computed embeddings to avoid re-computation |
| `sentence-transformers` | Text embeddings | Converts text → 384-dim vectors with all-MiniLM-L6-v2 |
| `faiss-cpu` | Vector search | Fast similarity search — our vector store |
| `rank-bm25` | Lexical search | BM25 keyword matching (complements vector search) |
| `langgraph` | Agent framework | Builds our state machine agent |
| `mlflow` | Experiment tracking | Logs params, metrics, model artifacts |
| `drain3` | Log template mining | Parses raw logs into templates (anomaly detection) |
| `prefect` | Workflow orchestration | Schedules nightly reindex, drift check jobs |
| `evidently` | Drift detection | Detects when data distribution shifts |
| `PyJWT` | JWT tokens | Auth token decoding for RBAC |

### Critical line explained
```toml
packages = [{ include = "opspilot", from = "src" }]
```
This tells pip: "When someone does `from opspilot.api.main import app`, look inside `src/opspilot/`." Without this, Python can't find your code.

### Version pinning with `^`
`"^0.112.0"` means "at least 0.112.0, up to (but not including) the next major version." This prevents breaking changes while allowing patches.

---

## Step 3: `.env.example` + `.gitignore` + `Makefile`

### `.env.example` — Environment variables

**What**: Template for config values that change between environments. Users copy it to `.env` and fill in real values.

**Critical variables explained**:

| Variable | Default | Why |
|----------|---------|-----|
| `LLM_PROVIDER=mock` | `mock` | Start with deterministic mock responses. Flip to `ollama` for real LLM. |
| `HYBRID_ALPHA=0.6` | `0.6` | Score fusion: 60% vector + 40% BM25. Higher = trust meaning more. |
| `RAG_TOP_K=6` | `6` | Retrieve 6 chunks per query. Enough context without overwhelming LLM. |
| `OLLAMA_MODEL=llama3.2:3b-instruct-q4_K_M` | — | 3B params, 4-bit quantized, ~2GB RAM on CPU. |
| `DATABASE_URL=sqlite:///./opspilot.db` | SQLite | Single file DB for local dev. Postgres in Docker. |

### `.gitignore` — What NOT to commit

Key entries: `.env` (secrets), `data/raw/` (DVC-tracked), `models/` (large binaries), `__pycache__/` (generated), `mlruns/` (use MLflow server).

### `Makefile` — Developer shortcuts

| Command | What happens |
|---------|-------------|
| `make setup` | Install all deps in editable mode |
| `make data` | Download Loghub + Runbooks |
| `make features` | Parse logs → templates → feature vectors |
| `make train` | Train IsolationForest + log to MLflow |
| `make index` | Build FAISS vector index from runbooks |
| `make api` | Start FastAPI at localhost:8000 |
| `make ui` | Start Streamlit at localhost:8501 |
| `make up` | Start entire Docker Compose stack |
| `make test` | Run pytest |
| `make repro` | Run entire DVC pipeline end-to-end |

---

## Step 4: Docker Files

### `docker-compose.yml` — Full stack orchestrator

**8 services** and what each does:

```
User → UI (8501) → API (8000) → { Ollama, Postgres, Redis, MLflow }
                                 ↓
                     Prometheus (9090) → Grafana (3000)
```

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `postgres` | postgres:16 | 5432 | SQL database for feedback, incidents |
| `mlflow` | mlflow:v2.14.3 | 5000 | Experiment tracking UI + model registry |
| `redis` | redis:7 | 6379 | Cache embeddings and retrieval results |
| `ollama` | ollama/ollama | 11434 | Local LLM runtime (optional) |
| `api` | custom Dockerfile | 8000 | FastAPI backend (our main app) |
| `ui` | custom Dockerfile | 8501 | Streamlit incident console |
| `prometheus` | prom/prometheus | 9090 | Scrapes /metrics every 10s |
| `grafana` | grafana/grafana | 3000 | Dashboard visualization |

**Key concept — Docker networking**: Inside Docker Compose, services find each other by **name**, not localhost:
```yaml
DATABASE_URL: postgresql+psycopg://opspilot:opspilot@postgres:5432/opspilot
#                                                    ^^^^^^^^
#                                            service name, not localhost
```

### `docker/api.Dockerfile` — API container

**Layer caching optimization**:
```dockerfile
COPY pyproject.toml /app/pyproject.toml   # Step 1: Copy deps file (changes rarely)
RUN pip install -e ".[api]"               # Step 2: Install deps (slow, but cached!)
COPY src /app/src                         # Step 3: Copy code (changes often)
```
If you only change source code, Docker reuses the cached pip install layer → **fast rebuilds**.

### `docker/prometheus.yml` — Scrape config

Tells Prometheus: "Every 10 seconds, call GET http://api:8000/metrics and store the data."

---

## Step 5: `drain3.ini`

### What is Drain3?

A streaming log parser that automatically discovers **templates** (patterns) in raw log lines.

### How it works (visual)

```
Raw log lines:                              Templates discovered:
────────────                                ────────────────────
"ERROR: disk full on /dev/sda1"     ──┐
"ERROR: disk full on /dev/sdb2"     ──┤──→  Template #1: "ERROR: disk full on <*>"
"ERROR: disk full on /dev/sdc3"     ──┘

"INFO: User john logged in"        ──┐
"INFO: User alice logged in"       ──┤──→  Template #2: "INFO: User <*> logged in"
"INFO: User bob logged in"         ──┘
```

### The full anomaly detection pipeline

```
drain3.ini (config)
    │ configures
    ▼
Raw Logs → [Drain3] → Template IDs → [Count per 5-min window] → Feature Vector → [IsolationForest] → Score
                                                                  [12, 0, 5, 87]                       0.8 🚨
```

1. **Raw logs** — messy text, can't do math on it
2. **Drain3** — converts each line to a template ID (e.g., Template #1, #2)
3. **Count** — count how many times each template appears per 5-minute window
4. **Feature vector** — list of numbers: `[12, 0, 5, 87, 0, 3, ...]`
5. **IsolationForest** — ML model that learns "normal" vectors
6. **Score** — 0.0 (normal) to 1.0 (anomalous) — high score = incident!

### Config settings explained

| Setting | Value | What it does |
|---------|-------|-------------|
| `snapshot_interval_minutes` | 10 | Saves learned state every 10 min (crash recovery) |
| `compress_state` | true | Compress saved state to save disk |
| `masking` | NUM, HEX | Replace numbers→`NUM`, hex→`HEX` before parsing |
| `sim_th` | 0.4 | Similarity threshold: 40%+ similar → merge into template |
| `depth` | 4 | Parse tree depth (4 is standard) |
| `max_clusters` | 100000 | Max templates Drain3 can discover |
| `extra_delimiters` | `_-/.` | Also split words on these (not just spaces) |

**Why masking matters**: Without masking, "port 8080" and "port 3000" would be different templates. With masking, both become "port NUM" → same template. Reduces noise dramatically.

---

# PHASE 2: API Skeleton + Observability

---

## Step 6: `src/opspilot/api/main.py`

### What is FastAPI?

A Python web framework that turns your functions into HTTP endpoints (URLs):

```
Your function:                    Becomes:
──────────                        ────────
health()                    →     GET  http://localhost:8000/health
analyze(req)                →     POST http://localhost:8000/incident/analyze
rag_search(req)             →     POST http://localhost:8000/rag/search
```

### What is the App Factory pattern?

```python
# Simple (bad for testing):
app = FastAPI()

# App Factory (professional):
def create_app():
    app = FastAPI()
    # ... setup logging, metrics, routers ...
    return app
app = create_app()
```

**Why factory?** In tests, call `create_app()` to get a **fresh** app instance with zero leftover state.

### What are Routers?

Instead of putting all endpoints in one file, we split them into focused files:
```
health.py      → handles /health
incident.py    → handles /incident/*
rag.py         → handles /rag/*
anomaly.py     → handles /anomaly/*
feedback.py    → handles /feedback
```

`main.py` connects them:
```python
app.include_router(incident_router, prefix="/incident", tags=["incident"])
# prefix="/incident" + route "/analyze" = full URL "/incident/analyze"
# tags=["incident"] = groups them in Swagger docs under "incident" section
```

### How `uvicorn opspilot.api.main:app` works

```
uvicorn opspilot.api.main:app
        ─────────────────  ───
        module path          variable name in that module
```
Uvicorn imports `opspilot.api.main`, finds the `app` variable, and starts serving it.

---

## Step 7: `src/opspilot/api/schemas.py`

### What is Pydantic?

Pydantic validates incoming data automatically:
```python
class IncidentRequest(BaseModel):
    incident_id: str        # Must be a string
    alert_title: str        # Must be a string
    service: Optional[str]  # Can be string or None
```

If someone sends `{"incident_id": 123}` (number instead of string), Pydantic either auto-converts it or returns a clear error message.

### All models explained

**`IncidentRequest`** — "Here's the incident, analyze it"
- `incident_id`: unique ID (e.g., "INC-2026-0042")
- `alert_title`: what triggered it (e.g., "NodeDiskRunningFull")
- `service`: which service (e.g., "payment-api") — optional
- `log_lines`: raw log text — list of strings
- `time_range`: when did this happen — optional TimeRange

**`IncidentAnalysisResponse`** — Full agent output
- `summary`: human-readable incident summary
- `anomaly_report`: how abnormal the logs are (score + templates)
- `retrieved_context`: relevant runbook chunks the agent found
- `actions`: recommended steps to fix the issue
- `verification_steps`: how to confirm the fix worked
- `fallback_plan`: what to do if the fix doesn't work
- `postmortem_markdown`: draft postmortem document
- `trace`: debug info showing agent steps

**`RecommendedAction`** — "Do this to fix it"
- `action`: the step (e.g., "Clear disk on node-42")
- `evidence_doc_ids`: which documents support this action
- This is **groundedness enforcement**: no evidence = action gets rejected by safety checks

**`AnomalyReport`** — "How abnormal are these logs?"
- `score`: 0.0 (normal) → 1.0 (highly anomalous)
- `top_templates`: most common log patterns found

**`FeedbackRequest`** — "Was this helpful?"
- After using OpsPilot's suggestion, the engineer gives feedback
- Used to improve the system over time (training data)

### Key Python concept: `Field(default_factory=list)`
```python
log_lines: List[str] = Field(default_factory=list)
```
If the user doesn't send `log_lines`, default to `[]`. Using `default_factory=list` (not `default=[]`) because mutable defaults are a classic Python bug — all instances would share the SAME list!

---

## Step 8: `src/opspilot/api/routes/health.py`

### Why health endpoints matter

1. **Docker** pings `/health` every 30s — if it fails 3 times, container is restarted
2. **Load balancers** check which instances are alive
3. **Monitoring** tools check uptime
4. **First debugging step** — "Does /health work?" If yes, server is up. If no, server crashed.

---

## Step 9: `src/opspilot/observability/logging.py`

### What is structured logging?

**Before** (Python default — ugly, hard to parse):
```
INFO:root:Request received from 192.168.1.5
```

**After** (structlog JSON — machine-readable):
```json
{"event": "request_received", "ip": "192.168.1.5", "timestamp": "2026-02-24T10:00:00Z", "level": "info"}
```

### Why JSON logs matter in production

- Monitoring tools (Loki, CloudWatch, ELK) can filter: "show me all ERROR logs from anomaly service, last hour"
- Scripts can parse JSON automatically
- Every production system at Google/Amazon/Netflix uses structured logging

### How structlog processors work

Each log passes through a chain of processors:
```
log.info("request_received", ip="192.168.1.5")
    │
    ▼ [add_log_level]     → adds {"level": "info"}
    ▼ [TimeStamper]       → adds {"timestamp": "2026-02-24T10:00:00Z"}
    ▼ [JSONRenderer]      → converts to JSON string
    │
    ▼ Output: {"event": "request_received", "ip": "...", "level": "info", "timestamp": "..."}
```

---

## Step 10: `src/opspilot/observability/metrics.py`

### What does Prometheus track?

For EVERY endpoint, automatically:
- **Request count**: how many times called
- **Latency histogram**: how long each request took (buckets: <10ms, <50ms, <100ms, etc.)
- **Status codes**: how many 200s, 404s, 500s

### How the metrics flow works

```
Your API                    Prometheus Server               Grafana
──────────                  ─────────────────               ────────
Exposes GET /metrics  ←───  Scrapes every 10s    ────────→  Pretty dashboards
(text format)               Stores time-series              Queries with PromQL
```

### Why we exclude `/health` from metrics

Health checks happen every 10 seconds per container. With 8 containers, that's 48 health checks/minute → floods metrics with noise, making real API trends invisible.

---

# PHASE 3: Data Download Scripts

---

## Step 11: `scripts/data/download_all.py`

### The two datasets

| Dataset | Source | License | What | How we use it |
|---------|--------|---------|------|--------------|
| **Loghub HDFS** | logpai/loghub | Research/academic | 11M+ real Hadoop log lines with anomaly labels | Train anomaly detection model |
| **Prometheus Runbooks** | prometheus-operator/runbooks | Apache-2.0 | SRE runbooks for Kubernetes alerts | RAG knowledge base |

### How the script works

```
scripts/data/download_all.py
    │
    ├── git clone --depth 1 loghub → external/loghub/ (gitignored)
    │       └── Copy HDFS/HDFS.log → data/raw/hdfs/HDFS.log (DVC-tracked)
    │
    └── git clone --depth 1 runbooks → external/runbooks/ (gitignored)
            └── Copy *.md → data/raw/runbooks/ (DVC-tracked)
```

### Key design decisions

1. **`--depth 1`** — shallow clone saves time (no full git history needed)
2. **`ensure_repo()`** — idempotent: clones first time, pulls updates after
3. **`external/` vs `data/raw/`** — external is gitignored temp storage, data/raw is DVC-tracked versioned data
4. **`Path(__file__).resolve().parents[2]`** — gets project root regardless of where you run the script from

---

# PHASE 4: RAG Pipeline

---

## How RAG Works — The Big Picture

```
User query: "NodeDiskRunningFull alert on payment service"
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                   HYBRID RETRIEVER                     │
│                                                        │
│  ┌─────────────────┐   ┌──────────────────────────┐  │
│  │ FAISS (Vector)   │   │ BM25 (Keyword)           │  │
│  │                   │   │                          │  │
│  │ "disk running     │   │ Exact match:             │  │
│  │  full" ≈ "storage │   │ "NodeDiskRunningFull"    │  │
│  │  capacity low"    │   │ appears in this doc      │  │
│  │                   │   │                          │  │
│  │ score: 0.85       │   │ score: 8.2               │  │
│  └───────┬───────────┘   └──────────┬───────────────┘  │
│          │                          │                    │
│          ▼          FUSION          ▼                    │
│    normalize(0.85)        normalize(8.2)                │
│       = 1.0                  = 1.0                      │
│                                                         │
│    final = 0.6 × vec + 0.4 × bm25                     │
│                                                         │
│  Result: ranked list of relevant runbook chunks          │
└──────────────────────────────────────────────────────────┘
    │
    ▼
  Top 6 chunks go to the LLM agent as "context"
```

---

## Step 12: `src/opspilot/embeddings/encoder.py`

### What are embeddings?

A way to convert text into **numbers** that capture meaning:

```
"Node disk is running full"      → [0.12, -0.34, 0.87, ...]  (384 numbers)
"Disk space filling up on node"  → [0.11, -0.33, 0.85, ...]  (very similar! ≈)
"User logged in successfully"    → [0.78, 0.22, -0.45, ...]  (very different! ≠)
```

Similar texts have similar vectors. This is how RAG finds relevant documents.

### Why `all-MiniLM-L6-v2`?

- **80MB** download — small enough for laptop
- **384 dimensions** — good balance of quality vs speed
- **Trained on 1 billion sentence pairs** — understands semantic similarity
- **Runs on CPU** — no GPU needed
- **~50ms per batch** — fast enough for real-time

### Why disk caching with `diskcache`?

Computing embeddings takes ~50ms per batch. If the same runbook is re-indexed, we'd waste time re-computing. `diskcache` stores results on disk — second call is instant.

Cache key = SHA-256 hash of the text. Same text always maps to same hash.

### Why `normalize_embeddings=True`?

Makes all vectors length 1.0. After normalization:
- **Inner product** (dot product) = **cosine similarity**
- FAISS `IndexFlatIP` uses inner product
- So normalized vectors + IP = cosine similarity search

This is a standard trick in information retrieval.

---

## Step 13: `src/opspilot/rag/chunking.py`

### Why chunk documents?

| Problem | Without chunking | With chunking |
|---------|-----------------|---------------|
| Embedding quality | Poor on long text | Great on paragraphs |
| LLM context | Overflows token limit | Fits easily |
| Precision | Get entire 10-section runbook | Get the specific section you need |

### How overlap works

```
Without overlap (information lost at boundary):
  Chunk 1: "...clear the disk. Restart"
  Chunk 2: "the service after cleanup..."
  ← The sentence "Restart the service after cleanup" is SPLIT! →

With overlap (sentence preserved):
  Chunk 1: "...clear the disk. Restart the service after cleanup..."
  Chunk 2: "Restart the service after cleanup. Verify disk space..."
  ← Complete sentence appears in BOTH chunks →
```

### Prefix trick

Each chunk starts with `"title | section\n"`:
```
"NodeDiskRunningFull | Mitigation\n
To clear disk space, first identify large files..."
```

The embedding now captures BOTH the content AND the source context. Without this, two chunks about "restart pod" from different runbooks would have nearly identical vectors.

---

## Step 14: `src/opspilot/rag/index.py`

### What is FAISS?

Facebook AI Similarity Search — a library for finding the most similar vectors. Even with millions of vectors, it finds matches in milliseconds.

### What is `IndexFlatIP`?

- **Flat** = brute-force (compares query against every vector). Exact results.
- **IP** = Inner Product similarity metric

For ~1000 chunks (our dataset), brute-force is fast. With millions, you'd use `IndexIVFFlat` (approximate search, much faster).

### Persistence format

```
artifacts/vector_index/
├── index.faiss     ← Binary file with all vectors (FAISS format)
└── meta.jsonl      ← One JSON per line — maps position → document metadata
```

FAISS only stores numbers. It doesn't know doc_ids, titles, or text. The `meta.jsonl` file maps vector position #42 → `{doc_id: "runbook:NodeDiskFull:2", title: "...", text: "..."}`.

---

## Step 15: `src/opspilot/rag/docstore.py`

### Why separate from FAISS?

```
FAISS says: "Vector #42 is the closest match"
    → What document is that?
    → DocStore: doc_id = "runbook:NodeDiskFull:2" → {title, text, section, ...}
```

Also provides `all_texts_and_ids()` — BM25 needs raw text for keyword matching.

---

## Step 16: `src/opspilot/rag/bm25.py`

### What is BM25?

The algorithm behind early Google search. Scores documents by keyword matching:

1. **Term frequency** — how often each query word appears in the doc
2. **Inverse document frequency** — penalise common words ("the", "is")
3. **Length normalization** — a 10-page doc mentioning "disk" once is less relevant than a 1-paragraph doc about "disk"

### Why BM25 + FAISS (hybrid)?

| Search Type | Finds | Misses |
|------------|-------|--------|
| **FAISS only** | "storage capacity low" for query "disk full" | Exact term "NodeFilesystemSpaceFillingUp" |
| **BM25 only** | Exact match "NodeFilesystemSpaceFillingUp" | "storage capacity low" (different words, same meaning) |
| **Hybrid** | **Both!** Best of both worlds | Very little |

---

## Step 17: `src/opspilot/rag/retriever.py`

### How score fusion works (detailed example)

```
Query: "NodeFilesystemSpaceFillingUp alert"

FAISS results (semantic):             BM25 results (keyword):
  doc_1: 0.85                           doc_4: 8.2  (exact runbook name!)
  doc_2: 0.72                           doc_1: 3.1
  doc_3: 0.68                           doc_5: 2.8

Step 1: Normalize to [0, 1] (divide by max)
  FAISS: doc_1=1.0, doc_2=0.85, doc_3=0.80
  BM25:  doc_4=1.0, doc_1=0.38, doc_5=0.34

Step 2: Fuse with alpha=0.6
  doc_1: 0.6×1.0 + 0.4×0.38 = 0.75  ← top result (both agree!)
  doc_2: 0.6×0.85 + 0.4×0.0 = 0.51  ← only FAISS found it
  doc_4: 0.6×0.0 + 0.4×1.0 = 0.40   ← only BM25 found it (exact name match!)
  doc_3: 0.6×0.80 + 0.4×0.0 = 0.48
  doc_5: 0.6×0.0 + 0.4×0.34 = 0.14

Final ranking: [doc_1, doc_2, doc_3, doc_4, doc_5]
```

**Without hybrid**: FAISS alone would miss doc_4 (exact runbook name). BM25 alone would miss doc_2 and doc_3 (semantically similar but different words).

---

## Step 18: `scripts/rag/build_index.py`

### What

Offline script that builds the FAISS vector index from runbook markdown files. You run it once (or whenever runbooks change) with `make index`.

### How the full pipeline flows

```
data/raw/runbooks/*.md
    │
    ├── For each .md file:
    │   ├── Read full text
    │   ├── Extract title from filename (e.g., "NodeDiskRunningFull")
    │   ├── Chunk into ~900-word pieces (chunking.py)
    │   └── Create metadata: doc_id, title, section, checksum
    │
    ├── All chunks collected into one list
    │
    ├── FaissStore.build(docs):
    │   ├── Embedder.encode(all texts) → N×384 matrix
    │   ├── faiss.IndexFlatIP.add(vectors)
    │   ├── Write index.faiss (binary vectors)
    │   └── Write meta.jsonl (one JSON per line)
    │
    └── Output: artifacts/vector_index/
            ├── index.faiss   ← vector data
            └── meta.jsonl    ← document metadata
```

### Key design decisions

1. **`doc_id = f"runbook:{title}:{i}"`** — unique ID per chunk. Format: `runbook:NodeDiskRunningFull:0`, `runbook:NodeDiskRunningFull:1`, etc.
2. **SHA-256 checksum** per chunk — detects stale indexes (if checksum changes, runbook was updated)
3. **Sorted file processing** (`sorted(md_files)`) — deterministic order so the same input always produces the same index
4. **Raises RuntimeError if no .md files** — fail loud, not silent

### How it connects to the Makefile

```bash
make index  →  python scripts/rag/build_index.py
```

---

## Step 19: `src/opspilot/api/routes/rag.py`

### What

The `POST /rag/search` REST endpoint. Accepts a query, runs hybrid retrieval, returns ranked runbook chunks.

### Full request/response lifecycle

```
POST /rag/search
  Body: {"query": "disk full on node", "top_k": 6}
    │
    ▼
rag.py route handler
    │
    ├── _get_retriever() [cached with @lru_cache]
    │   ├── FaissStore(INDEX_PATH).load()   ← reads index.faiss + meta.jsonl
    │   ├── DocStore(META_PATH)              ← reads meta.jsonl into memory
    │   └── HybridRetriever(store, docstore) ← builds BM25 index from docstore texts
    │
    ├── retriever.retrieve(query, top_k=6)
    │   ├── FAISS: encode query → vector search → top 12 semantic matches
    │   ├── BM25: keyword score → top 12 lexical matches
    │   ├── Normalize both score sets to [0, 1]
    │   └── Fuse: 0.6 × vector + 0.4 × bm25 → top 6 final results
    │
    └── Return: {"chunks": [{doc_id, title, text, score}, ...]}
```

### Why `@lru_cache` on `_get_retriever()`

Loading the FAISS index + embedding model takes 2-3 seconds. Without caching, every API request would re-load everything. `@lru_cache` means: load once on first request, reuse the same object forever after. This is a common singleton pattern in FastAPI.

### Why fetch `top_k * 2` from each source

The retriever asks FAISS and BM25 for `top_k * 2 = 12` results each, then fuses and returns only `top_k = 6`. This ensures enough candidates survive the fusion step — if we only fetched 6 from each, some good results might get lost after score normalization.

---

# PHASE 5: Anomaly Detection Pipeline

---

## How the Anomaly Pipeline Works — The Big Picture

```
OFFLINE (run once to train):
━━━━━━━━━━━━━━━━━━━━━━━━━━━
HDFS.log → [parse_logs.py] → templates.parquet → [build_features.py] → features.parquet + vocab.json
                                                                              │
                                                                              ▼
                                                                    [train_anomaly.py]
                                                                         │        │
                                                                  model.pkl    MLflow logs

ONLINE (every API request):
━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST /anomaly/score {log_lines: [...]} → [features.py] → feature vector → [infer.py] → score 0-1
                                         (uses same vocab.json)            (uses same model.pkl)
```

The critical connection is the **shared vocabulary** (`anomaly_vocab.json`). Both offline and online pipelines use it to ensure feature vector positions match.

---

## Step 20: `scripts/features/parse_logs.py`

### What

Reads raw HDFS log lines, runs each through Drain3, outputs a parquet table of `(line, cluster_id, template)`.

### How Drain3 processes logs

```
Input:  "081109 203615 148 INFO dfs.DataNode: Receiving block blk_123 src: /10.250.19.102"
Drain3:  cluster_id=1, template="INFO dfs.DataNode: Receiving block <*> src: <*>"

Input:  "081109 203615 149 INFO dfs.DataNode: Receiving block blk_456 src: /10.250.19.103"
Drain3:  cluster_id=1, template="INFO dfs.DataNode: Receiving block <*> src: <*>"
         ↑ Same template! Block ID and IP are just variables (<*>)
```

### Key design decisions

1. **Parquet output** — 10x smaller than CSV, columnar access, industry standard
2. **`MAX_LINES = 500000`** — full HDFS has 11M+ lines, 500K is enough for training
3. **`errors="replace"`** — handles corrupted encoding in real log files
4. **`drain3.ini` config** — masking replaces numbers→NUM, hex→HEX before parsing

---

## Step 21: `scripts/features/build_features.py`

### What

Converts parsed templates into **feature vectors** — lists of numbers the ML model can learn from.

### How template counting works

```
Drain3 found 300 unique templates: T1="disk full", T2="user login", T3="block received", ...

Window 1 (lines 0-499):                    Window 2 (lines 500-999):
  T1 appeared 2 times                        T1 appeared 0 times
  T2 appeared 45 times                       T2 appeared 50 times
  T3 appeared 120 times                      T3 appeared 0 times (!!!) ← unusual!
  → vec: [2, 45, 120, 0, 0, ...]             → vec: [0, 50, 0, 0, 0, ...]
                                                     ↑ IsolationForest will flag this
```

### What is the vocabulary?

Not all 300+ templates are useful. The **vocabulary** is the top 300 most frequent templates. We save this to `artifacts/anomaly_vocab.json`. The online featurizer (Step 23) loads the SAME vocab to produce matching vectors.

### Why window size = 500 lines?

Too small (10 lines) → mostly zeros, noisy. Too large (10000 lines) → anomalies hidden in average. 500 lines ≈ a 5-minute window in a busy system.

---

## Step 22: `scripts/train/train_anomaly.py`

### What

Trains IsolationForest on feature vectors and logs everything to MLflow.

### How IsolationForest works (visual)

```
Normal data (clustered):              Anomalous data (isolated):
  ● ● ●                                    ○
  ● ● ● ●     Takes MANY random                Takes VERY FEW random
  ● ● ●       splits to isolate one             splits to isolate
               = deep in tree = NORMAL           = shallow in tree = ANOMALOUS
```

Key insight: anomalies are rare and different → easy to isolate. Normal points are clustered → hard to isolate. Isolation depth = anomaly score.

### Key parameters

| Parameter | Value | Why |
|-----------|-------|-----|
| `n_estimators` | 150 | Number of trees. More = better but slower. 150 is a good balance. |
| `contamination` | 0.01 | Expect ~1% anomalies. Conservative — avoids flooding with false alarms. |
| `random_state` | 42 | Reproducible results across runs. |
| `n_jobs` | -1 | Use all CPU cores for parallel training. |

### What MLflow tracks

```python
mlflow.log_params({...})    → hyperparameters (n_estimators, contamination, etc.)
mlflow.log_metrics({...})   → train_time, mean_score, std_score, anomaly_pct
mlflow.log_artifact(...)    → the trained model.pkl file itself
```

Later you can compare experiments in the MLflow UI:
"Did 200 trees with 0.02 contamination perform better than 150 trees with 0.01?"

### Output

`models/anomaly_model.pkl` — serialised IsolationForest, ~5MB, loads in <1s.

---

## Step 23: `src/opspilot/anomaly/features.py`

### What

The **online featurizer** — real-time version of `build_features.py`. Converts raw log lines from API requests into feature vectors.

### Offline vs Online comparison

| | Offline (`build_features.py`) | Online (`features.py`) |
|---|---|---|
| Input | Millions of lines from parquet | 10-100 lines from API request |
| Vocab | Builds from scratch | Loads from `anomaly_vocab.json` |
| Output | Saves features to parquet | Returns vector in memory |
| When | Once during training | Every API request |
| Speed | Minutes | Milliseconds |

### Why vocab consistency is critical

If offline vocab says position #0 = template "disk full", the online featurizer MUST also put "disk full" counts at position #0. Otherwise the model sees data in wrong slots → meaningless scores.

Both load the same `artifacts/anomaly_vocab.json` → guaranteed consistency.

### Extra output: top_templates

Besides the feature vector, it returns the 5 most common templates found. This gives the on-call engineer human-readable context: "Your logs are dominated by 'disk full' and 'connection timeout' patterns."

---

## Step 24: `src/opspilot/anomaly/infer.py`

### What

Loads the trained model and scores feature vectors. The main function `score_logs()` is the single entry point.

### Score normalization explained

```
sklearn's decision_function output:
  +0.3  = very normal
   0.0  = borderline
  -0.3  = very anomalous

Our normalization (0.5 - raw):
  +0.3 → 0.2  (normal)
   0.0 → 0.5  (borderline)
  -0.3 → 0.8  (anomalous)

Clamped to [0, 1]: score = max(0, min(1, 0.5 - raw))
```

Now engineers see intuitive numbers: 0.0 = fine, 1.0 = red alert.

### Return format

```python
{
    "score": 0.65,              # 0-1 anomaly score
    "top_templates": [...],     # Human-readable template list
    "details": {
        "raw_isolation_score": -0.15,   # For debugging
        "n_lines": 50,
        "n_features": 300
    }
}
```

---

## Step 25: `src/opspilot/api/routes/anomaly.py`

### What

`POST /anomaly/score` endpoint — thinnest route handler in the project (15 lines).

### Full request lifecycle

```
POST /anomaly/score  {"log_lines": ["ERROR disk full ...", "WARN timeout ...", ...]}
    │
    ▼
anomaly.py route handler (THIS FILE — 3 lines of logic)
    │
    ├── Validates input with Pydantic (AnomalyScoreRequest)
    ├── Calls infer.score_logs(req.log_lines)
    │       ├── LogFeaturizer.featurize(lines) → vector + templates
    │       └── IsolationForest.decision_function(vec) → normalized score
    └── Returns AnomalyReport(score=0.65, top_templates=[...], details={...})
```

### Thin controller pattern

The route ONLY does: validate input → call service → return response. All ML logic lives in `infer.py` → `features.py`. This is clean separation — routes are easy to test, ML code is reusable.

---

# PHASE 6: Storage (SQL + Feedback)

---

## Step 26: `src/opspilot/storage/db.py`

### What

Sets up the database connection using SQLModel. Works with SQLite (local dev) or PostgreSQL (Docker).

### Engine vs Session (restaurant analogy)

```
Engine = connection to the kitchen (database). Created once, shared by everyone.
Session = one order ticket. Open it, do queries, close it.

engine = create_engine(DATABASE_URL)  # Connect to kitchen (once at startup)

with Session(engine) as session:      # Open order ticket
    session.add(feedback)             # Write an order
    session.commit()                  # Send to kitchen
    # ticket auto-closes
```

### How `get_session()` works with FastAPI

```python
def get_session():
    with Session(engine) as session:
        yield session    # ← give session to route handler
    # ← auto-closes after route finishes
```

`yield` makes this a generator. FastAPI's `Depends()` calls it, gives the session to the route, then cleans up. In tests, you swap in a fake session pointing to a test database.

### SQLite vs PostgreSQL

| | SQLite | PostgreSQL |
|---|---|---|
| Setup | Zero (single file) | Docker container |
| Concurrency | One writer at a time | Many concurrent writers |
| When | Local development | Docker / production |
| Switch | `DATABASE_URL=sqlite:///./opspilot.db` | `DATABASE_URL=postgresql+psycopg://...` |

---

## Step 27: `src/opspilot/storage/models.py`

### What

Defines the `FeedbackRow` database table using SQLModel.

### How SQLModel maps Python to SQL

```python
class FeedbackRow(SQLModel, table=True):        # Python class
    id: int | None = Field(primary_key=True)     # → id INTEGER PRIMARY KEY
    incident_id: str = Field(index=True)         # → incident_id TEXT + INDEX
    helpful: bool                                 # → helpful BOOLEAN
    tags: List[str] = Field(sa_column=Column(JSON))  # → tags JSON
    comment: Optional[str] = None                 # → comment TEXT NULL
    created_at: datetime                          # → created_at TIMESTAMP
```

### Design decisions

- **`index=True` on `incident_id`** — fast lookups by incident (O(log n) vs O(n))
- **`sa_column=Column(JSON)` for tags** — SQLite doesn't support arrays, so we store as JSON string
- **`created_at` with UTC** — always store in UTC, convert for display

### Why store feedback

1. **Improvement signal** — if 80% of disk-full analyses are "not helpful," runbooks need updating
2. **Quality dashboard** — helpful % over time
3. **Future fine-tuning** — human-labeled data for model training
4. **Audit trail** — what did the system recommend?

---

## Step 28: `src/opspilot/api/routes/feedback.py`

### What

`POST /feedback` endpoint with FastAPI dependency injection.

### Full request lifecycle

```
POST /feedback  {"incident_id": "INC-42", "helpful": true, "tags": ["fast"], "comment": "Spot on!"}
    │
    ▼
feedback.py route handler
    │
    ├── Pydantic validates input (FeedbackRequest)
    ├── Depends(get_session) injects a database session
    ├── Create FeedbackRow from request data
    ├── session.add(row)       ← stage the insert
    ├── session.commit()       ← write to database
    ├── session.refresh(row)   ← reload to get auto-generated id
    └── Return: {"id": 7, "status": "saved"}
```

### Why `session.refresh(row)`

After `commit()`, the database auto-generates the `id` (primary key). Python doesn't know the `id` yet. `refresh(row)` re-reads from database so `row.id` is populated for the response.

### Dependency injection pattern

```python
def submit_feedback(req: FeedbackRequest, session: Session = Depends(get_session)):
#                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                   FastAPI calls get_session(), passes result as `session`
#                   Route handler doesn't create its own session
#                   In tests, you inject a fake session
```

---

# REMAINING STEPS (Quick Reference)

## Phase 7: Agent Orchestration (LangGraph)
- **Step 29**: `src/opspilot/agent/prompts.py` — system prompt enforcing JSON + evidence
- **Step 30**: `src/opspilot/agent/safety.py` — validate_grounded_actions (reject actions without evidence)
- **Step 31**: `src/opspilot/agent/tools.py` — tool functions (retrieve, anomaly_score)
- **Step 32**: `src/opspilot/agent/graph.py` — LangGraph state machine: parse→anomaly→retrieve→draft→done
- **Step 33**: `src/opspilot/api/routes/incident.py` — POST /incident/analyze

## Phase 8-14
- Steps 34-57: Auth, Streamlit UI, Evaluation, DVC, Prefect, Tests, CI/CD, Docs, Ship

---

# Key Concepts Cheat Sheet

| Concept | What it means | Interview answer |
|---------|--------------|-----------------|
| **RAG** | Retrieval Augmented Generation | "Find relevant docs first, then generate with LLM using those docs as context" |
| **FAISS** | Facebook AI Similarity Search | "Vector similarity search library for finding semantically similar documents" |
| **BM25** | Best Matching 25 | "Keyword-based ranking algorithm using TF-IDF with length normalization" |
| **Hybrid Retrieval** | Vector + keyword fusion | "Combines semantic understanding with exact keyword matching for better recall" |
| **Drain3** | Streaming log parser | "Discovers templates from raw log lines, enabling log pattern analysis at scale" |
| **IsolationForest** | Anomaly detection | "Unsupervised ML model that learns normal patterns and flags outliers" |
| **LangGraph** | Agent framework | "State machine for building multi-step AI agents with tool use and branching" |
| **Groundedness** | Evidence enforcement | "Every recommended action must cite source documents — prevents hallucinations" |
| **App Factory** | Design pattern | "Wrap app setup in create_app() for clean testing and configuration" |
| **structlog** | Structured logging | "JSON-formatted logs that are machine-readable and searchable" |
| **DVC** | Data Version Control | "Git for data — tracks large files without bloating the repo" |
| **MLflow** | Experiment tracking | "Logs hyperparameters, metrics, and model artifacts for reproducibility" |

---

# Comment Style Guide

### ✅ DO (professional)
- Class and function **docstrings** — always
- **Section headers** in long files: `# ── Incident ──`
- Comments explaining **WHY** something non-obvious: `# Normalize so inner product = cosine similarity`
- Brief note on design decisions: `# Excludes /health to avoid metric noise`

### ❌ DON'T (suspicious, looks AI-generated)
- `# Import FastAPI` above `from fastapi import FastAPI`
- `# This is the score value` above `score: float`
- Comments on every single line
- Re-stating what the code already says
