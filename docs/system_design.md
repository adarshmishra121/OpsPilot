# OpsPilot — System Design Document

## Overview

OpsPilot is an AI-powered incident response copilot that combines:
- **RAG** for knowledge retrieval from SRE runbooks
- **Anomaly detection** for log pattern analysis
- **LLM agents** for incident summarization and action planning

## Architecture Decision Records (ADRs)

### ADR-1: Why LangGraph over raw LangChain?

**Context:** We need a multi-step agent pipeline with deterministic execution order.

**Decision:** LangGraph's `StateGraph` with explicit node edges.

**Rationale:**
- LangChain's `AgentExecutor` uses free-form LLM-driven tool calls — non-deterministic
- LangGraph enforces `parse → anomaly → retrieve → draft → validate` — always runs all steps
- State is a typed dict, not a blackbox — easier to debug and test
- Each node is a pure function — unit testable independently

### ADR-2: Why Hybrid RAG (FAISS + BM25)?

**Context:** Need to retrieve relevant runbook sections given incident descriptions.

**Decision:** Hybrid retrieval with alpha-weighted score fusion.

**Rationale:**
- FAISS alone misses exact alert names (e.g., "NodeFilesystemSpaceFillingUp")
- BM25 alone misses semantic matches (e.g., "disk full" ≈ "storage capacity low")
- Hybrid with alpha=0.6 (60% vector, 40% keyword) catches both
- Alpha is configurable in `params.yaml` for DVC experiments

### ADR-3: Why IsolationForest for Anomaly Detection?

**Context:** Need to score how "anomalous" a set of log lines is.

**Decision:** Drain3 template extraction → IsolationForest scoring.

**Rationale:**
- IsolationForest is unsupervised — no labeled anomaly data needed
- Drain3 converts free-text logs to structured template counts
- Lightweight: trains in seconds on 500K+ lines, infers in milliseconds
- Alternative (LSTM autoencoders) requires GPU and more training data

### ADR-4: Why Mock LLM as Default?

**Context:** Not everyone has Ollama or GPUs for local LLM inference.

**Decision:** `LLM_PROVIDER=mock` returns templated JSON responses.

**Rationale:**
- CI/CD pipeline can test the full agent without any LLM
- Demo-able in interviews without internet or GPU
- Architecture is identical — only the LLM response changes
- Switch to real LLM by setting `LLM_PROVIDER=ollama` in `.env`

### ADR-7: Why Qwen2.5:7B as the Production LLM?

**Context:** OpsPilot requires the LLM to produce strict, machine-parseable JSON with no extra prose. The `validate_node` reads `draft_response["actions"]` directly — a single stray sentence outside the JSON object causes a `JSONDecodeError` and drops the entire response.

**Decision:** `OLLAMA_MODEL=qwen2.5:7b` is the recommended model for OpsPilot.

**Rationale:**
- **Structured output compliance:** Qwen2.5 was trained with heavy instruction-following and JSON-mode datasets. In practice it outputs well-formed JSON far more consistently than similarly-sized Llama models, which tend to prefix responses with prose like "Here is the analysis:" before the JSON block — breaking our parser.
- **Strong instruction following at 7B scale:** Qwen2.5:7b matches or exceeds Llama-3:8b on instruction-following benchmarks (IFEval) while being the same 4.7 GB quantized size.
- **Better multilingual context:** Qwen2.5 handles mixed technical content (log lines, markdown runbooks, CLI commands) more reliably than Llama base models due to a broader pretraining corpus.
- **Efficient quantization:** The Q4_K_M quantization of Qwen2.5:7b retains >98% of full-precision quality while fitting in ~5 GB VRAM — runnable on a single consumer GPU alongside the FAISS index.
- **Ollama-native support:** `ollama pull qwen2.5:7b` works out of the box; the model is officially maintained in the Ollama model library with a tested system-prompt template.

**Why not Llama 3?**
- Llama 3:8b is an excellent general-purpose model but outputs conversational prose around JSON, requiring fragile post-processing regex to extract the JSON block.
- Llama models were initially used during early prototyping (`llama3.2:3b-instruct-q4_K_M` was the original default in `tools.py`) but replaced after observing consistent structured-output failures in the `draft_node`.
- For pure chat or open-ended reasoning Llama 3 is competitive; for schema-constrained JSON generation, Qwen2.5 is the better fit.

**Configuration:**
```bash
# .env
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

**Tradeoff:** Qwen2.5:7b requires ~5 GB VRAM. On CPU-only machines, inference takes 3–8 minutes per request — acceptable for async batch workflows but not for interactive use. For CPU-only environments, use `LLM_PROVIDER=mock` during development.

### ADR-5: Why Safety Validation (Groundedness Check)?

**Context:** LLMs hallucinate — they may suggest actions not supported by evidence.

**Decision:** `validate_grounded_actions()` filters actions without cited doc_ids.

**Rationale:**
- Production SRE actions have real consequences (restarting services, clearing data)
- Every suggested action MUST cite a retrieved document as evidence
- Actions without evidence are silently filtered out
- Better to suggest fewer actions than suggest wrong/dangerous ones
### ADR-6: Why Prefect/Evidently/MLflow Are External Dependencies

**Context:** CI and Docker builds fail because `drain3` pins `cachetools==4.2.1` (exact version) while `prefect` requires `cachetools>=5.3`. Poetry resolves ALL dependency groups — even optional ones — at resolution time, making `--without` ineffective for version conflicts.

**Decision:** Remove `prefect`, `evidently`, and `mlflow` from `pyproject.toml` entirely. Install them via `pip install prefect evidently mlflow` only when running MLOps workflows.

**Rationale:**
- Poetry `--without` only controls installation, not resolution — optional groups still cause resolver failures
- The core application (API, agent, RAG, anomaly) does NOT need these packages at runtime
- `prefect_flows.py` and `drift.py` use try-except import wrappers for graceful degradation
- CI and Docker builds stay fast and conflict-free
- MLOps engineers install the extra packages in their own environments

**Tradeoff:** MLOps dependencies are not lockfile-pinned, so version drift is possible in workflow environments. Mitigated by documenting exact install commands.

## Data Flow Diagram

```text
POST /incident/analyze
  │
  ▼
parse_node: extract incident_id, alert_title, service from request
  │
  ▼
anomaly_node: log_lines → Drain3 templates → IsolationForest → score (0.0–1.0)
  │
  ▼
retrieve_node: alert_title → HybridRetriever → top 6 runbook chunks
  │
  ▼
draft_node: incident + anomaly + context → LLM → JSON response
  │
  ▼
validate_node: filter actions where evidence ∉ retrieved_docs
  │
  ▼
IncidentAnalysisResponse (JSON)
