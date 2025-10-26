# CODEX.instructions.md

This file provides guidance to Codex when working with code in this repository.

## Development Commands

### Running the Application
```bash
uv sync                        # Install dependencies
make migrate                   # Apply database migrations
make serve                     # Start development server at http://localhost:8000
```

### Testing and Code Quality
```bash
make test                      # Run all tests with pytest
uv run pytest tests/test_api/  # Run specific test package
make lint                      # Check code with ruff
make format                    # Format code with ruff
make check                     # Run lint + tests (pre-commit workflow)
```

### Database Migrations
```bash
make migrate                      # Apply latest migrations
make revision msg="description"   # Generate new migration
make downgrade                    # Roll back last migration
```

### Running Single Tests
```bash
uv run pytest tests/test_services/test_rating_service.py::test_specific_function
uv run pytest -k "test_pattern"  # Run tests matching pattern
```

## Architecture Overview

This FastAPI application follows **Clean Architecture** with strict layer separation:

### Core Layers

1. **Models** (`app/models/`) - Pydantic schemas for validation
2. **Database** (`app/db/models.py`) - SQLAlchemy ORM models
3. **Repositories** (`app/repositories/`) - Data access layer with CRUD operations
4. **Services** (`app/services/`) - Business logic layer coordinating between repositories
5. **Routers** (`app/routers/`) - HTTP handlers split between:
   - `frontend.py` - Server-rendered HTML with Jinja2 templates
   - Other routers - JSON REST APIs with `/api/v1` prefix

### Key Patterns

**Dependency Injection**: Services and repositories are injected via FastAPI dependencies defined in `app/core/dependencies.py`. The `get_db()` dependency provides SQLAlchemy sessions.

**Repository Pattern**: All database access goes through repositories. Each repository encapsulates queries for a specific domain entity (users, spots, ratings, sessions, etc.).

**Hybrid API Design**: Most endpoints accept both JSON payloads and HTML form data to support both REST clients and HTMX-driven frontend forms.

**Activity Feed**: The social feed uses an event sourcing pattern:
- Services record activities via `ActivityRepository.create()`
- Activity metadata stored as JSON for flexibility
- `NotificationService` processes activities to generate targeted notifications
- Batched follower notification processing for memory efficiency

**Notification System**:
- `NotificationService._build_message()` generates human-readable messages
- Message selection uses `_select_message()` with condition tuples for fallback logic
- Always include an unconditional fallback `(True, "generic message")` as the last candidate
- Metadata augmentation via `_augment_metadata()` includes context like spot names, session titles

**Rate Limiting**: In-memory rate limiter defined in `app/core/rate_limiter.py`. Apply via `dependencies=[rate_limited(RULE)]` in router decorators. Suitable for single-instance deployments only.

### Critical Implementation Details

**Timestamps**: Always use timezone-aware UTC timestamps via `datetime.now(timezone.utc)`. Import `timezone` from `datetime` module.

**SQLAlchemy Queries**: Avoid `.unique()` calls unless using `joinedload` that causes row duplication.

**HTMX Patterns**:
- Templates in `templates/partials/` are HTMX snippets
- Use `hx-trigger="load"` for initial load and `every Xs` for polling
- Include loading indicators in dynamic components
- See `templates/partials/spot_check_ins.html` for reference pattern

**Template UUID Comparisons**: Cast UUIDs to strings when comparing in Jinja2 templates to avoid hex formatting issues: `actor.id|string == current_user.id|string`

**Logging**: Application uses structlog for structured logging. All logs include request context via `RequestContextLogMiddleware`. Configure with `SKATE_SPOTS_LOG_LEVEL` and `SKATE_SPOTS_LOG_JSON` environment variables.

## Testing Strategy

Tests are organized by architectural layer mirroring the app structure:
- `tests/test_models/` - Pydantic validation and schema tests
- `tests/test_repositories/` - Database layer tests
- `tests/test_services/` - Business logic tests with mocked dependencies
- `tests/test_api/` - Integration tests for HTTP endpoints

**Test Philosophy**:
- Each test validates a single piece of functionality
- No bundled CRUD workflows (create, read, update, delete tested separately)
- External services mocked using FastAPI's dependency override system
- No actual external API calls (geocoding uses mocked geopy)
- All tests use in-memory SQLite fixtures from `conftest.py`

**Adding Tests**: When creating new repositories, services, or routers, add corresponding test files in the appropriate `tests/test_*` directory.

## Code Style Conventions

- **Line length**: 100 characters (enforced by ruff)
- **Quotes**: Double quotes throughout
- **Type hints**: Full type annotations required
- **Imports**: Auto-sorted by ruff
- **Docstrings**: Required for all public functions and classes

## Repository Workflow

- Run `make format` and `make check` before every commit so linting and tests pass locally.
- Group related changes into a single commit with an imperative subject (e.g. `Add real-time spot check-ins`).
- Keep following the existing patterns: services in `app/services/`, repositories in `app/repositories/`, HTMX snippets under `templates/partials/`.
- Use timezone-aware UTC timestamps (`datetime.now(timezone.utc)`) when adding new models or migrations; import `timezone` from `datetime`.
- Avoid pessimistic `.unique()` calls in SQLAlchemy queries unless a `joinedload` causes duplication.
- Update `README.md` whenever new REST endpoints or HTMX widgets ship.
- Call out new Alembic migrations and ensure `make migrate` stays the way to apply them.

## Configuration

Settings managed via Pydantic in `app/core/config.py`. Set environment variables with `SKATE_SPOTS_` prefix or use a `.env` file:

```bash
SKATE_SPOTS_DATABASE_URL=sqlite:///skate_spots.db
SKATE_SPOTS_SECRET_KEY=your-secret-key
SKATE_SPOTS_ACCESS_TOKEN_EXPIRE_MINUTES=30
SKATE_SPOTS_LOG_LEVEL=INFO
SKATE_SPOTS_LOG_JSON=false
SKATE_SPOTS_GEOCODING_USER_AGENT=skate-spots-app
SKATE_SPOTS_MEDIA_DIRECTORY=./media
SKATE_SPOTS_MEDIA_URL_PATH=/media
```

## Database Schema

Key ORM models in `app/db/models.py`:
- `UserORM` - Authentication and profiles
- `SkateSpotORM` - Spot locations with photos
- `RatingORM` - User ratings (1-5 scores)
- `CommentORM` - Qualitative feedback (separate from ratings)
- `SessionORM` - Scheduled meetups with RSVP
- `UserFollowORM` - Social graph relationships
- `ActivityFeedORM` - Event sourcing for social feed
- `NotificationORM` - User notifications
- `CheckInORM` - Real-time spot presence

Migrations live in `alembic/versions/` numbered sequentially (0001, 0002, etc.).

## Entry Point

Application bootstraps in `main.py`:
- Routers mounted with `/api/v1` prefix (except `frontend.router`)
- Static files served from `/static` and `/media` directories
- Rate limiter attached to `app.state.rate_limiter`
- Logging middleware injects request IDs and correlation context

Feel free to edit this file to add more team conventions.
