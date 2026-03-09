#!/bin/bash
# OpsPilot API — Example curl commands for every endpoint

BASE="http://localhost:8000"

echo "=== Health Check ==="
curl -s "$BASE/health" | python -m json.tool

echo ""
echo "=== Incident Analysis ==="
curl -s -X POST "$BASE/incident/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2026-0042",
    "alert_title": "NodeDiskRunningFull",
    "service": "payment-api",
    "environment": "production",
    "log_lines": [
      "ERROR disk usage at 95% on /dev/sda1",
      "WARN inode count critical on node-42",
      "ERROR write failed: no space left on device"
    ]
  }' | python -m json.tool

echo ""
echo "=== RAG Search ==="
curl -s -X POST "$BASE/rag/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "NodeDiskRunningFull alert", "top_k": 3}' | python -m json.tool

echo ""
echo "=== Anomaly Score ==="
curl -s -X POST "$BASE/anomaly/score" \
  -H "Content-Type: application/json" \
  -d '{"log_lines": ["ERROR disk full", "WARN inode critical"]}' | python -m json.tool

echo ""
echo "=== Submit Feedback ==="
curl -s -X POST "$BASE/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2026-0042",
    "helpful": true,
    "tags": ["accurate", "clear"],
    "comment": "Actions were spot-on"
  }' | python -m json.tool

echo ""
echo "=== Admin Health ==="
curl -s "$BASE/admin/health" | python -m json.tool

echo ""
echo "=== Admin Clear Cache ==="
curl -s -X POST "$BASE/admin/clear-cache" | python -m json.tool

echo ""
echo "=== Admin Feedback Stats ==="
curl -s "$BASE/admin/feedback-stats" | python -m json.tool
