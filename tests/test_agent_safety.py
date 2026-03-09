"""Tests for agent safety: groundedness validation must reject ungrounded actions."""

import pytest
from opspilot.agent.safety import validate_grounded_actions


class TestGroundedActions:
    """Every action must cite evidence from retrieved documents."""

    def test_grounded_action_passes(self):
        """Action citing a real doc_id should survive validation."""
        actions = [{"action": "Clear /tmp", "evidence_doc_ids": ["runbook:NodeDiskFull:0"]}]
        retrieved_ids = {"runbook:NodeDiskFull:0", "runbook:NodeDiskFull:1"}
        result = validate_grounded_actions(actions, retrieved_ids)
        assert len(result) == 1
        assert result[0]["action"] == "Clear /tmp"

    def test_ungrounded_action_rejected(self):
        """Action citing unknown doc_id should be filtered out."""
        actions = [{"action": "Delete everything", "evidence_doc_ids": ["fake:doc:99"]}]
        retrieved_ids = {"runbook:NodeDiskFull:0"}
        result = validate_grounded_actions(actions, retrieved_ids)
        assert len(result) == 0

    def test_empty_evidence_rejected(self):
        """Action with no evidence should be filtered out."""
        actions = [{"action": "Restart pods", "evidence_doc_ids": []}]
        retrieved_ids = {"runbook:NodeDiskFull:0"}
        result = validate_grounded_actions(actions, retrieved_ids)
        assert len(result) == 0

    def test_mixed_actions_filtered(self):
        """Only grounded actions survive from a mixed set."""
        actions = [
            {"action": "Clear /tmp", "evidence_doc_ids": ["runbook:NodeDiskFull:0"]},
            {"action": "Restart world", "evidence_doc_ids": []},
            {"action": "Scale pods", "evidence_doc_ids": ["fake:doc:1"]},
        ]
        retrieved_ids = {"runbook:NodeDiskFull:0", "runbook:NodeDiskFull:1"}
        result = validate_grounded_actions(actions, retrieved_ids)
        assert len(result) == 1
        assert result[0]["action"] == "Clear /tmp"

    def test_empty_actions_returns_empty(self):
        """No actions in = no actions out."""
        result = validate_grounded_actions([], {"runbook:NodeDiskFull:0"})
        assert result == []

    def test_empty_retrieved_rejects_all(self):
        """If no docs were retrieved, all actions are ungrounded."""
        actions = [{"action": "Do something", "evidence_doc_ids": ["runbook:X:0"]}]
        result = validate_grounded_actions(actions, set())
        assert len(result) == 0
