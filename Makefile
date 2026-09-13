.PHONY: install lint format format-check test test-cov clean \
	run-bff run-crud run-process run-inference run-geo run-frontend \
	docker-build docker-up docker-down

install:
	uv sync --all-packages
	uv run pre-commit install

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

test:
	uv run pytest -v

test-cov:
	uv run pytest --cov=bff --cov=crud --cov=process --cov=inference --cov=geo \
		--cov=sirena_schema --cov=frontend --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage

run-bff:
	uv run --package bff uvicorn bff.main:app --reload --port 8000

run-crud:
	uv run --package crud uvicorn crud.main:app --reload --port 8001

run-process:
	uv run --package process uvicorn process.main:app --reload --port 8002

run-inference:
	uv run --package inference uvicorn inference.main:app --reload --port 8003

run-geo:
	uv run --package geo uvicorn geo.main:app --reload --port 8004

run-frontend:
	uv run --package frontend streamlit run frontend/src/frontend/streamlit_app.py

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
