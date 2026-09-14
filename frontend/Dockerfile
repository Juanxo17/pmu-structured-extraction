# Build context: raiz del repo (ver docker-compose.yml)
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY common/sirena-schema ./common/sirena-schema
COPY frontend ./frontend

RUN uv sync --package frontend --frozen --no-dev

EXPOSE 8501
CMD ["uv", "run", "--package", "frontend", "streamlit", "run", "frontend/frontend/streamlit_app.py", "--server.address=0.0.0.0"]
