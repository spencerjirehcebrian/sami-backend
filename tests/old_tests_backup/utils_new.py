"""
Simplified Test Utilities for SAMi Backend Testing

Basic utilities and retry mechanism for essential testing functionality.
Focused on the 80/20 principle - maximum value with minimal complexity.
"""

import asyncio
import json
import logging
import random
import time
import websockets
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SimpleRetry:
    """
    Simple exponential backoff retry mechanism for LLM API rate limits.

    Essential for LLM API stability without over-engineering.
    """

    def __init__(self, max_retries=3, base_delay=2.0):
        """
        Initialize simple retry handler.

        Args:
            max_retries: Maximum retry attempts (default 3)
            base_delay: Base delay in seconds (default 2s)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute(self, operation, *args, **kwargs):
        """Execute operation with retry logic for rate limits."""
        for attempt in range(self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                if self._is_rate_limit(e) and attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)  # Simple exponential
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                raise e

    def _is_rate_limit(self, exception):
        """Check if exception indicates rate limiting."""
        error_str = str(exception).lower()
        return any(term in error_str for term in ["rate limit", "429", "quota"])


class PromptTester:
    """
    Simplified WebSocket prompt tester.

    Essential functionality only - connection, send, receive, validate.
    """

    def __init__(self, session_id=None):
        """Initialize prompt tester with optional session ID."""
        self.session_id = session_id or f"test-{int(time.time())}"
        self.websocket = None
        self.retry = SimpleRetry()

    async def connect(self):
        """Connect to WebSocket endpoint."""
        url = f"ws://localhost:8000/ws/{self.session_id}"
        self.websocket = await websockets.connect(url)
        # Wait for welcome message
        await self.websocket.recv()

    async def disconnect(self):
        """Disconnect from WebSocket."""
        if self.websocket:
            await self.websocket.close()

    async def send_prompt(self, prompt: str) -> dict:
        """Send prompt with retry logic."""
        return await self.retry.execute(self._send_prompt_internal, prompt)

    async def _send_prompt_internal(self, prompt: str) -> dict:
        """Internal prompt sending logic."""
        message = {
            "type": "chat",
            "content": prompt,
            "metadata": {"test_timestamp": datetime.utcnow().isoformat() + "Z"}
        }

        await self.websocket.send(json.dumps(message))
        response_text = await self.websocket.recv()
        response = json.loads(response_text)

        # Check for rate limit in response content
        if self._is_rate_limit_response(response):
            raise Exception(f"Rate limit: {response.get('content', 'Rate limit exceeded')}")

        return response

    def _is_rate_limit_response(self, response: dict) -> bool:
        """Check if response indicates rate limiting."""
        if response.get("type") == "error":
            content = response.get("content", "").lower()
            return any(term in content for term in ["rate limit", "quota", "too many"])
        return False

    def assert_ai_response_valid(self, response: dict):
        """Validate AI response structure."""
        assert response.get("type") == "response", f"Expected response type, got {response.get('type')}"
        assert response.get("content"), "Response content is empty"
        assert response.get("metadata", {}).get("ai_powered") == True, "Should be AI-powered"


# Utility functions
def generate_test_session_id() -> str:
    """Generate unique test session ID."""
    return f"test_{int(time.time())}_{random.randint(1000, 9999)}"
