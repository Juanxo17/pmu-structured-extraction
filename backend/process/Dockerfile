# Build context: raiz del repo (ver docker-compose.yml)
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY common/sirena-schema ./common/sirena-schema
COPY config ./config
COPY backend/process ./backend/process

RUN uv sync --package process --frozen --no-dev

EXPOSE 8002
CMD ["uv", "run", "--package", "process", "uvicorn", "process.main:app", "--host", "0.0.0.0", "--port", "8002"]
