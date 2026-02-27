"""Safety guardrails: validate that agent outputs are grounded in evidence."""

from typing import Any, Dict, List

import structlog

logger = structlog.get_logger()


def validate_grounded_actions(
    actions: List[Dict[str, Any]],
    known_doc_ids: set[str],
) -> List[Dict[str, Any]]:
    """Filter actions to only those citing valid evidence documents.

    Any action whose evidence_doc_ids are empty or reference unknown
    documents is rejected.  This prevents the agent from recommending
    unsubstantiated remediation steps.
    """
    grounded = []
    for action in actions:
        refs = action.get("evidence_doc_ids", [])
        valid_refs = [r for r in refs if r in known_doc_ids]
        if valid_refs:
            action["evidence_doc_ids"] = valid_refs
            grounded.append(action)
        else:
            logger.warning(
                "action_rejected_no_evidence",
                action=action.get("action", "unknown"),
                refs=refs,
            )
    return grounded
