FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install Python dependencies using uv (reads from pyproject.toml)
# Install Python dependencies using uv, letting uv resolve from pyproject.toml and requirements.txt if available
COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE $PORT

# Run the application - use PORT env var with fallback to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
