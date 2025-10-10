.PHONY: help install dev lint format test serve clean check migrate revision downgrade

help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Install with dev dependencies"
	@echo "  lint       - Check code with ruff"
	@echo "  format     - Format code with ruff"
	@echo "  test       - Run tests with pytest"
	@echo "  serve      - Start development server"
	@echo "  check      - Run lint and tests"
	@echo "  migrate    - Apply database migrations"
	@echo "  revision   - Create a new Alembic revision (msg=\"description\")"
	@echo "  downgrade  - Roll back the last Alembic migration"
	@echo "  clean      - Clean cache files"

install:
	uv sync

dev:
	uv sync --group dev

lint:
	uv run ruff check

format:
	uv run ruff format

test:
	uv run pytest

serve:
	uv run uvicorn main:app --reload

check: lint test

migrate:
	uv run alembic upgrade head

revision:
	@if [ -z "$(msg)" ]; then \
		echo "Usage: make revision msg=\"Short description\""; \
		exit 1; \
	fi
	uv run alembic revision --autogenerate -m "$(msg)"

downgrade:
	uv run alembic downgrade -1

clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
