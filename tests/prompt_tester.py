"""
Core PromptTester class for WebSocket-based end-to-end testing of the SAMi Backend.

This module provides the primary testing interface for validating the natural language
processing pipeline through direct WebSocket communication.
"""

import asyncio
import json
import websockets
import pytest
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from tests.utils import RetryHandler

# Test configuration
WEBSOCKET_URL = "ws://localhost:8000/ws"
TEST_SESSION_PREFIX = "test-session"
DEFAULT_TIMEOUT = 30  # seconds

logger = logging.getLogger(__name__)


class PromptTester:
    """
    Core testing class for WebSocket-based prompt testing.

    Handles connection management, message sending, and response validation
    for end-to-end testing of the SAMi AI pipeline.
    """

    def __init__(self, session_id: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the PromptTester.

        Args:
            session_id: Optional custom session ID. If None, generates a unique ID.
            timeout: Timeout in seconds for WebSocket operations.
        """
        self.websocket = None
        self.session_id = session_id or f"{TEST_SESSION_PREFIX}-{datetime.now().isoformat()}"
        self.timeout = timeout
        self.url = f"{WEBSOCKET_URL}/{self.session_id}"
        self.connected = False
        self.retry_handler = RetryHandler(
            base_delay=5.0,
            max_delay=65.0,
            max_retries=5
        )

    async def connect(self):
        """Establish WebSocket connection to the backend."""
        try:
            self.websocket = await websockets.connect(self.url)
            self.connected = True
            logger.info(f"Connected to WebSocket: {self.url}")

            # Wait for welcome message
            welcome_msg = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=self.timeout
            )
            logger.info(f"Received welcome message: {welcome_msg}")

        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise ConnectionError(f"Could not connect to {self.url}: {e}")

    async def disconnect(self):
        """Close WebSocket connection."""
        if self.websocket and self.connected:
            try:
                await self.websocket.close()
                self.connected = False
                logger.info(f"Disconnected from WebSocket: {self.session_id}")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")

    async def send_prompt(self, prompt: str, message_type: str = "chat") -> Dict[str, Any]:
        """
        Send a prompt and return the parsed response with automatic retry logic.

        This method includes exponential backoff retry logic for handling rate limits.
        Use send_prompt_no_retry() if you need to disable retry behavior.

        Args:
            prompt: The natural language prompt to send
            message_type: Type of message ("chat", "command", "ping")

        Returns:
            Dict containing the parsed response from the backend

        Raises:
            ConnectionError: If not connected to WebSocket
            TimeoutError: If response takes longer than timeout
            ValueError: If response cannot be parsed
            Exception: If all retries are exhausted
        """
        return await self.send_prompt_with_retry(prompt, message_type)

    async def send_prompt_no_retry(self, prompt: str, message_type: str = "chat") -> Dict[str, Any]:
        """
        Send a prompt without retry logic (original behavior).

        Use this method when you specifically don't want retry logic,
        such as when testing error conditions.

        Args:
            prompt: The natural language prompt to send
            message_type: Type of message ("chat", "command", "ping")

        Returns:
            Dict containing the parsed response from the backend

        Raises:
            ConnectionError: If not connected to WebSocket
            TimeoutError: If response takes longer than timeout
            ValueError: If response cannot be parsed
        """
        return await self._send_prompt_internal(prompt, message_type)

    async def _send_prompt_internal(self, prompt: str, message_type: str = "chat") -> Dict[str, Any]:
        """
        Internal method for sending prompt without retry logic.

        This is the core prompt sending logic that will be wrapped with retry handling.
        """
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to WebSocket")

        # Create message payload
        message = {
            "type": message_type,
            "content": prompt,
            "metadata": {
                "test_timestamp": datetime.utcnow().isoformat() + "Z",
                "test_session": self.session_id
            }
        }

        try:
            # Send the message
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent message: {prompt[:100]}...")

            # Wait for response
            response_text = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=self.timeout
            )

            # Parse response
            response = json.loads(response_text)
            logger.info(f"Received response: {response.get('type', 'unknown')} - {response.get('content', '')[:100]}...")

            # Check if response indicates rate limiting
            if self._is_rate_limit_response(response):
                raise Exception(f"Rate limit error: {response.get('content', 'Rate limit exceeded')}")

            return response

        except asyncio.TimeoutError:
            raise TimeoutError(f"No response received within {self.timeout} seconds")
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse response as JSON: {e}")
        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            raise

    def _is_rate_limit_response(self, response: Dict[str, Any]) -> bool:
        """Check if response indicates a rate limit error."""
        if response.get("type") == "error":
            content = response.get("content", "").lower()
            rate_limit_indicators = [
                "rate limit", "quota exceeded", "too many requests",
                "resource exhausted", "api quota", "rate_limit_exceeded"
            ]
            return any(indicator in content for indicator in rate_limit_indicators)
        return False

    async def send_prompt_with_retry(self, prompt: str, message_type: str = "chat") -> Dict[str, Any]:
        """
        Send a prompt with exponential backoff retry logic for rate limits.

        Args:
            prompt: The natural language prompt to send
            message_type: Type of message ("chat", "command", "ping")

        Returns:
            Dict containing the parsed response from the backend

        Raises:
            ConnectionError: If not connected to WebSocket
            TimeoutError: If response takes longer than timeout
            ValueError: If response cannot be parsed
            Exception: If all retries are exhausted
        """
        return await self.retry_handler.execute_with_retry(
            self._send_prompt_internal,
            prompt,
            message_type,
            operation_name=f"send_prompt({prompt[:50]}...)"
        )

    async def send_prompt_expect_success(self, prompt: str) -> Dict[str, Any]:
        """
        Send a prompt and validate that it succeeds.

        Args:
            prompt: The natural language prompt to send

        Returns:
            Dict containing the successful response

        Raises:
            AssertionError: If the response indicates an error
        """
        response = await self.send_prompt(prompt)

        # Validate response is successful
        assert response.get("type") != "error", f"Request failed: {response.get('content', 'Unknown error')}"
        assert response.get("content"), "Response content is empty"

        return response

    async def send_prompt_expect_error(self, prompt: str) -> Dict[str, Any]:
        """
        Send a prompt and validate that it results in an error.

        Args:
            prompt: The natural language prompt that should fail

        Returns:
            Dict containing the error response

        Raises:
            AssertionError: If the response does not indicate an error
        """
        response = await self.send_prompt(prompt)

        # Validate response is an error or contains error indicators
        error_indicators = ["error", "cannot", "unable", "invalid", "failed"]

        is_error = (
            response.get("type") == "error" or
            any(indicator in response.get("content", "").lower() for indicator in error_indicators)
        )

        assert is_error, f"Expected error response, got: {response.get('content', 'No content')}"

        return response

    def validate_response_structure(self, response: Dict[str, Any]) -> None:
        """
        Validate that a response has the expected structure.

        Args:
            response: The response dictionary to validate

        Raises:
            AssertionError: If response structure is invalid
        """
        # Required fields
        assert "type" in response, "Response missing 'type' field"
        assert "content" in response, "Response missing 'content' field"
        assert "timestamp" in response, "Response missing 'timestamp' field"

        # Type should be valid
        valid_types = ["response", "error", "system", "typing", "pong"]
        assert response["type"] in valid_types, f"Invalid response type: {response['type']}"

        # Content should be string
        assert isinstance(response["content"], str), "Response content must be string"

        # Timestamp should be valid ISO format
        try:
            datetime.fromisoformat(response["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            assert False, f"Invalid timestamp format: {response['timestamp']}"

    def validate_ai_response(self, response: Dict[str, Any]) -> None:
        """
        Validate that a response indicates AI processing occurred.

        Args:
            response: The response dictionary to validate

        Raises:
            AssertionError: If response doesn't show AI processing
        """
        self.validate_response_structure(response)

        # Should have metadata indicating AI processing
        metadata = response.get("metadata", {})
        assert metadata.get("ai_powered") == True, "Response should be AI-powered"
        assert "handler" in metadata, "Response should have handler information"

        # Function calls should be tracked
        assert "function_calls_made" in metadata, "Response should track function calls"
        assert isinstance(metadata["function_calls_made"], int), "Function calls should be integer"

    def get_retry_metrics(self) -> Dict[str, Any]:
        """
        Get retry metrics for this PromptTester session.

        Returns:
            Dict containing retry statistics and performance data
        """
        metrics = self.retry_handler.metrics
        return {
            "total_attempts": metrics.total_attempts,
            "successful_attempts": metrics.successful_attempts,
            "rate_limit_hits": metrics.rate_limit_hits,
            "total_backoff_time": metrics.total_backoff_time,
            "max_delay_used": metrics.max_delay_used,
            "retry_rate": metrics.retry_rate,
            "session_id": self.session_id
        }


class TestSession:
    """
    Context manager for test sessions that automatically handles connection lifecycle.
    """

    def __init__(self, session_id: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        self.tester = PromptTester(session_id, timeout)

    async def __aenter__(self):
        await self.tester.connect()
        return self.tester

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.tester.disconnect()


class TestDataValidator:
    """
    Utility class for validating test data and responses.
    """

    @staticmethod
    def validate_cinema_response(response: Dict[str, Any], expected_cinema_id: Optional[int] = None) -> None:
        """Validate a cinema-related response."""
        content = response.get("content", "").lower()

        assert "cinema" in content or "theater" in content, "Response should mention cinema/theater"

        if expected_cinema_id:
            assert str(expected_cinema_id) in response.get("content", ""), f"Response should mention cinema {expected_cinema_id}"

    @staticmethod
    def validate_movie_response(response: Dict[str, Any], expected_movie: Optional[str] = None) -> None:
        """Validate a movie-related response."""
        content = response.get("content", "").lower()

        assert "movie" in content or "film" in content, "Response should mention movie/film"

        if expected_movie:
            assert expected_movie.lower() in content, f"Response should mention movie '{expected_movie}'"

    @staticmethod
    def validate_schedule_response(response: Dict[str, Any]) -> None:
        """Validate a schedule-related response."""
        content = response.get("content", "").lower()

        schedule_indicators = ["schedule", "showing", "time", "booked", "available"]
        assert any(indicator in content for indicator in schedule_indicators), "Response should mention scheduling"

    @staticmethod
    def validate_analytics_response(response: Dict[str, Any], metric_type: str) -> None:
        """Validate an analytics-related response."""
        content = response.get("content", "").lower()

        if metric_type == "revenue":
            revenue_indicators = ["revenue", "money", "earnings", "$", "income"]
            assert any(indicator in content for indicator in revenue_indicators), "Response should mention revenue"

        elif metric_type == "occupancy":
            occupancy_indicators = ["occupancy", "attendance", "full", "empty", "capacity"]
            assert any(indicator in content for indicator in occupancy_indicators), "Response should mention occupancy"

    @staticmethod
    def validate_error_response(response: Dict[str, Any]) -> None:
        """Validate an error response."""
        content = response.get("content", "").lower()
        error_indicators = ["error", "cannot", "unable", "invalid", "failed", "sorry"]

        assert (
            response.get("type") == "error" or
            any(indicator in content for indicator in error_indicators)
        ), "Response should indicate an error"


# Utility functions for test setup
async def ensure_backend_running(url: str = WEBSOCKET_URL) -> bool:
    """
    Check if the backend is running and accessible.

    Returns:
        bool: True if backend is accessible, False otherwise
    """
    try:
        # Try to connect to a test session
        test_session_id = f"health-check-{datetime.now().isoformat()}"
        test_url = f"{url}/{test_session_id}"

        websocket = await websockets.connect(test_url)
        await websocket.close()

        logger.info("Backend is running and accessible")
        return True

    except Exception as e:
        logger.error(f"Backend not accessible: {e}")
        return False


async def wait_for_backend(max_wait: int = 30, check_interval: int = 2) -> None:
    """
    Wait for the backend to become available.

    Args:
        max_wait: Maximum time to wait in seconds
        check_interval: Time between checks in seconds

    Raises:
        TimeoutError: If backend doesn't become available within max_wait
    """
    start_time = datetime.now()

    while (datetime.now() - start_time).total_seconds() < max_wait:
        if await ensure_backend_running():
            return

        logger.info(f"Waiting for backend... ({check_interval}s)")
        await asyncio.sleep(check_interval)

    raise TimeoutError(f"Backend did not become available within {max_wait} seconds")