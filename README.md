# Skate Spots API

[![CI](https://github.com/yourusername/skate-spots/workflows/CI/badge.svg)](https://github.com/yourusername/skate-spots/actions)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/downloads/)

A modern FastAPI application for sharing and discovering skateboarding spots around the world. Built with clean architecture principles, comprehensive testing, and professional development practices.

## 🛹 Features

- **REST API** for managing skate spots with full CRUD operations
- **Rich Data Model** with locations, difficulty levels, and spot types
- **Comprehensive Validation** using Pydantic models
- **Clean Architecture** with separation of concerns
- **Extensive Testing** with focused, single-responsibility tests
- **Auto-generated Documentation** with OpenAPI/Swagger
- **Code Quality** tools with ruff linting and formatting
- **Modern Tooling** with uv package manager and Makefile commands

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
# Start the development server with hot reload
make serve
# Or directly: uv run uvicorn main:app --reload
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

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

# Available make commands
make help          # Show all available commands
```

## 📋 API Endpoints

### Skate Spots

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/skate-spots/` | List all skate spots |
| `POST` | `/api/v1/skate-spots/` | Create a new skate spot |
| `GET` | `/api/v1/skate-spots/{id}` | Get a specific skate spot |
| `PUT` | `/api/v1/skate-spots/{id}` | Update a skate spot |
| `DELETE` | `/api/v1/skate-spots/{id}` | Delete a skate spot |

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

## 🏗️ Architecture

This project follows **Clean Architecture** principles with clear separation of concerns:

```
skate-spots/
├── app/
│   ├── models/           # Pydantic data models
│   │   └── skate_spot.py
│   ├── services/         # Business logic layer
│   │   └── skate_spot_service.py
│   └── routers/          # FastAPI route handlers
│       └── skate_spots.py
├── tests/                # Test suite (organized by app structure)
│   ├── test_api/         # API integration tests
│   │   ├── test_root.py         # Root & docs endpoints
│   │   └── test_skate_spots.py  # CRUD endpoint tests
│   ├── test_models/      # Model validation tests
│   │   └── test_skate_spot.py   # All model tests
│   ├── test_services/    # Service layer tests
│   │   └── test_skate_spot_service.py  # Repository & service tests
│   └── conftest.py       # Test configuration
├── main.py               # Application entry point
├── Makefile              # Development commands
└── pyproject.toml        # Project configuration
```

### Architecture Layers

1. **Models Layer** (`app/models/`)
   - Pydantic models for data validation
   - Type definitions and enums
   - Schema definitions for API contracts

2. **Services Layer** (`app/services/`)
   - Business logic and rules
   - Repository pattern for data access
   - Service classes for operations

3. **API Layer** (`app/routers/`)
   - HTTP request/response handling
   - Route definitions
   - API documentation

### Key Design Decisions

- **Repository Pattern**: Abstracts data storage (currently in-memory, easily replaceable)
- **Dependency Injection Ready**: Services can be easily swapped for different implementations
- **Pydantic Models**: Strong typing and automatic validation
- **Single Responsibility**: Each class has a focused purpose
- **Small Functions**: Functions are kept small and focused

## 🧪 Testing Strategy

Following **focused, single-responsibility testing** principles:

### Test Organization
Tests are organized into packages that mirror the app structure:
- **`tests/test_models/`**: Model validation and business rules (17 tests)
- **`tests/test_services/`**: Repository and service layer logic (25 tests)  
- **`tests/test_api/`**: HTTP endpoints and integration workflows (16 tests)
- **Total: 58 tests** with comprehensive coverage

### Test Philosophy
- **Small & Focused**: Each test validates a single piece of functionality
- **No CRUD Workflows**: Create, read, update, delete tested separately
- **Clear Separation**: View operations separated from update operations
- **Pytest Functions**: Simple function-based tests, no test classes
- **Package-Level Testing**: Run tests by architectural layer

### Test Categories

**Model Tests (`tests/test_models/test_skate_spot.py`)**
- Pydantic validation rules
- Field constraints and bounds  
- Enum validation
- Default values and auto-generation

**Service Tests (`tests/test_services/test_skate_spot_service.py`)**
- Repository CRUD operations
- Business logic validation
- Error handling and edge cases
- Service layer isolation

**API Tests (`tests/test_api/`)**
- HTTP request/response cycles
- Individual endpoint functionality
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

Currently uses in-memory storage. For production:

1. **Database Integration**: Replace repository with PostgreSQL/MongoDB
2. **Authentication**: Add JWT or OAuth2 authentication
3. **Rate Limiting**: Implement API rate limiting
4. **Caching**: Add Redis for improved performance
5. **Logging**: Structured logging with correlation IDs
6. **Monitoring**: Health checks and metrics
7. **Docker**: Containerization for deployment

### Environment Variables

```bash
# Example production environment
DATABASE_URL=postgresql://user:pass@localhost/skate_spots
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
```

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
- Code quality by [Ruff](https://github.com/astral-sh/ruff)
- Package management by [uv](https://github.com/astral-sh/uv)

## 📞 Support

For support, please open an issue in the GitHub repository or contact the development team.

---

**Happy skating!** 🛹