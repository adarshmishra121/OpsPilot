FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps needed by FAISS and some pip packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry (handles complex dep resolution better than pip)
RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

# Install Python deps first (layer caching: code changes won't re-trigger install)
COPY pyproject.toml /app/pyproject.toml
RUN poetry install --no-interaction --without dev --no-root

# Copy application code
COPY src /app/src

# Install the project itself (editable)
RUN poetry install --no-interaction --without dev --only-root

COPY scripts /app/scripts

# Create artifact/model dirs (populated at runtime via DVC or volume mounts)
RUN mkdir -p /app/artifacts /app/models

EXPOSE 8000

CMD ["uvicorn", "opspilot.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
