# Skate Spots API

[![CI](https://github.com/yourusername/skate-spots/workflows/CI/badge.svg)](https://github.com/yourusername/skate-spots/actions)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/downloads/)

A modern FastAPI application for sharing and discovering skateboarding spots around the world. Built with clean architecture principles, comprehensive testing, and professional development practices.

## 🛹 Features

- **Interactive Web Frontend** built with HTMX for dynamic user interactions
- **REST API** for managing skate spots with full CRUD operations
- **Secure Authentication** with registration, login, and cookie-based JWT tokens
- **Rich Data Model** with locations, difficulty levels, and spot types
- **Comprehensive Validation** using Pydantic models
- **Clean Architecture** with separation of concerns
- **Extensive Testing** with focused, single-responsibility tests
- **Auto-generated Documentation** with OpenAPI/Swagger
- **Code Quality** tools with ruff linting and formatting
- **Modern Tooling** with uv package manager and Makefile commands
- **Database Integration** with SQLAlchemy and SQLite

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd skate-spots

# Install dependencies (creates virtual environment automatically)
uv sync
```

### Running the Application

```bash
# Apply database migrations
make migrate

# Start the development server with hot reload
make serve
# Or directly: uv run uvicorn main:app --reload
```

The application will be available at:
- **Web Frontend**: http://localhost:8000/skate-spots
- **Authentication Pages**: http://localhost:8000/login and http://localhost:8000/register
- **API Base**: http://localhost:8000/api/v1
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication Workflow

1. **Register** using the HTML form at `/register` or the API endpoint `POST /api/v1/auth/register`.
2. **Login** via `/login` or `POST /api/v1/auth/login` to receive an access token stored in an HTTP-only cookie.
3. Authenticated requests automatically include the cookie; access the current user with `GET /api/v1/auth/me`.
4. **Logout** using the button in the UI or `POST /api/v1/auth/logout` to clear the cookie.

The JSON API endpoints also accept traditional form submissions for HTMX-driven pages.

### Development Commands

```bash
# Run all tests
make test
# Or directly: uv run pytest

# Run specific test packages
uv run pytest tests/test_models/        # Model validation tests
uv run pytest tests/test_services/      # Service layer tests
uv run pytest tests/test_api/           # API integration tests

# Check code quality
make lint          # Check code with ruff
make format        # Format code with ruff
make check         # Run both lint and tests

# Database migrations
make migrate       # Apply the latest migrations
make revision msg="add new feature"  # Generate a migration skeleton
make downgrade     # Roll back the last migration

# Available make commands
make help          # Show all available commands
```

## ⚙️ Configuration

The application reads runtime settings via `app/core/config.py`, powered by Pydantic. Set environment variables with the `SKATE_SPOTS_` prefix (for example, `SKATE_SPOTS_DATABASE_URL`) or provide them in a local `.env` file. By default the API stores data in `sqlite:///skate_spots.db` in the project root.

Key configuration values:

- `SKATE_SPOTS_DATABASE_URL` – Database connection string.
- `SKATE_SPOTS_SECRET_KEY` – Secret used to sign JWT access tokens (change this in production).
- `SKATE_SPOTS_ACCESS_TOKEN_EXPIRE_MINUTES` – Lifetime of authentication tokens (default 30 minutes).

## 🚦 Rate Limiting

The application protects sensitive endpoints with lightweight, in-memory rate limiting:

- `POST /api/v1/auth/login` and `POST /api/v1/auth/login/form` share a budget of **5 requests per minute per IP address**.
- `POST /api/v1/auth/register` and `POST /api/v1/auth/register/form` share the same **5 requests per minute** window.
- Mutating skate spot endpoints (`POST`, `PUT`, and `DELETE` under `/api/v1/skate-spots/`) allow up to **50 requests per minute per IP**.

When a limit is exceeded, the API returns HTTP 429 with a descriptive error and a `Retry-After` header indicating when it is safe to retry. Limits can be adjusted centrally in `app/core/rate_limiter.py`.

To apply an existing limit to an endpoint, add the `rate_limited(...)` dependency to the router decorator. For example:

```python
from app.core.rate_limiter import SKATE_SPOT_WRITE_LIMIT, rate_limited


@router.post("/api/v1/skate-spots/", dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)])
async def create_spot(...):
    ...
```

Creating a brand new limit requires defining a `RateLimitRule` and reusing it with `rate_limited(...)`, keeping configuration in one place and avoiding placeholder parameters in route handlers.

## 🗃️ Database Migrations

Database schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/). Run `make migrate` after pulling new code to ensure your database schema is up to date. Use `make revision msg="describe change"` to generate migration skeletons when evolving the schema.

## 📋 Endpoints

### Web Frontend Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Home page |
| `GET` | `/skate-spots` | View all skate spots (HTML) |
| `GET` | `/skate-spots/new` | Create new spot form |
| `GET` | `/skate-spots/{id}/edit` | Edit spot form |
| `GET` | `/map` | Interactive map view |
| `GET` | `/login` | Login form (redirects if already authenticated) |
| `GET` | `/register` | Registration form (redirects if already authenticated) |

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/skate-spots/` | List all skate spots (JSON) |
| `POST` | `/api/v1/skate-spots/` | Create a new skate spot (JSON or form data) |
| `GET` | `/api/v1/skate-spots/{id}` | Get a specific skate spot (JSON) |
| `PUT` | `/api/v1/skate-spots/{id}` | Update a skate spot (JSON or form data) |
| `DELETE` | `/api/v1/skate-spots/{id}` | Delete a skate spot |

**Note**: The API endpoints accept both JSON payloads and HTML form data, making them compatible with both traditional API clients and HTMX-powered forms.

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Create a new user account (JSON or form data) |
| `POST` | `/api/v1/auth/login` | Authenticate and receive a JWT access token cookie |
| `POST` | `/api/v1/auth/logout` | Clear the authentication cookie |
| `GET` | `/api/v1/auth/me` | Retrieve the currently authenticated user |

### Example Usage

**Create a Skate Spot:**
```bash
curl -X POST "http://localhost:8000/api/v1/skate-spots/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Downtown Rails",
    "description": "Great set of rails perfect for grinding practice",
    "spot_type": "rail",
    "difficulty": "intermediate",
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "address": "123 Main St",
      "city": "New York",
      "country": "USA"
    },
    "is_public": true,
    "requires_permission": false
  }'
