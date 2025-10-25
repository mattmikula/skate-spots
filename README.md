# Skate Spots API

[![CI](https://github.com/yourusername/skate-spots/workflows/CI/badge.svg)](https://github.com/yourusername/skate-spots/actions)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/downloads/)

A modern FastAPI application for sharing and discovering skateboarding spots around the world. Built with clean architecture principles, comprehensive testing, and professional development practices.

## 🛹 Features

- **Interactive Web Frontend** built with HTMX for dynamic user interactions
- **REST API** for managing skate spots with full CRUD operations and rich filtering
- **Interactive Map Location Picker** with click-to-place markers, address search, and automatic geocoding for intuitive spot creation
- **Geocoding API** for converting between addresses and coordinates using OpenStreetMap Nominatim
- **User Profiles** with customizable bio, avatar, and location, plus activity statistics dashboard
- **Tabbed Spot Detail Pages** with clean interface for Comments, Ratings, and Sessions, featuring badge indicators, deep linking, and smart tab memory
- **User Ratings** so skaters can rate spots with 1-5 scores, manage their own feedback, and see community sentiment
- **Community Comments** that let skaters share detailed feedback and discuss spots in real time via HTMX snippets and JSON APIs
- **Inline Ratings UI** with HTMX-driven snippets that let logged-in users rate spots directly from the listings with instant feedback
- **Dynamic Spot Filters** with HTMX-powered search and dropdowns so the catalogue updates instantly without full page reloads
- **Spot Photo Uploads** with local media storage, editing, and responsive galleries on each spot card
- **Personal Collections** so logged-in skaters can favorite spots and revisit them from their profile
- **Social Feed** with activity tracking, user follows/followers, and personalized activity feeds from users you follow
- **Public User Profiles** with contribution statistics, activity feeds, and lists of each skater's spots, comments, and ratings
- **Customizable Profiles** so skaters can edit their bio, links, and avatar directly from the dashboard
- **Secure Authentication** with registration, login, and cookie-based JWT tokens
- **Session Scheduling** that lets crews organise meetups, manage RSVPs, and automatically promote waitlisted skaters when spots open up
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
- **User Profiles**: http://localhost:8000/profile (own profile) or http://localhost:8000/users/{username} (public profiles)
- **Authentication Pages**: http://localhost:8000/login and http://localhost:8000/register
- **API Base**: http://localhost:8000/api/v1
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Uploaded Media**: http://localhost:8000/media/

Uploaded skate spot photos are stored under the `media/` directory in the project root. The FastAPI app automatically creates the folder on startup and serves its contents at `/media`. Add or remove photos using the HTMX forms on the spot create/edit pages – each submission supports multiple image uploads and lets you mark existing photos for deletion. The repository includes a `.gitignore` entry so that media files stay out of version control.

### Filtering Skate Spots via the API

Both the REST and GeoJSON skate spot endpoints accept optional query parameters so you can narrow down results without fetching
the full catalogue. Combine any of the following parameters on `GET /api/v1/skate-spots/` or `GET /api/v1/skate-spots/geojson`:

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | `str` | Case-insensitive substring match applied to name, description, city, and country. |
| `spot_type` | `SpotType` or repeated | Filter by one or more spot types (e.g. `spot_type=park&spot_type=street`). |
| `difficulty` | `Difficulty` or repeated | Filter by one or more difficulty levels. |
| `city` | `str` | Exact match (case-insensitive) on the city name. |
| `country` | `str` | Exact match (case-insensitive) on the country. |
| `is_public` | `bool` | Restrict to publicly accessible spots. |
| `requires_permission` | `bool` | Restrict to spots that require special permission. |

The `/skate-spots` HTMX front end uses the same parameters under the hood, so the filter form in the UI stays in sync with the API surface. When you favorite a spot from the listings, the UI issues the same requests you can script against `/api/v1/users/me/favorites/`.

Example: fetch all intermediate or advanced street spots in Barcelona that are publicly accessible:

```bash
curl \
  --get "http://localhost:8000/api/v1/skate-spots" \
  --data-urlencode "city=Barcelona" \
  --data-urlencode "is_public=true" \
  --data-urlencode "spot_type=street" \
  --data-urlencode "difficulty=intermediate" \
  --data-urlencode "difficulty=advanced"
```

The same parameters can be used with the GeoJSON endpoint to power filtered map views without downloading unnecessary data.

### Authentication Workflow

1. **Register** using the HTML form at `/register` or the API endpoint `POST /api/v1/auth/register`.
2. **Login** via `/login` or `POST /api/v1/auth/login` to receive an access token stored in an HTTP-only cookie.
3. Authenticated requests automatically include the cookie; access the current user with `GET /api/v1/auth/me`.
4. **Logout** using the button in the UI or `POST /api/v1/auth/logout` to clear the cookie.

The JSON API endpoints also accept traditional form submissions for HTMX-driven pages.

### User Profiles

Every user has a customizable profile showcasing their skateboarding activity:

**Profile Features:**
- **Bio** - Personal description (up to 500 characters)
- **Avatar** - Profile picture via URL
- **Location** - City, state, or country
- **Activity Statistics** - Automatic tracking of:
  - Spots added
  - Photos uploaded
  - Comments posted
  - Ratings given
  - Favorites count

**Accessing Profiles:**
- **Your Profile**: Visit `/profile` while logged in to view your statistics, edit your profile, and see your favorite spots
- **Public Profiles**: Anyone can view `/users/{username}` to see a user's public information, stats, and contributed spots
- **API Access**: Use `GET /api/v1/auth/users/{username}` to retrieve profile data programmatically

**Example: Update Your Profile**
```bash
curl -X PUT "http://localhost:8000/api/v1/auth/me/profile" \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=YOUR_TOKEN" \
  -d '{
    "bio": "Skateboarding enthusiast from LA. Love street spots!",
    "location": "Los Angeles, CA",
    "avatar_url": "https://example.com/my-avatar.jpg"
  }'
```

**Example: Get a User's Profile**
```bash
curl "http://localhost:8000/api/v1/auth/users/kickflip_master"
```

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
- `SKATE_SPOTS_GEOCODING_USER_AGENT` – User agent string for Nominatim geocoding requests (default: "skate-spots-app").

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
| `GET` | `/profile` | Current user's profile with stats and favorites (requires auth) |
| `POST` | `/profile` | Update profile bio, avatar, and location (requires auth) |
| `GET` | `/users/{username}` | Public profile page for any user |
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
| `GET` | `/api/v1/skate-spots/{id}/comments/` | List comments for a skate spot |
| `POST` | `/api/v1/skate-spots/{id}/comments/` | Create a comment on a skate spot |
| `DELETE` | `/api/v1/skate-spots/{id}/comments/{comment_id}` | Delete a comment (owner or admin only) |

### Social Feed Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/users/{username}/follow` | Follow a user by username |
| `DELETE` | `/api/v1/users/{username}/follow` | Unfollow a user |
| `GET` | `/api/v1/users/me/following/{username}` | Check if currently following a user |
| `GET` | `/api/v1/users/{username}/followers` | List users following a specific user (with pagination) |
| `GET` | `/api/v1/users/{username}/following` | List users that a specific user is following (with pagination) |
| `GET` | `/api/v1/users/{username}/follow-stats` | Get follower and following counts for a user |
| `GET` | `/api/v1/feed` | Get personalized activity feed from followed users (authenticated) |
| `GET` | `/api/v1/feed/public` | Get public activity feed (all recent user activities) |
| `GET` | `/api/v1/feed/users/{username}` | Get activity history for a specific user |

### Geocoding Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/geocoding/reverse` | Convert coordinates to address information (reverse geocoding) |
| `GET` | `/api/v1/geocoding/search` | Search for locations by address or place name (forward geocoding) |

**Reverse Geocoding Parameters:**
- `latitude` (required): Latitude coordinate (-90 to 90)
- `longitude` (required): Longitude coordinate (-180 to 180)

**Search Parameters:**
- `q` (required): Search query (minimum 1 character)
- `limit` (optional): Maximum results to return (1-10, default: 5)

**Note**: The API endpoints accept both JSON payloads and HTML form data, making them compatible with both traditional API clients and HTMX-powered forms.

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Create a new user account (JSON or form data) |
| `POST` | `/api/v1/auth/login` | Authenticate and receive a JWT access token cookie |
| `POST` | `/api/v1/auth/logout` | Clear the authentication cookie |
| `GET` | `/api/v1/auth/me` | Retrieve the currently authenticated user |
| `GET` | `/api/v1/auth/users/{username}` | Get a user's public profile with activity statistics |
| `PUT` | `/api/v1/auth/me/profile` | Update the authenticated user's profile (bio, avatar, location) |

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

**Rate a Spot (API):**
```bash
curl -X PUT "http://localhost:8000/api/v1/skate-spots/<spot-id>/ratings/me" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "score": 4,
    "comment": "Smooth transitions and clean coping."
  }'
```

**Check Rating Summary (API):**
```bash
curl "http://localhost:8000/api/v1/skate-spots/<spot-id>/ratings/summary" -b cookies.txt
```

**Reverse Geocode Coordinates:**
```bash
curl "http://localhost:8000/api/v1/geocoding/reverse?latitude=40.7128&longitude=-74.0060"
```

**Search for a Location:**
```bash
curl "http://localhost:8000/api/v1/geocoding/search?q=Brooklyn%20Skatepark&limit=3"
```

### Interactive Location Picker

Creating and editing skate spots features an intuitive map-based location picker instead of manual coordinate entry:

**Features:**
- **Interactive Map**: Click anywhere on the map to place a marker at the exact spot location
- **Draggable Marker**: Fine-tune the position by dragging the marker to the precise location
- **Address Search**: Type an address or place name to search and automatically jump to that location
- **Automatic Geocoding**: City, country, and address fields are automatically populated based on the selected coordinates
- **Manual Override**: All auto-filled fields can be manually edited if needed
- **Visual Feedback**: Read-only coordinate displays show the exact latitude/longitude selected

**How it Works:**
1. Open the spot creation/edit form at `/skate-spots/new` or `/skate-spots/{id}/edit`
2. Use the search box to find a general area, or click directly on the map
3. Drag the marker to fine-tune the exact location
4. City, country, and address are automatically filled via reverse geocoding
5. Adjust any fields manually if needed
6. Submit the form with precise coordinates

The location picker uses the Leaflet.js library for maps and the OpenStreetMap Nominatim service for geocoding (free, no API key required).

## 🏗️ Architecture

This project follows **Clean Architecture** principles with clear separation of concerns:

```
skate-spots/
├── alembic/              # Database migrations
│   ├── env.py            # Alembic environment configuration
│   ├── script.py.mako    # Migration file template
│   └── versions/         # Individual migration revisions
│       ├── 0001_create_skate_spots_table.py
│       ├── 0002_add_user_authentication.py
│       ├── 0003_add_spot_ratings.py
│       ├── 0009_add_user_follows.py
│       └── 0010_add_activity_feed.py
├── app/
│   ├── core/             # Shared configuration & security helpers
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── security.py
│   ├── db/               # Database layer
│   │   ├── database.py          # Database configuration
│   │   └── models.py            # SQLAlchemy models
│   ├── models/           # Pydantic data models
│   │   ├── activity.py
│   │   ├── follow.py
│   │   ├── rating.py
│   │   ├── skate_spot.py
│   │   └── user.py
│   ├── repositories/     # Data access layer
│   │   ├── activity_repository.py
│   │   ├── follow_repository.py
│   │   ├── rating_repository.py
│   │   ├── skate_spot_repository.py
│   │   └── user_repository.py
│   ├── routers/          # FastAPI route handlers
│   │   ├── activity.py          # Activity feed API routes
│   │   ├── auth.py              # Authentication API
│   │   ├── follows.py           # User follow/follower API routes
│   │   ├── frontend.py          # HTML/HTMX routes
│   │   ├── geocoding.py         # Geocoding API routes
│   │   ├── ratings.py           # Rating API routes
│   │   └── skate_spots.py       # REST API routes
│   └── services/         # Business logic layer
│       ├── activity_service.py
│       ├── follow_service.py
│       ├── geocoding_service.py
│       ├── rating_service.py
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
│   └── partials/
│       └── rating_section.html  # HTMX snippet for rating summary & form
│   └── spot_form.html    # Create/edit form
├── tests/                # Test suite (organized by app structure)
│   ├── test_api/         # API integration tests
│   │   ├── test_auth.py         # Authentication endpoint tests
│   │   ├── test_frontend.py     # Frontend route tests
│   │   ├── test_ratings.py      # Rating endpoint tests
│   │   ├── test_root.py         # Root & docs endpoints
│   │   └── test_skate_spots.py  # CRUD endpoint tests
│   ├── test_models/      # Model validation tests
│   │   ├── test_rating.py       # Rating model tests
│   │   ├── test_skate_spot.py   # Skate spot model tests
│   │   └── test_user.py         # User model tests
│   ├── test_repositories/ # Repository layer tests
│   │   ├── test_activity_repository.py
│   │   ├── test_follow_repository.py
│   │   ├── test_rating_repository.py
│   │   └── test_user_repository.py
│   ├── test_services/    # Service layer tests
│   │   ├── test_activity_service.py
│   │   ├── test_follow_service.py
│   │   ├── test_rating_service.py
│   │   └── test_skate_spot_service.py
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
   - **Geocoding API** (`geocoding.py`): Address search and coordinate conversion
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
- **User Ratings**: Simple 1-5 score system with dedicated repository/service pairing for live spot summaries
- **Ratings & Comments Separation**: Ratings are quantitative scores while comments are the qualitative feedback mechanism, keeping concerns separate and UX clear
- **Social Feed**: Activity tracking with event sourcing pattern; flexible JSON metadata for activity-specific data
- **Follow Relationships**: Graph-like user connections with CASCADE deletion for data integrity
- **Dependency Injection**: Services and repositories use FastAPI dependency injection
- **Pydantic Models**: Strong typing and automatic validation
- **Single Responsibility**: Each class has a focused purpose
- **Component-Based Templates**: Reusable Jinja2 template components
- **Cookie-Based Auth**: JWT access tokens issued via HTTP-only cookies for secure browser sessions

### Social Feed Feature

The social feed enables users to follow other skaters and receive personalized activity updates:

**Follow System**
- Users can follow/unfollow other users by username
- Prevents self-following and duplicate follows
- Tracks follower/following counts and relationships
- Uses graph-like database structure with CASCADE deletes

**Activity Tracking**
- Records all user activities: spot creation, ratings, comments, favorites, session creation, and RSVP
- Flexible JSON metadata for activity-specific information
- Indexed for efficient feed queries (user_id, created_at, activity_type)
- Automatically integrated into existing services (skate_spot, rating, comment, favorite)

**Activity Feeds**
- **Personalized Feed** (`GET /api/v1/feed`): Shows activities from followed users, paginated
- **Public Feed** (`GET /api/v1/feed/public`): Shows all recent activities across the platform
- **User Activity** (`GET /api/v1/feed/users/{username}`): Shows a specific user's activity history
- All feeds include enriched actor information (user profile data) and pagination metadata

**Database Schema**
- `user_follows` table: Tracks follower/following relationships with timestamps
- `activity_feed` table: Stores activities with activity type, target type, target ID, and JSON metadata
- Check constraints enforce valid activity and target types
- Comprehensive indexing for fast queries on user_id, created_at, and activity_type

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
- **Dependency Injection**: External services mocked using FastAPI's dependency override system
- **No External Calls**: Geocoding tests use mocked services - no actual API calls during testing
- **Pytest Functions**: Simple function-based tests, no test classes
- **Package-Level Testing**: Run tests by architectural layer

### Test Categories

**Model Tests (`tests/test_models/`)**
- Skate spot validation rules (`test_skate_spot.py`)
- Rating score boundaries and validation (`test_rating.py`)
- User schema constraints (`test_user.py`)
- Geographic helpers (`test_geojson.py`)
- Enum validation and default generation

**Service Tests (`tests/test_services/`)**
- Skate spot repository and service flows (`test_skate_spot_service.py`)
- Rating lifecycle, summaries, and error handling (`test_rating_service.py`)
- Geocoding service with mocked geopy library (`test_geocoding_service.py`)
- Follow user validation, error handling, and pagination (`test_follow_service.py`)
- Activity recording helpers and feed enrichment (`test_activity_service.py`)

**Repository Tests (`tests/test_repositories/`)**
- User persistence helpers (`test_user_repository.py`)
- Rating persistence, upsert logic, and aggregation (`test_rating_repository.py`)
- Follow relationships, follower/following queries, and pagination (`test_follow_repository.py`)
- Activity recording, feed queries, and pagination (`test_activity_repository.py`)

**API Tests (`tests/test_api/`)**
- REST API: HTTP request/response cycles with JSON
- REST API: Form data submission handling
- Rating endpoints: create/update/delete and summary queries (`test_ratings.py`)
- Geocoding endpoints: reverse geocoding and address search with mocked service (`test_geocoding.py`)
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
3. **Rate Limiting**: Replace the built-in in-memory limiter with a distributed solution (e.g. Redis) for multi-instance deployments
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
- Maps with [Leaflet](https://leafletjs.com/)
- Geocoding with [GeoPy](https://geopy.readthedocs.io/) and [OpenStreetMap Nominatim](https://nominatim.org/)
- Templates with [Jinja2](https://jinja.palletsprojects.com/)
- Code quality by [Ruff](https://github.com/astral-sh/ruff)
- Package management by [uv](https://github.com/astral-sh/uv)

## 📞 Support

For support, please open an issue in the GitHub repository or contact the development team.

---

**Happy skating!** 🛹
### 🎨 Frontend Ratings & Comments

- Every spot card now lazy-loads a rating widget (`templates/partials/rating_section.html`) via HTMX. When the snippet loads it shows the aggregate score and rating count pulled from the new summary endpoint.
- Authenticated users can select a score (1-5 stars) and submit directly from the list view. The form posts to `/skate-spots/{spot_id}/ratings` (frontend route) and swaps the snippet with the latest summary without a full page refresh.
- For detailed feedback, users can post comments in the dedicated comment section below the rating widget. Comments support full CRUD operations, author attribution, timestamps, and moderation by owners and admins.
- Removing a rating is equally quick: the "Remove rating" action issues an HTMX `DELETE` that clears the user's feedback and re-renders the summary.
- Anonymous visitors still see the community average and existing comments along with a prompt to log in, so the UI stays informative even when users can't rate.
