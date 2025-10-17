.PHONY: help install lint format test serve clean check migrate makemigrations shell createsuperuser

help:
	@echo "Skate Spots - Available commands:"
	@echo "  install         - Install dependencies with uv"
	@echo "  lint            - Check code with ruff"
	@echo "  format          - Format code with ruff"
	@echo "  test            - Run tests with pytest"
	@echo "  serve           - Start Django development server"
	@echo "  check           - Run lint and tests"
	@echo "  migrate         - Apply database migrations"
	@echo "  makemigrations  - Create new migrations"
	@echo "  shell           - Open Django shell"
	@echo "  createsuperuser - Create Django superuser"
	@echo "  clean           - Clean cache files"

install:
	uv sync

lint:
	uv run ruff check accounts spots ratings skate_spots_project

format:
	uv run ruff format accounts spots ratings skate_spots_project

test:
	uv run pytest

serve:
	uv run python manage.py runserver

check: lint test

migrate:
	uv run python manage.py migrate

makemigrations:
	uv run python manage.py makemigrations

shell:
	uv run python manage.py shell

createsuperuser:
	uv run python manage.py createsuperuser

clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
