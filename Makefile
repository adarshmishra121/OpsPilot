.PHONY: setup lint test up down data features train index repro api ui

# Install all dependencies in editable mode
setup:
	python -m pip install --upgrade pip
	pip install -e ".[api,ui]"
	pre-commit install || true

lint:
	ruff check .
	mypy src/opspilot

test:
	pytest -q

# Docker Compose full stack
up:
	docker compose up --build

down:
	docker compose down -v

# Offline data pipeline (run in order: data → features → train → index)
data:
	python scripts/data/download_all.py

features:
	python scripts/features/parse_logs.py
	python scripts/features/build_features.py

train:
	python scripts/train/train_anomaly.py

index:
	python scripts/rag/build_index.py

# Reproduce entire DVC pipeline
repro:
	dvc repro

# Local development servers
api:
	uvicorn opspilot.api.main:app --reload --port 8000

ui:
	streamlit run ui/streamlit_app.py
