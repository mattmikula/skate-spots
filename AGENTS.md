# Repository Guidelines

## Project Structure & Module Organization
Application code lives in `app/`, split into FastAPI `routers/`, data `repositories/`, domain `services/`, shared `core/`, and integration `adapters/`. ORM models are under `app/models/`, while HTML templates and static assets stay in `templates/` and `static/`. Uploaded photos are stored in `media/` (served at `/media`, ignored by git). Database migrations live in `alembic/`, and the public ASGI entrypoint is `main.py`. Tests mirror the runtime layout inside `tests/` (`test_api/`, `test_services/`, etc.) to keep concerns aligned.

## Build, Test, and Development Commands
Use the Makefile shortcuts (all wrap `uv`): `make dev` installs prod + dev deps, `make serve` runs `uvicorn main:app --reload`, and `make migrate` applies Alembic upgrades. Quality gates include `make lint` (ruff check), `make format` (ruff format), `make mypy`, `make test`, `make coverage`, and `make check` (lint + type + coverage). Schema changes rely on `make revision msg="Add spot type"` and `make downgrade` rolls the last migration.

## Coding Style & Naming Conventions
Python 3.12, four-space indentation, and `ruff` enforce the style: 100-character lines, double quotes, import sorting, and Bugbear/pyupgrade rules. Keep modules focused, prefer dependency-injected services/repositories, and type every public function; `mypy` currently targets `app/core`. Name routers by feature (`routers/spots.py`), services with verbs (`services/notifications.py`), and tests with `test_<unit>.py`. Run `make format` before committing.

## Testing Guidelines
All tests use `pytest` with async support and live under `tests/`. File names start with `test_`, test classes with `Test*`, and functions with `test_*`. Apply markers (`@pytest.mark.unit`, `integration`, `slow`) so CI can select subsets. Maintain ≥75% coverage (`uv run coverage run -m pytest` + `coverage report`). Prefer fixture-driven tests in `conftest.py`, and mirror the app module you are exercising (`tests/test_repositories/test_spots.py`).

## Commit & Pull Request Guidelines
Follow the existing log style: short, imperative summaries with optional scope and PR reference, e.g., `Add comprehensive tests for NotificationRepository (#62)`. Each PR should describe the change, list verification steps (`make check`, screenshots for UI tweaks), mention database or config migrations, and link any GitHub issues. Keep commits focused (one feature or fix) so reviewers can bisect easily.

## Security & Configuration Tips
Runtime settings come from `.env` files via `pydantic-settings` with the `SKATE_SPOTS_` prefix. Override the default `SECRET_KEY`, `DATABASE_URL`, and geocoding user agent per environment, and never commit real secrets or local `skate_spots.db` snapshots. Ensure uploads under `media/` stay out of version control, and when contributing migrations, test both upgrade and downgrade paths against a fresh SQLite file.
