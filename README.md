# Skate Spots 🛹

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.0-green)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.16-orange)](https://www.django-rest-framework.org/)
[![HTMX](https://img.shields.io/badge/HTMX-2.0-blueviolet)](https://htmx.org/)

A full-stack Django application for sharing and discovering skateboarding spots around the world. Features a REST API with Django REST Framework and an interactive HTMX-powered frontend.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Installation

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
make install

# Run migrations
make migrate

# Create superuser (optional, for admin access)
make createsuperuser

# Start server
make serve
```

The application will be available at:
- **Website**: http://localhost:8000/
- **API**: http://localhost:8000/api/v1/
- **Admin**: http://localhost:8000/admin/
- **Docs**: http://localhost:8000/api/docs/

## 🛹 Features

### Frontend
- **Interactive Web UI** with HTMX for smooth interactions
- **Spot Management** - Create, edit, delete spots with forms
- **Spot Details Page** - Full spot information with all ratings and reviews
- **Ratings & Reviews** - Create, edit, delete ratings directly on spot detail page
- **Rating Display** - Average star rating shown on spot cards with full reviews visible
- **Real-time Updates** - HTMX-powered delete and rating operations without page reload
- **Map View** with Leaflet.js for visualizing spots
- **Responsive Design** with modern CSS

### Backend
- **REST API** with full CRUD operations for skate spots and ratings
- **JWT Authentication** with httponly cookies
- **Ratings System** - Users can rate spots 1-5 stars with optional comments
- **Advanced Filtering** by location, difficulty, type, and more
- **GeoJSON Support** for mapping applications
- **Admin Interface** for easy data management
- **API Documentation** with interactive Swagger UI
- **Ownership & Permissions** - Users own their spots and ratings
- **Rate Limiting** - 5 requests/min for auth, 50/min for writes
- **Clean Architecture** with Django best practices
- **Comprehensive Test Suite** - 102 tests covering all functionality

## 📋 API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - Create account
- `POST /api/v1/auth/login/` - Login (returns JWT in cookie)
- `POST /api/v1/auth/logout/` - Logout
- `GET /api/v1/auth/me/` - Get current user

### Skate Spots
- `GET /api/v1/skate-spots/` - List spots (supports filtering)
- `POST /api/v1/skate-spots/` - Create spot (auth required)
- `GET /api/v1/skate-spots/{id}/` - Get specific spot
- `PUT /api/v1/skate-spots/{id}/` - Update spot (owner/admin)
- `DELETE /api/v1/skate-spots/{id}/` - Delete spot (owner/admin)
- `GET /api/v1/skate-spots/geojson/` - GeoJSON format

### Ratings
- `GET /api/v1/ratings/` - List all ratings (supports filtering by spot)
- `POST /api/v1/ratings/` - Create rating (auth required)
- `GET /api/v1/ratings/{id}/` - Get specific rating
- `PATCH /api/v1/ratings/{id}/` - Update rating (owner/admin)
- `DELETE /api/v1/ratings/{id}/` - Delete rating (owner/admin)

## 🔍 Filtering

Filter spots with query parameters:

```bash
# Search by keyword
curl "http://localhost:8000/api/v1/skate-spots/?search=rails"

# Filter by city and difficulty
curl "http://localhost:8000/api/v1/skate-spots/?city=Barcelona&difficulty=intermediate"

# Multiple spot types
curl "http://localhost:8000/api/v1/skate-spots/?spot_type=rail&spot_type=ledge"

# Public spots only
curl "http://localhost:8000/api/v1/skate-spots/?is_public=true"
```

Available filters:
- `search` - Search name, description, city, country
- `spot_type` - Filter by type (rail, park, street, etc.)
- `difficulty` - Filter by difficulty (beginner, intermediate, advanced, expert)
- `city` - Exact city match
- `country` - Exact country match
- `is_public` - Public access only
- `requires_permission` - Permission required

For ratings:
```bash
# Get all ratings for a specific spot
curl "http://localhost:8000/api/v1/ratings/?spot=<spot-id>"
```

## 📊 Data Models

### Spot Types
`street`, `park`, `skatepark`, `bowl`, `vert`, `mini_ramp`, `stairs`, `rail`, `ledge`, `gap`, `other`

### Difficulty Levels
`beginner`, `intermediate`, `advanced`, `expert`

### Rating Scores
1-5 stars (integer), with optional text comment

### Example Spot

```json
{
  "id": "uuid",
  "name": "Downtown Rails",
  "description": "Great set of rails for grinding",
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
  "requires_permission": false,
  "owner_id": "uuid",
  "created_at": "2025-10-17T00:00:00Z",
  "updated_at": "2025-10-17T00:00:00Z"
}
```

### Example Rating

```json
{
  "id": "uuid",
  "spot": "uuid",
  "spot_name": "Downtown Rails",
  "user": "uuid",
  "user_username": "skater123",
  "score": 5,
  "comment": "Amazing spot! Perfect for practicing grinds.",
  "created_at": "2025-10-17T00:00:00Z",
  "updated_at": "2025-10-17T00:00:00Z"
}
```

## 🔐 Authentication

The API uses JWT tokens stored in httponly cookies for security.

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user", "password": "pass123"}'

# Login (cookie stored automatically)
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username": "user", "password": "pass123"}'

# Make authenticated requests
curl http://localhost:8000/api/v1/auth/me/ -b cookies.txt

# Create a rating
curl -X POST http://localhost:8000/api/v1/ratings/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"spot": "<spot-id>", "score": 5, "comment": "Great spot!"}'
```

## 🛠️ Development

### Available Commands

```bash
make install            # Install dependencies with uv
make serve              # Start development server
make migrate            # Run database migrations
make makemigrations     # Create new migrations
make shell              # Open Django shell
make createsuperuser    # Create admin user
make test               # Run test suite (102 tests)
make check              # Run linting and tests
make lint               # Check code with ruff
make format             # Format code with ruff
make clean              # Remove cache files
```

### Project Structure

```
skate-spots/
├── accounts/              # User authentication
│   ├── models.py         # Custom User model with UUID
│   ├── serializers.py    # API serializers
│   ├── views.py          # API auth endpoints
│   ├── frontend_views.py # HTML login/register views
│   ├── forms.py          # Django forms
│   └── authentication.py # JWT cookie auth
├── spots/                # Skate spots app
│   ├── models.py         # SkateSpot model
│   ├── serializers.py    # API serializers (nested & flat)
│   ├── views.py          # API CRUD endpoints
│   ├── frontend_views.py # HTML views
│   ├── filters.py        # Advanced filtering
│   ├── permissions.py    # Owner/admin permissions
│   └── forms.py          # Spot creation forms
├── ratings/              # Ratings app
│   ├── models.py         # Rating model (1-5 stars)
│   ├── serializers.py    # Rating serializers
│   ├── views.py          # Rating CRUD endpoints
│   ├── permissions.py    # Rating ownership permissions
│   └── admin.py          # Admin interface
├── templates/            # Django templates
│   ├── spots/           # Spot templates with HTMX
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── spot_card.html
│   │   ├── spot_detail.html       # Spot detail page with ratings
│   │   ├── spot_form.html
│   │   ├── rating_edit.html       # Rating form/editor
│   │   └── map.html
│   └── accounts/        # Auth templates
├── static/              # CSS, JS, images
├── tests/               # Comprehensive test suite
│   ├── conftest.py      # pytest fixtures
│   ├── test_models.py
│   ├── test_api_endpoints.py
│   ├── test_frontend_pages.py
│   ├── test_ratings.py
│   └── test_rate_limiting.py
└── skate_spots_project/ # Django config
    ├── settings.py
    └── urls.py
```

## ⚙️ Configuration

Create a `.env` file:

```env
SKATE_SPOTS_SECRET_KEY=your-secret-key
SKATE_SPOTS_DATABASE_URL=sqlite:///skate_spots.db
SKATE_SPOTS_ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
```

## 🧪 Testing

Comprehensive test suite with **102 tests** covering:
- ✅ **Model tests** - User, SkateSpot, and Rating validation, constraints, cascade delete
- ✅ **API endpoint tests** - Auth flow, CRUD operations, filtering, GeoJSON
- ✅ **Ratings tests** - Create, update, delete, duplicate prevention, permissions
- ✅ **Frontend tests** - Page rendering, form submissions, authentication flow
- ✅ **Ratings UI tests** - Spot detail pages, rating display, form interactions
- ✅ **Permission tests** - Owner/admin access, update/delete authorization
- ✅ **Rate limiting** - Decorator configuration and enforcement

Run tests with:
```bash
make test        # Run all tests
make check       # Run linting + tests
```

## 📚 Documentation

- **Website**: http://localhost:8000/ - Interactive frontend
- **API Docs**: http://localhost:8000/api/docs/ - Swagger UI
- **Admin Interface**: http://localhost:8000/admin/ - Django admin

## 🔄 Migration History

This project was migrated from FastAPI to Django with full feature parity.

**Technology Stack Changes:**
- ~~FastAPI~~ → **Django REST Framework**
- ~~SQLAlchemy~~ → **Django ORM**
- ~~Alembic~~ → **Django Migrations**
- ~~Jinja2~~ → **Django Templates**
- Added: **HTMX** for interactive frontend
- Added: **Django Admin** interface

**All functionality preserved:**
- ✅ REST API endpoints
- ✅ JWT authentication
- ✅ Permission system
- ✅ Data validation
- ✅ Advanced filtering
- ✅ GeoJSON support
- ✅ Rate limiting
- **+** Interactive web UI
- **+** Ratings system
- **+** 95-test comprehensive suite

## 📦 Dependencies

### Backend
- **Django 5.0** - Web framework
- **Django REST Framework 3.16** - API toolkit
- **djangorestframework-simplejwt** - JWT authentication
- **django-filter** - Advanced filtering
- **django-ratelimit** - Rate limiting
- **django-environ** - Environment configuration
- **drf-spectacular** - OpenAPI documentation

### Frontend
- **HTMX 2.0** - Dynamic interactions
- **Leaflet.js** - Interactive maps
- **Modern CSS** - Responsive design

### Development
- **pytest-django** - Testing framework
- **ruff** - Fast Python linter & formatter
- **uv** - Fast Python package installer

## 🚀 Production

For production deployment:

1. Use PostgreSQL instead of SQLite
2. Set `DEBUG=False`
3. Configure proper `SECRET_KEY`
4. Set up static file serving
5. Use gunicorn or uwsgi
6. Add Redis for caching
7. Implement rate limiting

## 📝 License

MIT License

## 🙏 Acknowledgments

- Built with [Django](https://www.djangoproject.com/)
- API powered by [Django REST Framework](https://www.django-rest-framework.org/)
- Documentation by [drf-spectacular](https://drf-spectacular.readthedocs.io/)

---

**Happy skating!** 🛹
