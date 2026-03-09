"""Shared pytest fixtures for OpsPilot test suite."""

import os
import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Ensure tests always run with mock LLM and disabled auth."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")


@pytest.fixture
def sample_incident():
    """Standard incident payload for testing."""
    return {
        "incident_id": "INC-TEST-001",
        "alert_title": "NodeDiskRunningFull",
        "service": "payment-api",
        "environment": "production",
        "log_lines": [
            "ERROR disk usage at 95% on /dev/sda1",
            "WARN inode count critical on node-42",
            "ERROR write failed: no space left on device",
        ],
    }
