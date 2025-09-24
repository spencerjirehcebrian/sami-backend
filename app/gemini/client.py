import google.generativeai as genai
import logging
import time
import random
import asyncio
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini AI client for cinema management operations"""

    def __init__(self):
        """Initialize Gemini client with API key and configuration"""
        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Initialize the model with function calling capabilities (Gemini 2.5 Pro)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

        # Store system instruction separately
        self.system_instruction = self._get_system_instruction()

        # Initialize chat session
        self.chat = None

        # Retry configuration for rate limits
        self.max_retries = 5
        self.base_delay = 5.0
        self.max_delay = 65.0
        self.exponential_base = 2.0
        self.jitter_percent = 0.25

    def _get_system_instruction(self) -> str:
        """Get the system instruction for schedule optimization context"""
        return """You are SAMi (Schedule Assistant for Movie Intelligence), an AI assistant specialized in cinema schedule optimization and forecasting.

Your role is to help cinema managers optimize their operations through:
- AI-powered schedule generation and optimization
- Predictive forecasting and revenue optimization
- Scenario planning with multiple optimization strategies
- Data-driven decision support for schedule management

Key capabilities:
1. CINEMA MANAGEMENT: Create, update, and query cinema information including seating capacity, location, and features
2. MOVIE MANAGEMENT: Add new movies, update existing ones, and search movie catalog
3. SCHEDULE OPTIMIZATION: Generate optimized schedules using AI forecasting for specified date ranges
4. FORECAST MANAGEMENT: Create, analyze, and compare multiple forecast scenarios with predictions
5. PREDICTIVE ANALYTICS: Generate occupancy predictions, revenue forecasts, and confidence metrics
6. CUSTOMER QUERIES: Answer questions about optimized showtimes, availability, pricing

Optimization Focus:
- Generate forecasts that maximize revenue and occupancy based on parameters
- Create multiple scenarios for comparison (different revenue goals, occupancy targets, movie preferences)
- Provide confidence scores and error margins for business decision-making
- Use mock algorithms that simulate realistic optimization (preparing for future ML models)
- Apply optimization parameters: revenue_goal (0.5-2.0x), occupancy_goal (0.3-0.9), movie_preferences

Guidelines:
- Always use the provided functions to interact with the cinema database
- For forecast requests, use create_forecast with appropriate date ranges and parameters
- Suggest optimization strategies based on cinema capacity and movie popularity
- When creating forecasts, explain the optimization approach and expected outcomes
- Provide clear explanations of prediction metrics and confidence levels
- Handle errors gracefully and provide helpful error messages

