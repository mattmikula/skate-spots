# Codex Working Guidelines for Skate Spots

## Commit Hygiene
- Group related changes into a single commit and keep the message imperative (e.g. `Add real-time spot check-ins`).
- Run `make format` and `make check` before every commit so ruff and pytest pass locally.

## Code Style
- Prefer the existing patterns: FastAPI services live in `app/services`, repositories in `app/repositories`, HTMX snippets under `templates/partials`.
- Use timezone-aware UTC timestamps (`datetime.now(timezone.utc)`) when adding new models or migrations; import `timezone` from `datetime` as needed. Keep Pydantic models in ASCII.
- Avoid pessimistic `.unique()` calls on SQLAlchemy queries unless a joinedload creates row duplication.

## Frontend
- New HTMX components should include load indicators and use the `hx-trigger="load"` / `every 60s` polling pattern already in `templates/partials/spot_check_ins.html`.
- When comparing UUIDs in templates, cast to strings (`actor.id|string`) to avoid hex formatting mismatches.

## Testing
- Any new repository, service, or router should come with focused tests under `tests/test_repositories`, `tests/test_services`, or `tests/test_api`.
- Tests can rely on the in-memory SQLite fixtures from `tests/conftest.py`; avoid real-file I/O.

## Documentation
- Update `README.md` whenever new REST endpoints or HTMX widgets ship.
- Mention new Alembic migrations and ensure `make migrate` remains the way to apply them.

Feel free to edit this file to add more team conventions.
