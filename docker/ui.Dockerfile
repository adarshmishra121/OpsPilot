FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

# Install deps (with ui extra, without dev)
COPY pyproject.toml /app/pyproject.toml
RUN poetry install --no-interaction --without dev --no-root -E ui

# Copy application code
COPY src /app/src
RUN poetry install --no-interaction --without dev --only main -E ui

COPY ui /app/ui

EXPOSE 8501

CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