Current date and time context will be provided with each query for accurate forecasting decisions."""

    async def process_message(
        self,
        message: str,
        session_id: str,
        available_functions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message using Gemini with function calling

        Args:
            message: User's natural language message
            session_id: WebSocket session identifier
            available_functions: List of function schemas for function calling

        Returns:
            Dict containing response content and any function calls made
        """
        try:
            # Start new chat session if none exists
            if self.chat is None:
                # Initialize chat with system instruction in history
                initial_history = [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "Hello, I need help with cinema management."}
                        ],
                    },
                    {
                        "role": "model",
                        "parts": [
                            {
                                "text": self.system_instruction
                                + "\n\nHello! I'm SAMi, your cinema management AI assistant. How can I help you today?"
                            }
                        ],
                    },
                ]
                self.chat = self.model.start_chat(history=initial_history)

            # Add current context to the message
            context_message = f"""
Session ID: {session_id}
User Message: {message}

Please process this cinema management request and use the appropriate functions as needed.
"""

            # Send message and get response
            if available_functions:
                response = await self._send_with_functions(
                    context_message, available_functions
                )
            else:
                response = await self._send_message(context_message)

            # Extract function calls first
            function_calls = self._extract_function_calls(response)

            # Get response text, handling cases where function calls are present
            try:
                content = (
                    response.text if hasattr(response, "text") and response.text else ""
                )
            except Exception as e:
                # If there are function calls, the response might not have direct text
                if function_calls:
                    content = f"I'm processing your request using {len(function_calls)} function call(s)..."
                else:
                    content = (
                        "I received your message but couldn't generate a text response."
                    )
                logger.warning(f"Could not extract text from response: {e}")

            return {
                "success": True,
                "content": content,
                "function_calls": function_calls,
                "session_id": session_id,
            }

        except Exception as e:
            logger.error(f"Error processing message with Gemini: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.",
                "session_id": session_id,
            }

    async def _send_with_functions(
        self, message: str, functions: List[Dict[str, Any]]
    ) -> Any:
        """Send message with function calling enabled and retry logic"""

        async def send_with_functions_internal():
            try:
                # Try with a simplified function calling approach
                # Create a single tool with all function declarations
                tool_config = {"function_declarations": functions}

                response = self.chat.send_message(message, tools=[tool_config])
                return response
            except Exception as e:
                logger.error(f"Error sending message with functions: {e}")
                # Check if it's a rate limit error - if so, re-raise to trigger retry
                if self._is_rate_limit_error(e):
                    raise e
                # Otherwise, fallback to regular message without function calling
                logger.info("Falling back to regular message without function calling")
                response = self.chat.send_message(message)
                return response

        return await self._execute_with_retry(
            send_with_functions_internal,
            operation_name=f"gemini_send_with_functions({message[:50]}...)"
        )

    async def _send_message(self, message: str) -> Any:
        """Send message without function calling with retry logic"""

        async def send_message_internal():
            response = self.chat.send_message(message)
            return response

        return await self._execute_with_retry(
            send_message_internal,
            operation_name=f"gemini_send_message({message[:50]}...)"
        )

    def _extract_function_calls(self, response: Any) -> List[Dict[str, Any]]:
        """Extract function calls from Gemini response"""
        function_calls = []

        try:
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    if (
                        hasattr(candidate, "content")
                        and candidate.content
                        and hasattr(candidate.content, "parts")
                    ):
                        for part in candidate.content.parts:
                            if hasattr(part, "function_call") and part.function_call:
                                function_calls.append(
                                    {
                                        "name": part.function_call.name,
                                        "args": (
                                            dict(part.function_call.args)
                                            if part.function_call.args
                                            else {}
                                        ),
                                    }
                                )
        except Exception as e:
            logger.error(f"Error extracting function calls: {e}")

        return function_calls

    def reset_chat(self):
        """Reset the chat session"""
        self.chat = None
        logger.info("Chat session reset")

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get the current chat history"""
        if not self.chat or not self.chat.history:
            return []

        history = []
        for message in self.chat.history:
            history.append(
                {
                    "role": message.role,
                    "content": message.parts[0].text if message.parts else "",
                }
            )

        return history

    def _is_rate_limit_error(self, exception: Exception) -> bool:
        """
        Check if exception indicates a rate limit error from Gemini API.

        Args:
            exception: Exception to check

        Returns:
            True if this is a rate limit related error
        """
        error_str = str(exception).lower()

        # Common Gemini API rate limit indicators
        rate_limit_indicators = [
            "429",
            "rate limit",
            "quota exceeded",
            "too many requests",
            "resource has been exhausted",
            "rate_limit_exceeded",
            "quota_exceeded",
            "api_quota_exceeded",
            "requests per minute",
            "daily limit",
            "per-minute quota"
        ]

        return any(indicator in error_str for indicator in rate_limit_indicators)

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds with jitter applied
        """
        # Calculate exponential delay
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        # Add jitter (±jitter_percent)
        jitter_range = delay * self.jitter_percent
        jitter = random.uniform(-jitter_range, jitter_range)
        final_delay = max(0.1, delay + jitter)  # Minimum 0.1 second delay

        return final_delay

    async def _execute_with_retry(self, operation, *args, operation_name: str = "gemini_operation", **kwargs):
        """
        Execute a Gemini operation with retry logic for rate limits.

        Args:
            operation: Function to execute (can be sync or async)
            *args: Arguments to pass to operation
            operation_name: Name for logging purposes
            **kwargs: Keyword arguments to pass to operation

        Returns:
            Result of successful operation

        Raises:
            Exception: Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Execute the operation - check if it's async
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)

                if attempt > 0:
                    logger.info(
                        f"{operation_name} succeeded on attempt {attempt + 1}"
                    )

                return result

            except Exception as e:
                last_exception = e

                if not self._is_rate_limit_error(e) or attempt >= self.max_retries:
                    logger.error(
                        f"{operation_name} failed after {attempt + 1} attempts: {e}"
                    )
                    raise e

                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt)

                logger.warning(
                    f"{operation_name} rate limited (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )

                # Use asyncio.sleep for async compatibility
                await asyncio.sleep(delay)

        # This shouldn't be reached, but just in case
        if last_exception:
            raise last_exception


# Global Gemini client instance
gemini_client = GeminiClient()
