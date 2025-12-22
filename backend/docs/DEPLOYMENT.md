# Deployment Abstraction Layer

This document describes the deployment abstraction layer that enables the Household Management API to run on multiple cloud platforms without platform-specific code in the application logic.

## Overview

The deployment abstraction layer (`app/core/deployment.py`) provides:

- **Platform Detection**: Automatically detects the deployment platform (Railway, Render, GCP, AWS, or local)
- **Normalized Configuration**: Provides consistent configuration interface across all platforms
- **Environment Variable Handling**: Normalizes platform-specific environment variables
- **Database URL Management**: Handles different database connection string formats
- **Production Detection**: Identifies production vs development environments

## Supported Platforms

### Primary Platform: Railway.app

Railway.app is the primary deployment platform for this application.

**Detection**: Automatically detected via:
- `RAILWAY_ENVIRONMENT` environment variable
- `RAILWAY_PROJECT_ID` environment variable

**Configuration Available**:
- `service_name`: Railway service name
- `project_id`: Railway project ID
- `environment`: Railway environment name
- `region`: Railway region
- `replica_id`: Railway replica ID

**Example Environment Variables**:
```bash
RAILWAY_ENVIRONMENT=production
RAILWAY_PROJECT_ID=abc123
RAILWAY_SERVICE_NAME=api
DATABASE_URL=postgresql://railway:pass@railway.db:5432/railway
JWT_SECRET_KEY=your-secret-key
```

### Secondary Platform: Render.com

Render.com is supported as a secondary platform for easy migration.

**Detection**: Automatically detected via:
- `RENDER` environment variable (set to "true")
- `RENDER_SERVICE_ID` environment variable

**Configuration Available**:
- `service_id`: Render service ID
- `service_name`: Render service name
- `service_type`: Render service type
- `region`: Render region
- `instance_id`: Render instance ID

**Example Environment Variables**:
```bash
RENDER=true
RENDER_SERVICE_ID=srv-abc123
RENDER_SERVICE_NAME=api
DATABASE_URL=postgresql://render:pass@render.db:5432/render
JWT_SECRET_KEY=your-secret-key
```

### Local Development

Default platform when no cloud platform indicators are present.

**Detection**: No platform-specific environment variables detected

**Configuration Available**:
- `environment`: Always "development"
- `debug`: From `DEBUG` environment variable

**Example Environment Variables**:
```bash
DATABASE_URL=postgresql://localhost:5432/manageapp_db
JWT_SECRET_KEY=local-dev-secret
DEBUG=true
```

### Future Platforms

#### GCP (Google Cloud Platform)

**Detection**: Automatically detected via:
- `GOOGLE_CLOUD_PROJECT` environment variable
- `GCP_PROJECT` environment variable

**Status**: Configuration structure defined, full implementation pending.

#### AWS (Amazon Web Services)

**Detection**: Automatically detected via:
- `AWS_REGION` environment variable
- `AWS_EXECUTION_ENV` environment variable

**Status**: Configuration structure defined, full implementation pending.

## Usage

### Basic Usage

```python
from app.core.deployment import deployment

# Get the detected platform
platform = deployment.get_platform()
# Returns: DeploymentPlatform.RAILWAY, DeploymentPlatform.RENDER, etc.

# Check if running in production
is_prod = deployment.is_production()
# Returns: True or False

# Get database URL
db_url = deployment.get_database_url()
# Returns: Database connection string or None

# Get environment name
env = deployment.get_environment()
# Returns: "development", "staging", "production", etc.

# Get platform-specific configuration
service_name = deployment.get("service_name")
# Returns: Platform-specific value or None
```

### Platform Detection

The platform is detected in the following order:

1. **Explicit Override**: `DEPLOYMENT_PLATFORM` environment variable
2. **Railway**: `RAILWAY_ENVIRONMENT` or `RAILWAY_PROJECT_ID`
3. **Render**: `RENDER` or `RENDER_SERVICE_ID`
4. **GCP**: `GOOGLE_CLOUD_PROJECT` or `GCP_PROJECT`
5. **AWS**: `AWS_REGION` or `AWS_EXECUTION_ENV`
6. **Default**: Local development

### Explicit Platform Override

You can explicitly set the platform for testing or migration:

```bash
export DEPLOYMENT_PLATFORM=railway
# or
export DEPLOYMENT_PLATFORM=render
# or
export DEPLOYMENT_PLATFORM=local
```

### Production Detection

