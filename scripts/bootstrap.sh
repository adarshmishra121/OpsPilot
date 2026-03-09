#!/bin/bash
# OpsPilot — One-command bootstrap
# Usage: bash scripts/bootstrap.sh

set -e  # Exit on any error

echo "🛡️ OpsPilot Bootstrap"
echo "===================="

echo ""
echo "📦 Step 1/6: Installing Python dependencies..."
pip install -e ".[dev]"

echo ""
echo "📥 Step 2/6: Downloading datasets..."
python scripts/data/download_all.py

echo ""
echo "🔍 Step 3/6: Parsing logs into templates..."
python scripts/features/parse_logs.py

echo ""
echo "📊 Step 4/6: Building feature vectors..."
python scripts/features/build_features.py

echo ""
echo "🤖 Step 5/6: Training anomaly model..."
python scripts/train/train_anomaly.py

echo ""
echo "📚 Step 6/6: Building search index..."
python scripts/rag/build_index.py

echo ""
echo "✅ Bootstrap complete!"
echo ""
echo "Start the API:  uvicorn opspilot.api.main:app --reload --port 8000"
echo "Start the UI:   streamlit run ui/streamlit_app.py"
echo "Or use Docker:  docker compose up --build"
