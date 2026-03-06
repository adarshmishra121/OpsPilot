"""OpsPilot — Incident Response Console (Streamlit UI)."""

import streamlit as st
import httpx

API_URL = "http://localhost:8000"

st.set_page_config(page_title="OpsPilot", page_icon="🛡️", layout="wide")
st.title("🛡️ OpsPilot — Incident Response Console")

# ── Sidebar: Incident Input ──────────────────────────────────

with st.sidebar:
    st.header("📋 Incident Details")
    incident_id = st.text_input("Incident ID", value="INC-2026-0001")
    alert_title = st.text_input("Alert Title", value="NodeDiskRunningFull")
    service = st.text_input("Service", value="payment-api")
    environment = st.text_input("Environment", value="production")
    log_lines_raw = st.text_area(
        "Log Lines (one per line)",
        value="ERROR disk usage at 95% on /dev/sda1\nWARN inode count critical on node-42\nERROR write failed: no space left on device",
        height=200,
    )
    analyze_btn = st.button("🔍 Analyze Incident", type="primary", use_container_width=True)

# ── Main Area: Results ────────────────────────────────────────

if analyze_btn:
    log_lines = [l.strip() for l in log_lines_raw.strip().split("\n") if l.strip()]

    payload = {
        "incident_id": incident_id,
        "alert_title": alert_title,
        "service": service,
        "environment": environment,
        "log_lines": log_lines,
    }

    with st.spinner("Running agent pipeline: parse → anomaly → retrieve → draft → validate..."):
        try:
            resp = httpx.post(f"{API_URL}/incident/analyze", json=payload, timeout=120.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.ConnectError:
            st.error("❌ Cannot connect to API. Is the server running on port 8000?")
            st.stop()
        except httpx.HTTPStatusError as e:
            st.error(f"❌ API error: {e.response.status_code} — {e.response.text}")
            st.stop()

    # ── Anomaly Score ──
    st.divider()
    col1, col2, col3 = st.columns(3)
    score = data.get("anomaly_report", {}).get("score", 0)
    col1.metric("🔴 Anomaly Score", f"{score:.2f}", delta=None)
    col2.metric("📄 Log Lines Analyzed", len(log_lines))
    col3.metric("📚 Runbooks Retrieved", len(data.get("retrieved_context", [])))

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "📚 Context", "🔧 Actions", "📝 Postmortem"])

    with tab1:
        st.subheader("Incident Summary")
        st.write(data.get("summary", "No summary available."))
        templates = data.get("anomaly_report", {}).get("top_templates", [])
        if templates:
            st.subheader("Top Log Templates")
            for t in templates:
                st.code(t)

    with tab2:
        st.subheader("Retrieved Runbook Chunks")
        for i, chunk in enumerate(data.get("retrieved_context", [])):
            with st.expander(f"#{i+1} — {chunk.get('doc_id', 'unknown')} (score: {chunk.get('score', 0):.3f})"):
                st.markdown(chunk.get("text", ""))

    with tab3:
        st.subheader("Recommended Actions")
        actions = data.get("actions", [])
        if not actions:
            st.warning("No grounded actions found. The safety validator filtered all suggestions.")
        for i, action in enumerate(actions):
            st.markdown(f"**{i+1}.** {action.get('action', '')}")
            refs = action.get("evidence_doc_ids", [])
            if refs:
                st.caption(f"Evidence: {', '.join(refs)}")

        st.subheader("Verification Steps")
        for step in data.get("verification_steps", []):
            st.checkbox(step, value=False, key=f"verify_{step}")

        st.subheader("Fallback Plan")
        for step in data.get("fallback_plan", []):
            st.info(step)

    with tab4:
        st.subheader("Draft Postmortem")
        st.markdown(data.get("postmortem_markdown", "*No postmortem generated.*"))

    # ── Trace ──
    with st.expander("🔍 Agent Trace (debug)"):
        st.json(data.get("trace", {}))
