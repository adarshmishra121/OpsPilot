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

### ADR-5: Why Safety Validation (Groundedness Check)?

**Context:** LLMs hallucinate — they may suggest actions not supported by evidence.

**Decision:** `validate_grounded_actions()` filters actions without cited doc_ids.

**Rationale:**
- Production SRE actions have real consequences (restarting services, clearing data)
- Every suggested action MUST cite a retrieved document as evidence
- Actions without evidence are silently filtered out
- Better to suggest fewer actions than suggest wrong/dangerous ones

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
