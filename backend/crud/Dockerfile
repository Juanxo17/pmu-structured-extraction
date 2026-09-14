# Build context: raiz del repo (ver docker-compose.yml)
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY common/sirena-schema ./common/sirena-schema
COPY config ./config
COPY backend/crud ./backend/crud

RUN uv sync --package crud --frozen --no-dev

EXPOSE 8001
CMD ["uv", "run", "--package", "crud", "uvicorn", "crud.main:app", "--host", "0.0.0.0", "--port", "8001"]
