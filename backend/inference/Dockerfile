# Build context: raiz del repo (ver docker-compose.yml)
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY common/sirena-schema ./common/sirena-schema
COPY config ./config
COPY backend/inference ./backend/inference

RUN uv sync --package inference --frozen --no-dev

EXPOSE 8003
CMD ["uv", "run", "--package", "inference", "uvicorn", "inference.main:app", "--host", "0.0.0.0", "--port", "8003"]