```

**List All Spots:**
```bash
curl http://localhost:8000/api/v1/skate-spots/
```

**Register a User:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "skater@example.com",
    "username": "kickflip_master",
    "password": "super-secure-password"
  }'
```

**Login and Store Cookie:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "kickflip_master",
    "password": "super-secure-password"
  }'
```

**Fetch Current User:**
```bash
curl "http://localhost:8000/api/v1/auth/me" -b cookies.txt
```

## 🏗️ Architecture

This project follows **Clean Architecture** principles with clear separation of concerns:

```
skate-spots/
├── alembic/              # Database migrations
│   ├── env.py            # Alembic environment configuration
│   ├── script.py.mako    # Migration file template
│   └── versions/         # Individual migration revisions
│       └── 0001_create_skate_spots_table.py
├── app/
│   ├── core/             # Shared configuration & security helpers
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── security.py
│   ├── db/               # Database layer
│   │   ├── database.py          # Database configuration
│   │   └── models.py            # SQLAlchemy models
│   ├── models/           # Pydantic data models
│   │   ├── skate_spot.py
│   │   └── user.py
│   ├── repositories/     # Data access layer
│   │   ├── skate_spot_repository.py
│   │   └── user_repository.py
│   ├── routers/          # FastAPI route handlers
│   │   ├── auth.py              # Authentication API
│   │   ├── frontend.py          # HTML/HTMX routes
│   │   └── skate_spots.py       # REST API routes
│   └── services/         # Business logic layer
│       └── skate_spot_service.py
├── static/               # Static assets
│   └── style.css         # Application styles
├── templates/            # Jinja2 HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Spots list page
│   ├── login.html        # Login form
│   ├── map.html          # Interactive map view
│   ├── register.html     # Registration form
│   ├── spot_card.html    # Spot card component
│   └── spot_form.html    # Create/edit form
├── tests/                # Test suite (organized by app structure)
│   ├── test_api/         # API integration tests
│   │   ├── test_auth.py         # Authentication endpoint tests
│   │   ├── test_frontend.py     # Frontend route tests
│   │   ├── test_root.py         # Root & docs endpoints
│   │   └── test_skate_spots.py  # CRUD endpoint tests
│   ├── test_models/      # Model validation tests
│   │   ├── test_skate_spot.py   # Skate spot model tests
│   │   └── test_user.py         # User model tests
│   ├── test_services/    # Service layer tests
│   │   └── test_skate_spot_service.py  # Repository & service tests
│   └── conftest.py       # Test configuration
├── main.py               # Application entry point
├── Makefile              # Development commands
└── pyproject.toml        # Project configuration
```

### Architecture Layers

1. **Configuration Layer** (`app/core/`)
   - Centralised Pydantic settings and environment management
   - Security utilities for password hashing and JWT creation
   - Dependency helpers for resolving authenticated users

2. **Database Layer** (`app/db/`)
   - SQLAlchemy ORM models
   - Database session management
   - SQLite (or configured database) integration

3. **Models Layer** (`app/models/`)
   - Pydantic models for data validation
   - Type definitions and enums
   - Schema definitions for skate spots, users, and tokens

4. **Repository Layer** (`app/repositories/`)
   - Data access abstraction
   - CRUD operations on database
   - Repository pattern implementation for skate spots and users

5. **Services Layer** (`app/services/`)
   - Business logic and rules
   - Coordinates between repositories and routers
   - Service classes for operations

6. **API Layer** (`app/routers/`)
   - **Authentication** (`auth.py`): Registration, login, logout, and user info
   - **REST API** (`skate_spots.py`): JSON endpoints with form data support
   - **Frontend** (`frontend.py`): HTML pages with Jinja2 templates
   - HTTP request/response handling

7. **Presentation Layer** (`templates/` & `static/`)
   - Jinja2 templates for server-side rendering of skate spot and auth flows
   - HTMX for dynamic interactions
   - CSS styling

### Key Design Decisions

- **Repository Pattern**: Abstracts data storage with SQLAlchemy ORM
- **SQLite Database**: Persistent storage with SQLAlchemy
- **HTMX Frontend**: Progressive enhancement for dynamic UI without heavy JavaScript
- **Hybrid API**: Endpoints accept both JSON and form data for flexibility
- **Dependency Injection**: Services and repositories use FastAPI dependency injection
- **Pydantic Models**: Strong typing and automatic validation
- **Single Responsibility**: Each class has a focused purpose
- **Component-Based Templates**: Reusable Jinja2 template components
- **Cookie-Based Auth**: JWT access tokens issued via HTTP-only cookies for secure browser sessions

## 🧪 Testing Strategy

Following **focused, single-responsibility testing** principles:

### Test Organization
Tests are organized into packages that mirror the app structure:
- **`tests/test_models/`**: Model validation and business rules
- **`tests/test_services/`**: Repository and service layer logic
- **`tests/test_api/`**: HTTP endpoints and integration workflows
  - REST API tests (JSON and form data)
  - Frontend route tests (HTML rendering)
  - Authentication flows (registration, login, logout)

### Test Philosophy
- **Small & Focused**: Each test validates a single piece of functionality
- **No CRUD Workflows**: Create, read, update, delete tested separately
- **Clear Separation**: View operations separated from update operations
- **Pytest Functions**: Simple function-based tests, no test classes
- **Package-Level Testing**: Run tests by architectural layer

### Test Categories

**Model Tests (`tests/test_models/`)**
- Skate spot validation rules (`test_skate_spot.py`)
- User schema constraints (`test_user.py`)
- Geographic helpers (`test_geojson.py`)
- Enum validation and default generation

**Service Tests (`tests/test_services/test_skate_spot_service.py`)**
- Repository CRUD operations
- Business logic validation
- Error handling and edge cases
- Service layer isolation

**API Tests (`tests/test_api/`)**
- REST API: HTTP request/response cycles with JSON
- REST API: Form data submission handling
- Authentication: Cookie-based login, logout, and access control
- Frontend: HTML page rendering
- Frontend: Template integration
- Error responses (404, 422)
- OpenAPI documentation generation

### Test Configuration

Tests are configured in `pyproject.toml` with:
- Automatic test discovery
- Verbose output
- Short traceback format
- Test isolation fixtures

## 🔧 Development Practices

### Code Quality

- **Ruff**: Lightning-fast Python linter and formatter
- **Type Hints**: Full type annotations throughout
- **Docstrings**: Comprehensive documentation for all functions
- **Single Responsibility Principle**: Each function/class has one clear purpose

### Code Style

- **Line Length**: 100 characters
- **Quote Style**: Double quotes
- **Import Sorting**: Automatic with ruff
- **Format on Save**: Recommended IDE setup

### Validation Rules

- **Geographic Coordinates**: Latitude (-90 to 90), Longitude (-180 to 180)
- **String Lengths**: Name (1-100 chars), Description (1-1000 chars)
- **Required Fields**: All core fields must be provided
- **Enum Validation**: Spot types and difficulty levels

## 📊 Data Models

### Skate Spot Types
- `street` - Street skating spots
- `park` - Skate parks
- `bowl` - Bowl/pool spots
- `vert` - Vert ramps
- `mini_ramp` - Mini ramps
- `stairs` - Stair sets
- `rail` - Rails for grinding
- `ledge` - Ledges and curbs
- `gap` - Gaps to jump
- `other` - Other spot types

### Difficulty Levels
- `beginner` - Easy for newcomers
- `intermediate` - Moderate skill required
- `advanced` - High skill level needed
- `expert` - Professional level

### Location Model
```python
{
  "latitude": float,      # Required: -90 to 90
  "longitude": float,     # Required: -180 to 180
  "address": str | None,  # Optional: Human-readable address
  "city": str,           # Required: City name
  "country": str         # Required: Country name
}
```

## 🚀 Deployment

### Production Considerations

Currently uses SQLite database. For production:

1. **Database Migration**: Upgrade from SQLite to PostgreSQL for better concurrency
2. **Secret Management**: Store JWT secret keys and credentials securely
3. **Rate Limiting**: Implement API rate limiting
4. **Caching**: Add Redis for improved performance
5. **Monitoring**: Health checks and metrics
6. **Docker**: Containerization for deployment
7. **CDN**: Serve static assets from CDN

### Environment Variables

```bash
# Example production environment
DATABASE_URL=postgresql://user:pass@localhost/skate_spots
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
SKATE_SPOTS_LOG_LEVEL=INFO
SKATE_SPOTS_LOG_JSON=false
```

## 🪵 Logging

The API uses [structlog](https://www.structlog.org/) for structured logs and request context enrichment.

- Per-request correlation identifiers are returned via the `X-Request-ID` response header and included in log events.
- Configure verbosity with `SKATE_SPOTS_LOG_LEVEL` (for example: `DEBUG`, `INFO`, `WARNING`).
- Emit JSON logs for log aggregation platforms by setting `SKATE_SPOTS_LOG_JSON=true`.

Logs from FastAPI and Uvicorn are routed through the same configuration so they share formatting and context fields.

## 🔄 CI Workflow

This project uses GitHub Actions for continuous integration:

### 🧪 CI Workflow (`.github/workflows/ci.yml`)
Runs on every push and pull request to `main` and `develop` branches:

- ✅ **Code Linting** - Ruff code quality checks
- ✅ **Code Formatting** - Ruff formatting validation
- ✅ **Test Suite** - Complete test suite execution

The workflow uses:
- **Python 3.12** - Single Python version for simplicity
- **uv package manager** - Fast dependency management
- **Ubuntu Latest** - Reliable CI environment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the code style
4. Add tests for new functionality  
5. Run the development workflow (`make check`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

All pull requests trigger the CI workflow which must pass before merging.

### Development Setup

```bash
# Install all dependencies (including dev group)
uv sync

# Run development server
make serve

# Run the full development workflow
make check     # Runs linting and all tests
```

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install dependencies |
| `make dev` | Install with dev dependencies |
| `make serve` | Start development server with hot reload |
| `make test` | Run all tests |
| `make lint` | Check code with ruff |
| `make format` | Format code with ruff |
| `make check` | Run lint + tests |
| `make clean` | Clean cache files |

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Pydantic](https://pydantic.dev/)
- Database with [SQLAlchemy](https://www.sqlalchemy.org/)
- Dynamic UI with [HTMX](https://htmx.org/)
- Templates with [Jinja2](https://jinja.palletsprojects.com/)
- Code quality by [Ruff](https://github.com/astral-sh/ruff)
- Package management by [uv](https://github.com/astral-sh/uv)

## 📞 Support

For support, please open an issue in the GitHub repository or contact the development team.

---

**Happy skating!** 🛹
