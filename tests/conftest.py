"""
Simplified pytest configuration and fixtures for SAMi Backend testing.

Minimal essential fixtures only - no over-engineering.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.cinema import CinemaType
from tests.utils import PromptTester, generate_test_session_id


# Database Setup for Testing
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup essential test data before any tests run."""
    db = SessionLocal()
    try:
        # Create cinema types if they don't exist
        cinema_types_data = [
            {"id": "standard", "name": "Standard", "description": "Traditional cinema experience", "price_multiplier": 1.0},
            {"id": "premium", "name": "Premium", "description": "Enhanced experience", "price_multiplier": 1.5},
            {"id": "imax", "name": "IMAX", "description": "Large format screens", "price_multiplier": 2.0},
            {"id": "vip", "name": "VIP", "description": "Exclusive experience", "price_multiplier": 2.5},
        ]

        for ct_data in cinema_types_data:
            # Check if cinema type already exists
            existing = db.query(CinemaType).filter(CinemaType.id == ct_data["id"]).first()
            if not existing:
                cinema_type = CinemaType(**ct_data)
                db.add(cinema_type)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Could not setup test cinema types: {e}")
    finally:
        db.close()


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
    import time
    import random
    timestamp = int(time.time())
    random_num = random.randint(1000, 9999)
    return {
        "title": f"Test Movie {timestamp}_{random_num}",
        "duration": 120,
        "genre": "Action",
        "rating": "PG-13",
        "description": "A test movie for API testing"
    }


@pytest.fixture
def sample_cinema_data():
    """Sample cinema data for testing."""
    import time
    import random
    timestamp = int(time.time())
    random_num = random.randint(1000, 9999)
    unique_number = int(str(timestamp)[-4:] + str(random_num)[-2:])
    return {
        "number": unique_number,
        "cinema_type": "standard",
        "total_seats": 100,
        "location": f"Test Location {timestamp}_{random_num}",
        "features": ["Test features"]
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for testing."""
    import time
    timestamp = int(time.time())
    return {
        "movie_id": f"test-movie-id-{timestamp}",
        "cinema_number": 1,
        "time_slot": "2024-12-01T20:00:00Z",
        "price": 15.00
    }


@pytest.fixture
def sample_forecast_data():
    """Sample forecast data for testing."""
    import time
    timestamp = int(time.time())
    return {
        "date_range_start": "2024-12-01",
        "date_range_end": "2024-12-07",
        "description": f"Test forecast for a week {timestamp}",
        "created_by": "test_user"
    }