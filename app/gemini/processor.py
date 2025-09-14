"""
Gemini AI processor for cinema management
Coordinates between client, function schemas, and executor
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.gemini.client import gemini_client
from app.gemini.function_schemas import ALL_FUNCTIONS, get_functions_by_category
from app.gemini.function_executor import function_executor

logger = logging.getLogger(__name__)

class GeminiProcessor:
    """Main processor for Gemini AI interactions"""

    def __init__(self):
        self.client = gemini_client
        self.executor = function_executor

    async def process_chat_message(
        self,
        message: str,
        session_id: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message using Gemini AI with function calling

        Args:
            message: User's natural language message
            session_id: WebSocket session identifier
            context: Additional context information

        Returns:
            Dict containing response and execution results
        """
        try:
            # Add current datetime context to help with scheduling
            enhanced_message = self._add_context(message, context)

            # Process message with Gemini
            gemini_response = await self.client.process_message(
                message=enhanced_message,
                session_id=session_id,
                available_functions=ALL_FUNCTIONS
            )

            if not gemini_response["success"]:
                return {
                    "success": False,
                    "error": gemini_response.get("error", "Unknown error"),
                    "content": gemini_response["content"],
                    "session_id": session_id
                }

            # Execute any function calls made by Gemini
            function_results = []
            if gemini_response.get("function_calls"):
                execution_results = await self.executor.execute_multiple_functions(
                    gemini_response["function_calls"]
                )

                # Process execution results
                for result in execution_results:
                    if result["success"]:
                        function_results.append(result["result"])
                    else:
                        # Log error but continue processing
                        logger.error(f"Function execution failed: {result['error']}")
                        function_results.append({
                            "error": result["error"],
                            "function": result["function_name"]
                        })

            # Format the final response
            response_content = self._format_response(
                gemini_response["content"],
                function_results,
                gemini_response.get("function_calls", [])
            )

            return {
                "success": True,
                "content": response_content,
                "function_calls_made": len(gemini_response.get("function_calls", [])),
                "function_results": function_results,
                "session_id": session_id,
                "processing_time": self._calculate_processing_time(),
                "handler": "gemini_ai"
            }

        except Exception as e:
            logger.error(f"Error processing chat message with Gemini: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "I apologize, but I encountered an error processing your request. Please try rephrasing your question or contact support if the issue persists.",
                "session_id": session_id
            }

    def _add_context(self, message: str, context: Dict[str, Any] = None) -> str:
        """Add contextual information to the message"""
        current_time = datetime.now()

        context_info = f"""
Current Date/Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Current Day: {current_time.strftime('%A')}
"""

        if context:
            if context.get("user_location"):
                context_info += f"User Location: {context['user_location']}\n"
            if context.get("preferred_cinema"):
                context_info += f"Preferred Cinema: {context['preferred_cinema']}\n"

        return f"{context_info}\nUser Request: {message}"

    def _format_response(
        self,
        gemini_content: str,
        function_results: List[Any],
        function_calls: List[Dict[str, Any]]
    ) -> str:
        """Format the final response combining Gemini's response with function results"""
        if not function_calls:
            return gemini_content

        # If functions were called, Gemini's response should already incorporate the results
        # But we can add additional formatting if needed
        formatted_response = gemini_content

        # Add execution summary if multiple functions were called
        if len(function_calls) > 1:
            formatted_response += f"\n\n📊 Processed {len(function_calls)} operations for your request."

        return formatted_response

    def _calculate_processing_time(self) -> str:
        """Calculate and format processing time (placeholder)"""
        # This is a simple placeholder - in a real implementation,
        # you'd track actual start/end times
        return "~0.5s"

    async def handle_command_message(
        self,
        command: str,
        args: List[str],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Handle special command messages that bypass AI processing

        Args:
            command: Command name (help, status, etc.)
            args: Command arguments
            session_id: WebSocket session identifier

        Returns:
            Dict containing command response
        """
        try:
            if command == "functions":
                # List available functions
                functions = self.executor.get_available_functions()
                content = "Available AI Functions:\n\n"

                # Group functions by category
                categories = {
                    "Cinema Management": [f for f in functions if f.startswith(("get_cinema", "create_cinema", "update_cinema"))],
                    "Movie Management": [f for f in functions if f.startswith(("get_movie", "search_movie", "create_movie", "update_movie"))],
                    "Schedule Management": [f for f in functions if f.startswith(("get_schedule", "create_schedule", "update_schedule", "cancel_schedule", "get_available"))],
                    "Analytics & Reports": [f for f in functions if f.startswith(("get_revenue", "get_occupancy", "get_movie_performance", "get_daily"))]
                }

                for category, funcs in categories.items():
                    if funcs:
                        content += f"**{category}:**\n"
                        for func in sorted(funcs):
                            content += f"  • {func}\n"
                        content += "\n"

                content += "💡 You can use natural language to access these functions!"

                return {
                    "success": True,
                    "content": content,
                    "session_id": session_id,
                    "handler": "command"
                }

            elif command == "reset":
                # Reset Gemini chat session
                self.client.reset_chat()
                return {
                    "success": True,
                    "content": "🔄 AI chat session has been reset. Starting fresh!",
                    "session_id": session_id,
                    "handler": "command"
                }

            elif command == "history":
                # Get chat history
                history = self.client.get_chat_history()
                if not history:
                    content = "No chat history available."
                else:
                    content = "Recent Chat History:\n\n"
                    for i, msg in enumerate(history[-5:], 1):  # Show last 5 messages
                        role_icon = "🤖" if msg["role"] == "model" else "👤"
                        content += f"{i}. {role_icon} {msg['content'][:100]}...\n"

                return {
                    "success": True,
                    "content": content,
                    "session_id": session_id,
                    "handler": "command"
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "content": f"Unknown command '{command}'. Try 'help', 'functions', 'reset', or 'history'.",
                    "session_id": session_id
                }

        except Exception as e:
            logger.error(f"Error handling command {command}: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Error executing command '{command}'. Please try again.",
                "session_id": session_id
            }

    async def get_system_status(self, session_id: str) -> Dict[str, Any]:
        """Get system status information"""
        try:
            return {
                "success": True,
                "content": f"""
🤖 SAMi AI System Status

Session ID: {session_id}
Status: ✅ Connected and Ready
AI Model: Google Gemini 1.5 Pro
Phase: 3 (AI Integration Complete)

Available Functions: {len(self.executor.get_available_functions())}
• Cinema Management: ✅ Active
• Movie Management: ✅ Active
• Schedule Management: ✅ Active
• Analytics & Reports: ✅ Active

💡 Try asking me:
"Show me today's schedules"
"What's our revenue this week?"
"Schedule Avatar for Cinema 1 tonight at 8pm"
"Which movies are most popular?"
                """.strip(),
                "session_id": session_id,
                "handler": "system"
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "Unable to retrieve system status.",
                "session_id": session_id
            }

# Global Gemini processor instance
gemini_processor = GeminiProcessor()