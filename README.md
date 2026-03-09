# 🛡️ OpsPilot — AI-Powered Incident Response Copilot

> **AIOps + RAG + Tool-Using Agents** — An intelligent system that analyzes production incidents,
> retrieves relevant runbooks, detects anomalies, and generates actionable incident response plans.

[![CI](https://github.com/adarshmishra121/OpsPilot/actions/workflows/ci.yml/badge.svg)](https://github.com/adarshmishra121/OpsPilot/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard                         │
│                   (ui/streamlit_app.py)                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │ POST /incident/analyze
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ /health  │  │ /incident│  │ /rag     │  │ /admin       │   │
│  │          │  │ /analyze │  │ /search  │  │ /clear-cache │   │
│  └──────────┘  └────┬─────┘  └──────────┘  └──────────────┘   │
│                     │                                           │
│              LangGraph Agent                                    │
│   ┌─────┐  ┌───────┐  ┌────────┐  ┌─────┐  ┌────────┐        │
│   │Parse│→ │Anomaly│→ │Retrieve│→ │Draft│→ │Validate│        │
│   └─────┘  └───────┘  └────────┘  └─────┘  └────────┘        │
│                │            │          │                        │
│       ┌────────┘     ┌──────┘   ┌──────┘                       │
│       ▼              ▼          ▼                               │
│  IsolationForest   FAISS    LLM (Ollama                        │
│  + Drain3          + BM25    or Mock)                           │
└─────────────────────────────────────────────────────────────────┘
         │                                    │
    ┌────┘                               ┌────┘
    ▼                                    ▼
 SQLite/Postgres                    Prometheus
 (Feedback)                         + Grafana
```

---

## ✨ Key Features

- **🧠 LangGraph Agent** — 5-node state machine: parse → anomaly → retrieve → draft → validate
- **📚 Hybrid RAG** — FAISS (semantic) + BM25 (keyword) retrieval with score fusion
- **📊 Anomaly Detection** — Drain3 log parsing + IsolationForest scoring
- **🛡️ Safety Validation** — Rejects hallucinated actions without cited evidence
- **🔐 JWT Auth + RBAC** — Role-based access control with optional auth
- **📈 Observability** — Prometheus metrics + structured JSON logging
- **🔄 Reproducible Pipeline** — DVC-managed: download → parse → train → index → eval
- **⏰ Automated Workflows** — Prefect flows for nightly reindex and weekly retrain
- **📉 Drift Detection** — Evidently monitors feature distribution shifts

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI + Uvicorn |
| Agent Orchestration | LangGraph (LangChain) |
| Vector Search | FAISS + sentence-transformers |
| Keyword Search | rank-bm25 |
| Log Parsing | Drain3 |
| Anomaly Detection | scikit-learn IsolationForest |
| LLM | Ollama (local) or Mock |
| Database | SQLModel (SQLite / PostgreSQL) |
| UI | Streamlit |
| Observability | Prometheus + Grafana + structlog |
| Pipeline | DVC + Prefect |
| Drift Monitoring | Evidently |
| CI/CD | GitHub Actions |
| Containerization | Docker + Docker Compose |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/adarshmishra121/OpsPilot.git
cd OpsPilot

# Install
pip install -e ".[dev]"

# Download data + build pipeline
python scripts/data/download_all.py
python scripts/features/parse_logs.py
python scripts/features/build_features.py
python scripts/train/train_anomaly.py
python scripts/rag/build_index.py

# Run API
uvicorn opspilot.api.main:app --reload --port 8000

# Run UI (separate terminal)
streamlit run ui/streamlit_app.py
```

Or with Docker:
```bash
docker compose up --build
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/incident/analyze` | Full agent pipeline |
| POST | `/rag/search` | Standalone RAG search |
| POST | `/anomaly/score` | Standalone anomaly scoring |
| POST | `/feedback` | Submit analysis feedback |
| GET | `/admin/health` | Detailed system health (admin) |
| POST | `/admin/clear-cache` | Clear model caches (admin) |
| GET | `/admin/feedback-stats` | Feedback aggregates (admin) |

Interactive docs: `http://localhost:8000/docs`

---

## 📁 Project Structure

```
OpsPilot/
├── src/opspilot/          # Main package
│   ├── api/               # FastAPI routes + schemas
│   ├── agent/             # LangGraph agent + safety
│   ├── rag/               # FAISS + BM25 hybrid retrieval
│   ├── anomaly/           # Drain3 + IsolationForest
│   ├── embeddings/        # Sentence-transformer encoder
│   ├── storage/           # SQLModel database
│   ├── workflows/         # Prefect flows + drift detection
│   └── observability/     # Logging + Prometheus metrics
├── ui/                    # Streamlit dashboard
├── scripts/               # Data download, training, evaluation
├── tests/                 # API contract + safety tests
├── docker/                # Dockerfiles + compose
├── docs/                  # Architecture docs + build guide
└── data/                  # Raw data + eval gold set
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
