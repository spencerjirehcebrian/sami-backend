import google.generativeai as genai
import logging
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """Google Gemini AI client for cinema management operations"""

    def __init__(self):
        """Initialize Gemini client with API key and configuration"""
        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Initialize the model with function calling capabilities (Gemini 2.5 Pro)
        self.model = genai.GenerativeModel("gemini-2.5-pro")

        # Store system instruction separately
        self.system_instruction = self._get_system_instruction()

        # Initialize chat session
        self.chat = None

    def _get_system_instruction(self) -> str:
        """Get the system instruction for cinema management context"""
        return """You are SAMi (Schedule Assistant for Movie Intelligence), an AI assistant specialized in cinema schedule management.

Your role is to help cinema managers with:
- Movie scheduling and theater allocation
- Revenue tracking and analytics
- Cinema availability and booking status
- Customer service related to movie schedules

Key capabilities:
1. CINEMA MANAGEMENT: Create, update, and query cinema information including seating capacity, location, and features
2. MOVIE MANAGEMENT: Add new movies, update existing ones, and search movie catalog
3. SCHEDULE MANAGEMENT: Create movie schedules, check availability, update time slots
4. ANALYTICS: Generate revenue reports, analyze booking patterns, track occupancy rates
5. CUSTOMER QUERIES: Answer questions about showtimes, availability, pricing

Guidelines:
- Always use the provided functions to interact with the cinema database
- Provide clear, professional responses suitable for both staff and customers
- When scheduling conflicts occur, suggest alternative solutions
- For revenue queries, include relevant context like time periods and comparisons
- Be proactive in suggesting optimizations for cinema operations
- Handle errors gracefully and provide helpful error messages

Current date and time context will be provided with each query for accurate scheduling decisions."""

    async def process_message(
        self,
        message: str,
        session_id: str,
        available_functions: List[Dict[str, Any]] = None
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
                    {"role": "user", "parts": [{"text": "Hello, I need help with cinema management."}]},
                    {"role": "model", "parts": [{"text": self.system_instruction + "\n\nHello! I'm SAMi, your cinema management AI assistant. How can I help you today?"}]}
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
                response = self._send_with_functions(context_message, available_functions)
            else:
                response = self._send_message(context_message)

            # Extract function calls first
            function_calls = self._extract_function_calls(response)

            # Get response text, handling cases where function calls are present
            try:
                content = response.text if hasattr(response, 'text') and response.text else ""
            except Exception as e:
                # If there are function calls, the response might not have direct text
                if function_calls:
                    content = f"I'm processing your request using {len(function_calls)} function call(s)..."
                else:
                    content = "I received your message but couldn't generate a text response."
                logger.warning(f"Could not extract text from response: {e}")

            return {
                "success": True,
                "content": content,
                "function_calls": function_calls,
                "session_id": session_id
            }

        except Exception as e:
            logger.error(f"Error processing message with Gemini: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.",
                "session_id": session_id
            }

    def _send_with_functions(
        self,
        message: str,
        functions: List[Dict[str, Any]]
    ) -> Any:
        """Send message with function calling enabled"""
        try:
            # Try with a simplified function calling approach
            # Create a single tool with all function declarations
            tool_config = {
                "function_declarations": functions
            }

            response = self.chat.send_message(
                message,
                tools=[tool_config]
            )
            return response
        except Exception as e:
            logger.error(f"Error sending message with functions: {e}")
            # Fallback to regular message without function calling
            logger.info("Falling back to regular message without function calling")
            response = self.chat.send_message(message)
            return response

    def _send_message(self, message: str) -> Any:
        """Send message without function calling"""
        response = self.chat.send_message(message)
        return response

    def _extract_function_calls(self, response: Any) -> List[Dict[str, Any]]:
        """Extract function calls from Gemini response"""
        function_calls = []

        try:
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                function_calls.append({
                                    "name": part.function_call.name,
                                    "args": dict(part.function_call.args) if part.function_call.args else {}
                                })
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
            history.append({
                "role": message.role,
                "content": message.parts[0].text if message.parts else ""
            })

        return history

# Global Gemini client instance
gemini_client = GeminiClient()