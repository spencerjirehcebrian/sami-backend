# SAMi Backend Testing

Testing framework for SAMi cinema management system covering REST APIs, AI integration, and business flows.

## Setup

```bash
cd sami-backend
poetry install
poetry run alembic upgrade head
poetry run python alembic/seed.py
```

## Test Files

- **`test_rest_apis.py`** - REST API endpoints and database operations
- **`test_ai_integration.py`** - AI-powered functionality and integration
- **`test_basic_flows.py`** - End-to-end user scenarios and workflows
- **`conftest.py`** - Pytest fixtures and test setup
- **`utils.py`** - Test utilities and helpers
- **`run_tests.py`** - Main test runner with reporting

## Essential Commands

### Run All Tests
```bash
# Using test runner (recommended)
poetry run python tests/run_tests.py

# Using pytest directly
poetry run pytest tests/ -v
```

### Run Specific Test Files
```bash
poetry run pytest tests/test_rest_apis.py -v
poetry run pytest tests/test_ai_integration.py -v
poetry run pytest tests/test_basic_flows.py -v
```

### Run Specific Test Classes
```bash
# REST API tests
poetry run pytest tests/test_rest_apis.py::TestMoviesAPI -v
poetry run pytest tests/test_rest_apis.py::TestCinemasAPI -v
poetry run pytest tests/test_rest_apis.py::TestSchedulesAPI -v

# AI Integration tests
poetry run pytest tests/test_ai_integration.py::TestCinemaAIIntegration -v
poetry run pytest tests/test_ai_integration.py::TestMovieAIIntegration -v
poetry run pytest tests/test_ai_integration.py::TestScheduleAIIntegration -v
poetry run pytest tests/test_ai_integration.py::TestForecastAIIntegration -v

# Basic Flow tests
poetry run pytest tests/test_basic_flows.py::TestMovieDiscoveryFlow -v
poetry run pytest tests/test_basic_flows.py::TestBookingFlow -v
poetry run pytest tests/test_basic_flows.py::TestAnalyticsFlow -v
```

### Run Specific Test Methods
```bash
poetry run pytest tests/test_rest_apis.py::TestMoviesAPI::test_get_all_movies -v
poetry run pytest tests/test_rest_apis.py::TestMoviesAPI::test_create_movie -v
poetry run pytest tests/test_ai_integration.py::TestCinemaAIIntegration::test_cinema_recommendations -v
```

### Advanced Options
```bash
# With coverage
poetry run pytest --cov=app tests/

# Parallel execution
poetry run pytest tests/ -n auto

# Stop on first failure
poetry run pytest tests/ -x

# Verbose with output
poetry run pytest tests/ -v -s

# Debug mode
poetry run pytest tests/ --pdb
```

## Test Categories

**REST APIs**: CRUD operations, validation, error handling
**AI Integration**: AI queries, recommendations, processing validation
**Basic Flows**: End-to-end scenarios, business logic, workflows

## Quick Troubleshooting

```bash
# Database issues
poetry run alembic upgrade head
poetry run python alembic/seed.py

# Dependencies
poetry install

# Specific failing test
poetry run pytest tests/test_rest_apis.py::TestMoviesAPI::test_get_all_movies -v -s
```

## Performance Targets
- Complete test suite: < 5 minutes
- Individual tests: < 30 seconds
- Success rate: > 95%