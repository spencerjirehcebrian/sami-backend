"""
Pytest configuration and fixtures for SAMi Backend testing.

This module provides shared fixtures and configuration for all test modules,
including database setup, backend connectivity, and test data management.
"""

import pytest
import asyncio
import logging
from datetime import datetime
from typing import Generator, AsyncGenerator
from tests.prompt_tester import PromptTester, TestSession, ensure_backend_running, wait_for_backend

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BACKEND_STARTUP_TIMEOUT = 30
TEST_TIMEOUT = 30


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the entire test session.
    This ensures all async tests run in the same event loop.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def ensure_backend() -> None:
    """
    Ensure the backend is running before any tests execute.
    This fixture runs automatically for the entire test session.
    """
    logger.info("Checking backend availability...")

    try:
        await wait_for_backend(max_wait=BACKEND_STARTUP_TIMEOUT)
        logger.info("Backend is available")
    except TimeoutError:
        pytest.fail(
            f"Backend is not available after {BACKEND_STARTUP_TIMEOUT} seconds. "
            "Please ensure the SAMi backend is running on localhost:8000"
        )


@pytest.fixture
async def prompt_tester() -> AsyncGenerator[PromptTester, None]:
    """
    Provide a PromptTester instance with automatic connection management.

    This is the primary fixture for individual test functions.
    """
    session_id = f"test-{datetime.now().isoformat()}-{id(asyncio.current_task())}"
    tester = PromptTester(session_id=session_id, timeout=TEST_TIMEOUT)

    try:
        await tester.connect()
        yield tester
    finally:
        await tester.disconnect()


@pytest.fixture
async def test_session() -> AsyncGenerator[TestSession, None]:
    """
    Provide a TestSession context manager for tests that need explicit session control.
    """
    session_id = f"session-{datetime.now().isoformat()}-{id(asyncio.current_task())}"
    session = TestSession(session_id=session_id, timeout=TEST_TIMEOUT)

    # Context manager handles connection lifecycle automatically
    async with session as tester:
        yield session


@pytest.fixture
def unique_session_id() -> str:
    """
    Generate a unique session ID for tests that need custom session management.
    """
    return f"custom-{datetime.now().isoformat()}-{id(asyncio.current_task())}"


@pytest.fixture(scope="module")
async def shared_tester() -> AsyncGenerator[PromptTester, None]:
    """
    Provide a shared PromptTester instance for module-level tests.

    Use this for tests that need to share context across multiple test functions
    within the same module.
    """
    session_id = f"shared-{datetime.now().isoformat()}"
    tester = PromptTester(session_id=session_id, timeout=TEST_TIMEOUT)

    try:
        await tester.connect()
        yield tester
    finally:
        await tester.disconnect()


@pytest.fixture
def test_prompts():
    """
    Provide common test prompts for reuse across test modules.
    """
    return {
        "cinema": {
            "list_all": [
                "Show me all cinemas",
                "List all movie theaters",
                "What cinemas do we have?",
                "Give me the cinema information",
                "I need to see all our theaters"
            ],
            "get_specific": [
                ("Tell me about Cinema 5", 5),
                ("What's the capacity of Cinema 1?", 1),
                ("Show me details for theater number 3", 3),
                ("I need info on Cinema 10", 10)
            ]
        },
        "movie": {
            "search": [
                ("Find all action movies", "action"),
                ("Show me horror films", "horror"),
                ("What comedies do we have?", "comedy"),
                ("List PG-13 movies", "PG-13")
            ],
            "add": [
                {
                    "prompt": "Add a new movie called 'Test Adventure' that's 120 minutes long, rated PG-13, action genre, about a hero's journey",
                    "expected_title": "Test Adventure",
                    "expected_duration": 120,
                    "expected_rating": "PG-13",
                    "expected_genre": "action"
                }
            ]
        },
        "schedule": {
            "create": [
                "Schedule Avatar for Cinema 1 tomorrow at 8:00 PM with ticket price $15",
                "Add a showing of Inception in Theater 2 at 7:30 PM tomorrow for $12",
                "Book Cinema 3 for Spider-Man at 9:00 PM tomorrow, price $18"
            ],
            "check_availability": [
                "What time slots are available for Cinema 1 tomorrow?",
                "When is Cinema 5 free next week?",
                "Show me available times for all theaters on Friday"
            ]
        },
        "analytics": {
            "revenue": [
                "Show me today's revenue",
                "What was our revenue this week?",
                "Generate a revenue report for Cinema 1",
                "How much money did we make yesterday?"
            ],
            "occupancy": [
                "What's our occupancy rate today?",
                "Show me how full our theaters are",
                "Which cinemas have the best attendance?",
                "Generate an occupancy report for this week"
            ]
        },
        "errors": {
            "invalid": [
                "Schedule a movie for Cinema 999 tomorrow",  # Non-existent cinema
                "Show me revenue for the year 3000",         # Invalid date
                "Add a movie with -50 minutes duration",     # Invalid duration
                "Book Cinema 1 at 25:00",                   # Invalid time
            ],
            "ambiguous": [
                "Schedule a movie tomorrow",           # Missing movie, cinema, time
                "What's the revenue?",                # Missing time period
                "Cancel the showing",                 # Missing which showing
                "Update the movie",                   # Missing which movie and what to update
            ]
        }
    }


