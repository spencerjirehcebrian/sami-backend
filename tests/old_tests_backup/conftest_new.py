"""
Simplified pytest configuration and fixtures for SAMi Backend testing.

Minimal essential fixtures only - no over-engineering.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from app.main import app
from tests.utils_new import PromptTester, generate_test_session_id


# REST API Testing Fixtures
@pytest.fixture(scope="session")
def client():
    """FastAPI test client for REST API testing."""
    return TestClient(app)


# AI Integration Testing Fixtures
@pytest_asyncio.fixture
async def prompt_tester():
    """WebSocket prompt tester for AI integration tests."""
    tester = PromptTester(generate_test_session_id())
    await tester.connect()
    yield tester
    await tester.disconnect()


# Test Data Fixtures
@pytest.fixture
def sample_movie_data():
    """Sample movie data for testing."""
    return {
        "title": "Test Movie",
        "duration": 120,
        "genre": "Action",
        "rating": "PG-13",
        "description": "A test movie for API testing"
    }


@pytest.fixture
def sample_cinema_data():
    """Sample cinema data for testing."""
    return {
        "number": 99,
        "name": "Test Cinema",
        "capacity": 100,
        "type": "Standard"
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for testing."""
    return {
        "movie_id": "test-movie-id",
        "cinema_id": 99,
        "time_slot": "2024-12-01T20:00:00Z",
        "unit_price": 15.00
    }


@pytest.fixture
def sample_forecast_data():
    """Sample forecast data for testing."""
    return {
        "start_date": "2024-12-01",
        "end_date": "2024-12-07",
        "description": "Test forecast for a week"
    }