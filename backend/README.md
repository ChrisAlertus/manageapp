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
- `JWT_SECRET_KEY`: A secure random string for JWT token signing
- `DATABASE_URL`: PostgreSQL connection string
- `RESEND_API_KEY`: API Key for Resend email service

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

### Households

- `POST /api/v1/households` - Create a new household (requires authentication)
- `GET /api/v1/households` - List all households where current user is a member (requires authentication)
- `GET /api/v1/households/{household_id}` - Get household details (requires authentication, must be a member)
- `POST /api/v1/households/{household_id}/leave` - Leave a household (requires authentication, must be a member)
- `POST /api/v1/households/{household_id}/transfer-ownership` - Transfer ownership to another member (requires authentication, owners only)
- `DELETE /api/v1/households/{household_id}` - Delete a household (requires authentication, owners only)

**Note**: All household endpoints require authentication. Users can only access households they are members of. Non-members will receive a 404 error to prevent household ID enumeration.

#### Example: Creating a Household

```bash
# First, login to get a token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "YourPassword123!"}' \
  | jq -r '.access_token')

# Create a household
curl -X POST "http://localhost:8000/api/v1/households" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Household",
    "description": "A shared household for managing expenses"
  }'
```

#### Example: Listing Households

```bash
curl -X GET "http://localhost:8000/api/v1/households" \
  -H "Authorization: Bearer $TOKEN"
```

#### Example: Getting Household Details

```bash
curl -X GET "http://localhost:8000/api/v1/households/1" \
  -H "Authorization: Bearer $TOKEN"
```

#### Example: Leaving a Household

```bash
curl -X POST "http://localhost:8000/api/v1/households/1/leave" \
  -H "Authorization: Bearer $TOKEN"
```

**Note**: The last owner of a household cannot leave. They must first transfer ownership or invite another owner.

#### Example: Transferring Ownership

```bash
curl -X POST "http://localhost:8000/api/v1/households/1/transfer-ownership" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_owner_id": 2
  }'
```

**Note**: Only owners can transfer ownership. The new owner must already be a member of the household. Ownership is shared (both users remain owners after transfer).

#### Example: Deleting a Household

```bash
curl -X DELETE "http://localhost:8000/api/v1/households/1" \
  -H "Authorization: Bearer $TOKEN"
```

**Note**: Only owners can delete a household. This will permanently delete the household and all associated memberships.

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
│   │   ├── user.py          # User database model
│   │   ├── household.py     # Household database model
│   │   └── household_member.py  # Household membership model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py          # Pydantic schemas
│   │   └── household.py     # Household Pydantic schemas
│   └── api/
│       ├── deps.py          # FastAPI dependencies
│       └── v1/
│           ├── auth.py       # Authentication routes
│           └── households.py  # Household management routes
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
# Run all tests (fast, no coverage)
pytest

# Run with coverage (slower, for CI/reports)
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_deployment.py

# Run integration tests
pytest tests/integration/

# Run only unit tests (fastest)
pytest tests/unit/ -m unit

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

**Performance Tips:**
- Coverage is disabled by default for faster test runs
- Tests automatically use faster bcrypt rounds (4 instead of 12)
- Use `-m unit` to skip slower integration tests during development
- Use `-n auto` with pytest-xdist for parallel test execution

### Test Structure

- **Unit Tests**: `tests/unit/` - Fast, isolated tests for individual components
- **Integration Tests**: `tests/integration/` - Tests for real-world deployment scenarios
- **Fixtures**: `tests/conftest.py` - Shared test fixtures

### Documentation

- [Testing Guide](README_TESTING.md) - Complete testing documentation
- [Deployment Documentation](docs/DEPLOYMENT.md) - Deployment abstraction details

## License

[To be determined]

