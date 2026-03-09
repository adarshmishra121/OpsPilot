"""API contract tests: verify every endpoint returns correct schemas."""

import pytest
from fastapi.testclient import TestClient

from opspilot.api.main import app

client = TestClient(app)


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
    def test_analyze_returns_200(self):
        payload = {
            "incident_id": "INC-TEST-001",
            "alert_title": "TestAlert",
            "service": "test-service",
            "log_lines": ["ERROR test log line"],
        }
        resp = client.post("/incident/analyze", json=payload)
        assert resp.status_code == 200

    def test_analyze_response_shape(self):
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

    def test_search_response_is_list(self):
        resp = client.post("/rag/search", json={"query": "test"})
        assert isinstance(resp.json(), list)


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
