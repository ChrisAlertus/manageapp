# Household Management API Backend

FastAPI backend for the Household Management Application.

## Features

- User registration and authentication (JWT)
- PostgreSQL database with SQLAlchemy ORM
- Alembic database migrations
- Docker support for local development
- Automatic API documentation (Swagger/OpenAPI)
- **Deployment abstraction layer** for multi-platform support (Railway.app, Render.com, GCP, AWS)

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- PostgreSQL 15+ (or use Docker Compose)
- Docker and Docker Compose (optional, for containerized development)

### Installing uv

Install uv using one of these methods:

```bash
# Using pip
pip install uv

# Using homebrew (macOS)
brew install uv

# Using curl (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Local Development Setup

1. **Create a virtual environment and install dependencies:**

```bash
# Using uv (recommended - much faster)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Or using traditional pip
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Set up environment variables:**

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Edit `.env` and set:
- `SECRET_KEY`: A secure random string for JWT token signing
- `DATABASE_URL`: PostgreSQL connection string

4. **Set up the database:**

If using Docker Compose:

```bash
docker-compose up -d db
```

Or use your own PostgreSQL instance and update `DATABASE_URL` in `.env`.

5. **Run database migrations:**

```bash
alembic upgrade head
```

6. **Run the development server:**

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker Development

1. **Build and start services:**

```bash
docker-compose up --build
```

This will start:
- PostgreSQL database on port 5432
- FastAPI backend on port 8000

2. **Run migrations in the container:**

```bash
docker-compose exec backend alembic upgrade head
```

## Database Migrations

### Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations:

```bash
alembic upgrade head
```

### Rollback a migration:

```bash
alembic downgrade -1
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user information (requires authentication)

### Health Check

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   ├── database.py      # Database connection
│   │   └── security.py      # JWT and password hashing
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # User database model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py          # Pydantic schemas
│   └── api/
│       ├── deps.py          # FastAPI dependencies
│       └── v1/
│           └── auth.py       # Authentication routes
├── alembic/                 # Database migrations
├── pyproject.toml           # Project dependencies (uv/pip)
├── requirements.txt         # Python dependencies (legacy)
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Local development setup
└── .env.example            # Environment variables template
```

## Security Considerations

- Passwords are hashed using bcrypt
- JWT tokens are used for authentication
- CORS is configured for allowed origins
- Environment variables are used for sensitive configuration
- SQL injection prevention via SQLAlchemy ORM

## Using uv for Dependency Management

This project uses [uv](https://github.com/astral-sh/uv) for fast dependency management.

### Common uv Commands

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
uv pip install -e .

# Add a new dependency
uv pip install package-name
uv pip freeze > requirements.txt  # Update requirements.txt if needed

# Update dependencies
uv pip install --upgrade -e .

# Sync dependencies (install exactly as specified)
uv pip sync requirements.txt

# Keep requirements.txt in sync with pyproject.toml
./scripts/sync-requirements.sh
```

### Benefits of uv

- **10-100x faster** than pip for package installation
- Drop-in replacement for pip
- Better dependency resolution
- Works with both `pyproject.toml` and `requirements.txt`

## Development Guidelines

- Follow PEP-8 with 2-space indentation
- Use type hints for all function signatures
- Include docstrings for all functions
- Keep line length to 80 characters
- Use functional/declarative patterns where possible

## Testing

The project includes comprehensive unit and integration tests for the deployment abstraction layer.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_deployment.py

# Run integration tests
pytest tests/integration/
```

### Test Structure

- **Unit Tests**: `tests/unit/` - Fast, isolated tests for individual components
- **Integration Tests**: `tests/integration/` - Tests for real-world deployment scenarios
- **Fixtures**: `tests/conftest.py` - Shared test fixtures

### Documentation

- [Testing Guide](README_TESTING.md) - Complete testing documentation
- [Deployment Documentation](docs/DEPLOYMENT.md) - Deployment abstraction details

## License

[To be determined]

