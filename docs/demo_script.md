# OpsPilot — Interview Demo Script

> **Duration**: 10-15 minutes  
> **Goal**: Walk the interviewer through your project confidently  

---

## Opening (1 min)

> "I built OpsPilot — an AI-powered incident response copilot. When an on-call engineer gets paged at 3 AM, they submit the incident details. OpsPilot analyzes the logs, finds relevant runbooks, and suggests concrete actions — all with cited evidence."

**Key phrase to say**: "It combines three AI techniques: RAG for knowledge retrieval, anomaly detection for log analysis, and LLM agents for reasoning."

---

## Part 1: Show Architecture (2 min)

Open `README.md` on GitHub and point to the architecture diagram.

**Talk through the flow:**

> "The Streamlit UI sends a POST to the FastAPI backend. The LangGraph agent runs 5 nodes in sequence: parse the incident, score anomaly, retrieve runbooks, draft a response with LLM, then validate that every suggested action has cited evidence."

**Key talking points:**
- "It's a **5-node state machine**, not a free-form agent — deterministic execution"
- "**Hybrid RAG** — FAISS for semantic search plus BM25 for keyword matching"
- "**Safety validation** — filters out any LLM hallucinations without evidence"

---

## Part 2: Show Code (3 min)

### File 1: `src/opspilot/agent/graph.py` (30 sec)

> "This is the LangGraph state machine. Each node is a pure function. The edges are explicit — parse, then anomaly, then retrieve, then draft, then validate. No ambiguity."

### File 2: `src/opspilot/agent/safety.py` (30 sec)

> "This is the groundedness validator. Every action the LLM suggests must cite a document from the retrieved context. If it can't cite evidence, the action gets filtered out. Better to suggest nothing than suggest something wrong."

### File 3: `src/opspilot/rag/retriever.py` (30 sec)

> "Hybrid retrieval — I combine vector search with BM25 keyword search. Vector search finds 'disk space low' when you search 'storage full'. BM25 finds exact alert names like 'NodeFilesystemSpaceFillingUp'. Combined, you get the best of both."

### File 4: `src/opspilot/anomaly/infer.py` (30 sec)

> "Anomaly detection — Drain3 converts raw log lines into template patterns, then IsolationForest scores how unusual the pattern distribution is. Score of 0 means normal, 1 means highly anomalous."

### File 5: `dvc.yaml` (30 sec)

> "The entire pipeline is reproducible with DVC. One command — `dvc repro` — runs download, parse, train, index, and evaluate. It skips stages where inputs haven't changed."

---

## Part 3: Show It Running (3 min)

### Option A: With API running

```bash
# Terminal 1 (already running)
uvicorn opspilot.api.main:app --reload --port 8000

# Terminal 2: Quick demo
curl http://localhost:8000/health
curl -X POST http://localhost:8000/incident/analyze \
  -H "Content-Type: application/json" \
  -d '{"incident_id":"DEMO","alert_title":"NodeDiskRunningFull","log_lines":["ERROR disk full"]}'
```

### Option B: Without running (show Swagger)

> "The API auto-generates interactive documentation. Here's every endpoint with request/response schemas."

Open: `http://localhost:8000/docs`

---

## Part 4: Testing & CI/CD (1 min)

> "I have two types of tests: **contract tests** that verify every endpoint returns the right shape, and **safety tests** that verify the groundedness validator rejects hallucinated actions."

> "CI runs on every push — ruff for linting, pytest for tests. Docker builds are separate and only trigger when Dockerfiles change."

---

## Part 5: MLOps & Observability (1 min)

> "Every training run is logged to MLflow with hyperparameters and metrics. The DVC pipeline tracks data versions. Evidently detects when log patterns drift from training data — if drift is detected, we trigger retraining."

> "Prometheus scrapes API metrics every 10 seconds. I can see request latency, error rates, and anomaly score distributions in Grafana."

---

## Anticipated Questions & Answers

### Q: "How would you scale this for production?"
> A: "Three things: (1) Replace SQLite with PostgreSQL — already supported via `DATABASE_URL`. (2) Replace mock LLM with vLLM on GPU for real inference. (3) Put the API behind a load balancer with multiple replicas — each is stateless."

### Q: "What would you improve next?"
> A: "Two things: (1) Add a feedback loop — when engineers rate actions as helpful/unhelpful, use that to fine-tune the retriever's alpha weight. (2) Add streaming responses — the LLM already uses streaming internally via `httpx.stream`, but exposing SSE tokens to the UI would show progress in real time."

### Q: "Why Qwen2.5:7B over Llama?"
> A: "Two reasons: structured output and instruction following. OpsPilot's `draft_node` feeds the raw LLM response directly into `json.loads()` — any prose outside the JSON block causes a parse failure. Qwen2.5:7b consistently outputs clean JSON because it was trained on heavy instruction-following and JSON-mode datasets. Llama 3 is a great general model but tends to prefix answers with conversational text like 'Here is my analysis:' before the JSON, which breaks the parser. We prototyped with Llama initially and switched to Qwen2.5:7b after observing the structured-output improvement."

### Q: "Did you fine-tune the LLM?"
> A: "No — and that's intentional. Fine-tuning an LLM for incident response would require thousands of labeled incident→action pairs, which most teams don't have. Instead, OpsPilot uses the LLM purely as a reasoning engine: the knowledge lives in the runbook RAG index, not baked into model weights. This means you can update the runbooks and get better answers without any retraining."

### Q: "How do you handle hallucinations?"
> A: "The safety validator in `safety.py` checks every suggested action. Each action must cite a `doc_id` from the retrieved context. If the LLM invents a citation that doesn't exist in our retrieved documents, it gets filtered out. I have 6 unit tests covering edge cases — empty evidence, fake doc_ids, mixed valid/invalid actions."

### Q: "Why not just use ChatGPT API?"
> A: "Three reasons: (1) **Data privacy** — production logs contain sensitive information, can't send to external APIs. (2) **Reproducibility** — mock mode lets us test and demo without API costs or internet. (3) **Control** — LangGraph gives us deterministic execution order, not free-form agent wandering."

### Q: "How good is the retrieval?"
> A: "I measure MRR and Recall@K against a 12-query gold set. MRR tells me if the right document is in the top results. Recall@K tells me what fraction of relevant documents are found. I can compare metrics across experiments with `dvc metrics diff`."

---

## Closing Statement

> "OpsPilot is a full production pipeline — from data download to model training to API serving to UI dashboard. Everything is reproducible, tested, and documented. I built it to demonstrate that I can architect and implement end-to-end ML systems, not just train models."

---

## Quick Prep Checklist

Before the interview:
- [ ] `git clone` the repo on your demo machine
- [ ] Run `bash scripts/bootstrap.sh` (takes ~5 min)
- [ ] Start API: `uvicorn opspilot.api.main:app --port 8000`
- [ ] Open `http://localhost:8000/docs` in browser
- [ ] Test: `curl http://localhost:8000/health`
- [ ] Have `docs/build_guide.md` open for reference
