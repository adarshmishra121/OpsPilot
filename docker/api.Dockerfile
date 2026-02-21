FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps needed by FAISS and some pip packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer caching: code changes won't re-trigger pip)
COPY pyproject.toml /app/pyproject.toml
RUN pip install --upgrade pip && pip install -e ".[api]"

# Copy application code
COPY src /app/src
COPY scripts /app/scripts
COPY artifacts /app/artifacts
COPY models /app/models

EXPOSE 8000

CMD ["uvicorn", "opspilot.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
