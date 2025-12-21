# Testing Guide

This document describes how to run tests for the Household Management API backend.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── unit/                     # Unit tests
│   ├── __init__.py
│   └── test_deployment.py   # Deployment abstraction tests
└── integration/             # Integration tests
    ├── __init__.py
    └── test_deployment_integration.py  # Deployment integration tests
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Integration Tests Only

```bash
pytest tests/integration/
```

### Run Specific Test File

```bash
pytest tests/unit/test_deployment.py
```

### Run Specific Test

```bash
pytest tests/unit/test_deployment.py::TestDeploymentConfig::test_railway_detection
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

This generates:
- Terminal coverage report
- HTML report in `htmlcov/index.html`
- XML report in `coverage.xml`

### Run with Verbose Output

```bash
pytest -v
```

### Run with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Fixtures

### Available Fixtures

- `local_environment`: Local development environment variables
- `railway_environment`: Railway.app environment variables
- `render_environment`: Render.com environment variables
- `deployment_config`: Factory for creating DeploymentConfig instances

### Using Fixtures

```python
def test_something(local_environment):
    # local_environment provides mocked environment variables
    config = DeploymentConfig()
    assert config.get_platform() == DeploymentPlatform.LOCAL
```

## Writing Tests

### Unit Test Example

```python
def test_platform_detection():
    """Test platform detection logic."""
    with patch.dict(os.environ, {"RAILWAY_ENVIRONMENT": "production"}):
        config = DeploymentConfig()
        assert config.get_platform() == DeploymentPlatform.RAILWAY
```

### Integration Test Example

```python
def test_railway_production_environment(railway_environment):
    """Test Railway production environment."""
    config = DeploymentConfig()
    assert config.get_platform() == DeploymentPlatform.RAILWAY
    assert config.is_production() is True
```

## Test Coverage

Current test coverage targets:

- **Deployment Abstraction**: 100% coverage
  - Platform detection
  - Configuration loading
  - Environment variable handling
  - Database URL management

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml
```

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running tests from the project root:

```bash
cd backend
pytest
```

### Environment Variable Conflicts

Tests use `unittest.mock.patch` to isolate environment variables. If you see conflicts:

1. Check that tests are using fixtures or `patch.dict`
2. Ensure tests clean up after themselves
3. Use `clear=True` in `patch.dict` to clear existing env vars

### Platform Detection Issues

If platform detection tests fail:

1. Ensure `patch.dict` is clearing environment variables
2. Check that test environment doesn't have conflicting variables
3. Use explicit `DEPLOYMENT_PLATFORM` in tests if needed

## Best Practices

1. **Isolate Tests**: Each test should be independent
2. **Use Fixtures**: Reuse common test setup with fixtures
3. **Mock External Dependencies**: Don't rely on external services
4. **Clear Environment**: Always clear environment variables in tests
5. **Descriptive Names**: Use clear test function and class names
6. **Documentation**: Add docstrings to test functions explaining what they test. Inputs and the expected behaviour.

## See Also

- [Pytest Documentation](https://docs.pytest.org/)
- [Deployment Documentation](docs/DEPLOYMENT.md)
- [Project Plan](../PROJECT_PLAN.md)
