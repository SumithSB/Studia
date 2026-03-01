# Studia backend: run with Ollama on host; set OLLAMA_BASE_URL for container→host.
FROM python:3.12-slim

WORKDIR /app
COPY backend/ /app/backend/
COPY web/ /app/web/

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

WORKDIR /app/backend
EXPOSE 8000

# Default: SQLite at /app/backend/data. Override DATABASE_URL for Postgres.
# From host, use OLLAMA_BASE_URL=http://host.docker.internal:11434 (Mac/Windows).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