Production is detected when:
- `ENVIRONMENT` is set to "production", "prod", or "live"
- `RAILWAY_ENVIRONMENT` is set to "production", "prod", or "live"
- Platform is not LOCAL or UNKNOWN

### Database URL

The deployment abstraction handles database URLs consistently across platforms:

- **Railway**: Uses `DATABASE_URL` (automatically provided)
- **Render**: Uses `DATABASE_URL` (automatically provided)
- **Local**: Uses `DATABASE_URL` (from `.env` file)
- **GCP**: Uses `DATABASE_URL` or constructs from Cloud SQL config (future)
- **AWS**: Uses `DATABASE_URL` or constructs from RDS config (future)

All platforms use the standard PostgreSQL connection string format:
```
postgresql://user:password@host:port/database
```

## Integration with Application Configuration

The deployment abstraction is designed to work with `app/core/config.py`:

```python
from app.core.config import settings
from app.core.deployment import deployment

# settings.DATABASE_URL will work with deployment.get_database_url()
# Both use the same DATABASE_URL environment variable
```

## Migration Between Platforms

### Railway → Render

Migration is straightforward (1-2 hours):

1. Export environment variables from Railway
2. Create Render account and services
3. Set environment variables in Render dashboard
4. Deploy - the abstraction layer handles the rest

**No code changes required** - the abstraction layer handles platform differences.

### Railway → GCP/AWS

Migration is more complex (4-8 hours):

1. Set up GCP/AWS infrastructure
2. Configure database (Cloud SQL or RDS)
3. Set environment variables
4. Deploy - the abstraction layer handles platform detection

**Minimal code changes** - mainly infrastructure configuration.

## Testing

### Unit Tests

Unit tests verify platform detection and configuration loading:

```bash
pytest tests/unit/test_deployment.py
```

### Integration Tests

Integration tests verify real-world deployment scenarios:

```bash
pytest tests/integration/test_deployment_integration.py
```

### Running All Tests

```bash
pytest tests/
```

## Environment Variables Reference

### Required for All Platforms

- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Secret key for JWT token signing

### Railway.app Specific

- `RAILWAY_ENVIRONMENT`: Environment name (production, development, etc.)
- `RAILWAY_PROJECT_ID`: Railway project identifier
- `RAILWAY_SERVICE_NAME`: Service name
- `RAILWAY_REGION`: Deployment region
- `RAILWAY_REPLICA_ID`: Replica identifier

### Render.com Specific

- `RENDER`: Set to "true" when running on Render
- `RENDER_SERVICE_ID`: Render service identifier
- `RENDER_SERVICE_NAME`: Service name
- `RENDER_SERVICE_TYPE`: Service type (web, worker, etc.)
- `RENDER_REGION`: Deployment region
- `RENDER_INSTANCE_ID`: Instance identifier

### Local Development

- `DEBUG`: Set to "true" for debug mode
- `ENVIRONMENT`: Environment name (optional, defaults to "development")

### Platform Override

- `DEPLOYMENT_PLATFORM`: Explicitly set platform (railway, render, local, gcp, aws)

## Best Practices

1. **Never hardcode platform-specific logic** - Always use the deployment abstraction
2. **Use environment variables** - All configuration should come from environment variables
3. **Test on multiple platforms** - Use `DEPLOYMENT_PLATFORM` to test different platforms locally
4. **Document platform-specific requirements** - Keep this documentation updated
5. **Keep abstraction layer simple** - Don't add complex platform-specific logic

## Troubleshooting

### Platform Not Detected

If the platform is not detected correctly:

1. Check environment variables are set correctly
2. Use `DEPLOYMENT_PLATFORM` to explicitly set the platform
3. Verify platform-specific detection variables exist

### Database URL Issues

If database connection fails:

1. Verify `DATABASE_URL` is set correctly
2. Check connection string format (must be PostgreSQL format)
3. Ensure database is accessible from the deployment platform

### Production Detection Issues

If production detection is incorrect:

1. Set `ENVIRONMENT=production` explicitly
2. Check `RAILWAY_ENVIRONMENT` if using Railway
3. Verify platform detection is working correctly

## Future Enhancements

- [ ] Full GCP Cloud SQL database URL construction
- [ ] Full AWS RDS database URL construction
- [ ] Platform-specific health check endpoints
- [ ] Platform-specific logging configuration
- [ ] Platform-specific monitoring integration

## See Also

- [Railway.app Documentation](https://docs.railway.app/)
- [Render.com Documentation](https://render.com/docs)
- [Project Plan - Task 7.1](../PROJECT_PLAN.md#task-71-deployment-abstraction-layer)