@pytest.fixture
def performance_thresholds():
    """
    Provide performance thresholds for response time testing.
    """
    return {
        "fast_response": 2.0,      # 2 seconds for simple queries
        "normal_response": 5.0,    # 5 seconds for complex operations
        "slow_response": 10.0,     # 10 seconds for heavy analytics
    }


# Pytest markers for test categorization
pytest_markers = [
    "cinema: Cinema management tests",
    "movie: Movie management tests",
    "schedule: Schedule management tests",
    "analytics: Analytics and reporting tests",
    "error: Error handling tests",
    "context: Context and follow-up tests",
    "performance: Performance tests",
    "integration: Integration tests",
    "smoke: Smoke tests for basic functionality"
]


def pytest_configure(config):
    """Configure pytest markers."""
    for marker in pytest_markers:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers based on test file names."""
    for item in items:
        # Add markers based on test file names
        if "cinema" in str(item.fspath):
            item.add_marker(pytest.mark.cinema)
        elif "movie" in str(item.fspath):
            item.add_marker(pytest.mark.movie)
        elif "schedule" in str(item.fspath):
            item.add_marker(pytest.mark.schedule)
        elif "analytics" in str(item.fspath):
            item.add_marker(pytest.mark.analytics)
        elif "error" in str(item.fspath):
            item.add_marker(pytest.mark.error)
        elif "context" in str(item.fspath):
            item.add_marker(pytest.mark.context)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

        # Add integration marker to all e2e tests
        item.add_marker(pytest.mark.integration)


@pytest.fixture(autouse=True)
def test_logging(request):
    """Add test-specific logging context."""
    test_name = request.node.name
    logger.info(f"Starting test: {test_name}")

    yield

    logger.info(f"Completed test: {test_name}")


# Async test timeout configuration
@pytest.fixture(autouse=True)
def timeout_all_tests():
    """Apply a default timeout to all tests."""
    # This will be handled by pytest-asyncio and our individual test timeouts
    pass


# Error handling helpers
class TestError(Exception):
    """Custom exception for test-specific errors."""
    pass


@pytest.fixture
def assert_ai_response():
    """
    Provide a helper function for asserting AI response quality.
    """
    def _assert_ai_response(response, expected_content_keywords=None, min_length=10):
        """
        Assert that a response is a valid AI response.

        Args:
            response: The response dictionary to validate
            expected_content_keywords: List of keywords that should appear in content
            min_length: Minimum content length
        """
        assert response.get("type") == "response", f"Expected response type, got {response.get('type')}"

        content = response.get("content", "")
        assert len(content) >= min_length, f"Response too short: {len(content)} < {min_length}"

        if expected_content_keywords:
            content_lower = content.lower()
            for keyword in expected_content_keywords:
                assert keyword.lower() in content_lower, f"Missing keyword '{keyword}' in response"

        # Check AI metadata
        metadata = response.get("metadata", {})
        assert metadata.get("ai_powered") == True, "Response should be AI-powered"

        return True

    return _assert_ai_response


# Test data validation helpers
@pytest.fixture
def test_data_seeds():
    """
    Provide information about test data that should be available in the database.
    This assumes the database has been seeded with test data.
    """
    return {
        "cinemas": [
            {"id": 1, "name": "Cinema 1", "capacity": 100},
            {"id": 2, "name": "Cinema 2", "capacity": 150},
            {"id": 3, "name": "Cinema 3", "capacity": 200},
            # Add more based on your seed data
        ],
        "movies": [
            {"title": "Avatar", "genre": "Sci-Fi", "rating": "PG-13"},
            {"title": "Inception", "genre": "Thriller", "rating": "PG-13"},
            {"title": "Spider-Man", "genre": "Action", "rating": "PG-13"},
            # Add more based on your seed data
        ]
    }


# Cleanup helpers
@pytest.fixture(autouse=True, scope="session")
def cleanup_test_sessions():
    """
    Cleanup any test sessions at the end of the test run.
    """
    yield

    # Any cleanup logic can go here
    logger.info("Test session cleanup completed")