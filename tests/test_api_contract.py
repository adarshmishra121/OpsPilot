"""API contract tests: verify every endpoint returns correct schemas."""

from unittest.mock import patch
from fastapi.testclient import TestClient

from opspilot.api.main import app

client = TestClient(app)

# Dummy successful agent response matching the schema
DUMMY_AGENT_RESPONSE = {
    "final_response": {
        "summary": "Mock summary",
        "actions": [{"action": "restart", "description": "Restart"}],
        "verification_steps": [],
        "fallback_plan": [],
        "postmortem_markdown": "## Mock"
    },
    "anomaly_result": {"score": 0.5, "top_templates": []},
    "retrieved_chunks": []
}


class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_has_version(self):
        resp = client.get("/health")
        assert "version" in resp.json()


class TestIncidentEndpoint:
    @patch("opspilot.api.routes.incident.agent.invoke")
    def test_analyze_returns_200(self, mock_invoke):
        mock_invoke.return_value = DUMMY_AGENT_RESPONSE
        payload = {
            "incident_id": "INC-TEST-001",
            "alert_title": "TestAlert",
            "service": "test-service",
            "log_lines": ["ERROR test log line"],
        }
        resp = client.post("/incident/analyze", json=payload)
        assert resp.status_code == 200

    @patch("opspilot.api.routes.incident.agent.invoke")
    def test_analyze_response_shape(self, mock_invoke):
        mock_invoke.return_value = DUMMY_AGENT_RESPONSE
        payload = {
            "incident_id": "INC-TEST-002",
            "alert_title": "TestAlert",
            "log_lines": [],
        }
        resp = client.post("/incident/analyze", json=payload)
        data = resp.json()
        assert "summary" in data
        assert "anomaly_report" in data
        assert "actions" in data
        assert "trace" in data

    def test_analyze_missing_fields_returns_422(self):
        resp = client.post("/incident/analyze", json={})
        assert resp.status_code == 422


class TestRAGEndpoint:
    def test_search_returns_200(self):
        resp = client.post("/rag/search", json={"query": "disk full", "top_k": 3})
        assert resp.status_code == 200

    def test_search_response_has_chunks(self):
        resp = client.post("/rag/search", json={"query": "test"})
        assert "chunks" in resp.json()
        assert isinstance(resp.json()["chunks"], list)


class TestFeedbackEndpoint:
    def test_feedback_returns_200(self):
        payload = {
            "incident_id": "INC-TEST-001",
            "helpful": True,
            "tags": ["accurate"],
            "comment": "Test feedback",
        }
        resp = client.post("/feedback", json=payload)
        assert resp.status_code == 200


class TestAdminEndpoint:
    def test_admin_health_returns_200(self):
        resp = client.get("/admin/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_clear_cache_returns_200(self):
        resp = client.post("/admin/clear-cache")
        assert resp.status_code == 200
        assert "cleared" in resp.json()
