"""
Simplified pytest configuration and fixtures for SAMi Backend testing.

Minimal essential fixtures only - no over-engineering.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import SessionLocal, get_db
from app.models.cinema import CinemaType
from app.models.movie import Movie
from app.models.cinema import Cinema
from app.models.schedule import Schedule
from app.models.forecast import Forecast, PredictionData
from tests.utils import PromptTester, generate_test_session_id


# Database Setup for Testing
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup essential test data before any tests run."""
    db = SessionLocal()
    try:
        # Create cinema types if they don't exist
        cinema_types_data = [
            {
                "id": "standard",
                "name": "Standard",
                "description": "Traditional cinema experience",
                "price_multiplier": 1.0,
            },
            {
                "id": "premium",
                "name": "Premium",
                "description": "Enhanced experience",
                "price_multiplier": 1.5,
            },
            {
                "id": "imax",
                "name": "IMAX",
                "description": "Large format screens",
                "price_multiplier": 2.0,
            },
            {
                "id": "vip",
                "name": "VIP",
                "description": "Exclusive experience",
                "price_multiplier": 2.5,
            },
        ]

        for ct_data in cinema_types_data:
            # Check if cinema type already exists
            existing = (
                db.query(CinemaType).filter(CinemaType.id == ct_data["id"]).first()
            )
            if not existing:
                cinema_type = CinemaType(**ct_data)
                db.add(cinema_type)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Could not setup test cinema types: {e}")
    finally:
        db.close()


# Database Cleanup Utilities
def cleanup_test_data(db_session=None):
    """Clean up test data in proper dependency order."""
    if db_session is None:
        db_session = SessionLocal()

    try:
        # Delete in dependency order to avoid foreign key constraints

        # Leverage CASCADE deletes - delete forecasts first, related data deletes automatically
        # This is much faster than manually deleting in dependency order
        deleted_forecasts = db_session.query(Forecast).filter(
            Forecast.created_by == 'test_user'
        ).delete(synchronize_session=False)

        # 4. Delete test movies (created by tests with timestamps in names)
        deleted_movies = db_session.query(Movie).filter(
            Movie.title.like('%Test Movie%')
        ).delete(synchronize_session=False)

        # 5. Delete test cinemas (created by tests with test locations)
        deleted_cinemas = db_session.query(Cinema).filter(
            Cinema.location.like('%Test Location%')
        ).delete(synchronize_session=False)

        db_session.commit()

        print(f"Database cleanup completed: "
              f"{deleted_forecasts} forecasts (CASCADE), "
              f"{deleted_movies} movies, "
              f"{deleted_cinemas} cinemas deleted")

    except Exception as e:
        db_session.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        if db_session != SessionLocal():
            db_session.close()


# Global tracking for cleanup efficiency
_cleanup_stats = {
    "class_cleanups_performed": 0,
    "items_cleaned_by_classes": 0
}

def track_cleanup_performed(items_cleaned):
    """Track that class-level cleanup was performed."""
    global _cleanup_stats
    _cleanup_stats["class_cleanups_performed"] += 1
    _cleanup_stats["items_cleaned_by_classes"] += items_cleaned

# Optimized session management for cleanup operations
_cleanup_session = None

def get_cleanup_session():
    """Get a reusable session for cleanup operations."""
    global _cleanup_session
    if _cleanup_session is None:
        _cleanup_session = SessionLocal()
    return _cleanup_session

def close_cleanup_session():
    """Close the cleanup session when done."""
    global _cleanup_session
    if _cleanup_session is not None:
        _cleanup_session.close()
        _cleanup_session = None

@pytest.fixture(scope="class", autouse=True)
def cleanup_after_test_class():
    """Automatically clean up test data after each test class."""
    # Reset cleanup tracking for this class
    global _cleanup_stats
    _cleanup_stats["class_cleanups_performed"] = 0
    _cleanup_stats["items_cleaned_by_classes"] = 0

    yield  # This runs before the test class

    # Only run global cleanup if class-level cleanup didn't handle everything
    # This avoids redundant database operations
    if _cleanup_stats["class_cleanups_performed"] == 0:
        cleanup_test_data()  # This runs after the test class
    else:
        print(f"Skipped redundant global cleanup - class-level cleanup handled {_cleanup_stats['items_cleaned_by_classes']} items")


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
        "description": "A test movie for API testing",
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
        "features": ["Test features"],
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
        "price": 15.00,
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
        "created_by": "test_user",
    }
