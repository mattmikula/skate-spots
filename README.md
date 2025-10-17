# Skate Spots API - Django Version

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.0-green)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.16-orange)](https://www.django-rest-framework.org/)

A Django REST Framework implementation of the Skate Spots API for sharing and discovering skateboarding spots around the world.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- pip or uv package manager

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
make -f Makefile.django migrate

# Create superuser
make -f Makefile.django createsuperuser

# Start server
make -f Makefile.django serve
```

The API will be available at:
- **API**: http://localhost:8000/api/v1/
- **Admin**: http://localhost:8000/admin/
- **Docs**: http://localhost:8000/api/docs/

## 🛹 Features

- **REST API** with full CRUD operations for skate spots
- **JWT Authentication** with httponly cookies
- **Advanced Filtering** by location, difficulty, type, and more
- **GeoJSON Support** for mapping applications
- **Admin Interface** for easy data management
- **API Documentation** with interactive Swagger UI
- **Ownership & Permissions** - Users own their spots
- **Clean Architecture** with Django best practices

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

## 📊 Data Models

### Spot Types
`street`, `park`, `skatepark`, `bowl`, `vert`, `mini_ramp`, `stairs`, `rail`, `ledge`, `gap`, `other`

### Difficulty Levels
`beginner`, `intermediate`, `advanced`, `expert`

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
```

## 🛠️ Development

### Available Commands

```bash
make -f Makefile.django serve           # Start dev server
make -f Makefile.django makemigrations  # Create migrations
make -f Makefile.django migrate         # Apply migrations
make -f Makefile.django shell           # Django shell
make -f Makefile.django createsuperuser # Create admin user
make -f Makefile.django lint            # Check code
make -f Makefile.django format          # Format code
make -f Makefile.django test            # Run tests
make -f Makefile.django clean           # Clean cache
```

### Project Structure

```
skate-spots/
├── accounts/              # User authentication
│   ├── models.py         # User model
│   ├── serializers.py    # API serializers
│   ├── views.py          # Auth endpoints
│   └── authentication.py # JWT cookie auth
├── spots/                # Skate spots
│   ├── models.py         # SkateSpot model
│   ├── serializers.py    # Spot serializers
│   ├── views.py          # CRUD endpoints
│   ├── filters.py        # Filtering logic
│   └── permissions.py    # Access control
└── skate_spots_project/  # Django config
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

Core API tested and verified:
- ✅ User registration & login
- ✅ JWT cookie authentication
- ✅ CRUD operations on spots
- ✅ Filtering & search
- ✅ GeoJSON endpoint
- ✅ Permission controls

## 📚 Documentation

- **API Docs**: http://localhost:8000/api/docs/ (Swagger UI)
- **Migration Guide**: [DJANGO_MIGRATION.md](DJANGO_MIGRATION.md)
- **Admin Interface**: http://localhost:8000/admin/

## 🔄 Migration from FastAPI

This is a Django implementation of the original FastAPI application. See [DJANGO_MIGRATION.md](DJANGO_MIGRATION.md) for details on the migration.

**Key differences:**
- Django REST Framework instead of FastAPI
- Django ORM instead of SQLAlchemy
- Built-in admin interface
- Django migrations instead of Alembic

**Preserved functionality:**
- All API endpoints
- Authentication & permissions
- Data validation
- Filtering capabilities
- GeoJSON support

## 📦 Dependencies

- Django 5.0
- Django REST Framework 3.16
- djangorestframework-simplejwt (JWT auth)
- django-filter (filtering)
- django-environ (settings)
- drf-spectacular (API docs)

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
