import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class MessageHandler:
    """Handles processing and validation of WebSocket messages"""

    @staticmethod
    def validate_message(message: str) -> Dict[str, Any]:
        """
        Validate and parse incoming WebSocket messages.

        Expected message format:
        {
            "type": "chat" | "command" | "ping",
            "content": "message content",
            "metadata": {...} // optional
        }
        """
        try:
            # Try to parse as JSON
            parsed = json.loads(message)

            # Validate required fields
            if not isinstance(parsed, dict):
                raise ValueError("Message must be a JSON object")

            message_type = parsed.get("type", "chat")
            content = parsed.get("content", "")

            if not content and message_type != "ping":
                raise ValueError("Message content cannot be empty")

            return {
                "valid": True,
                "type": message_type,
                "content": content,
                "metadata": parsed.get("metadata", {}),
                "original": parsed
            }

        except json.JSONDecodeError:
            # If not JSON, treat as plain text chat message
            return {
                "valid": True,
                "type": "chat",
                "content": message.strip(),
                "metadata": {},
                "original": {"type": "chat", "content": message.strip()}
            }

        except Exception as e:
            logger.error(f"Message validation error: {e}")
            return {
                "valid": False,
                "error": str(e),
                "content": message
            }

    @staticmethod
    def create_response(
        content: str,
        message_type: str = "response",
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Create a standardized response message.

        Response format:
        {
            "type": "response" | "error" | "system" | "typing",
            "content": "response content",
            "session_id": "session_id",
            "timestamp": "2023-...",
            "metadata": {...}
        }
        """
        response = {
            "type": message_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        if session_id:
            response["session_id"] = session_id

        if metadata:
            response["metadata"] = metadata

        return json.dumps(response, ensure_ascii=False)

    @staticmethod
    def create_error_response(
        error_message: str,
        session_id: str = None,
        error_code: str = None
    ) -> str:
        """Create an error response message"""
        metadata = {}
        if error_code:
            metadata["error_code"] = error_code

        return MessageHandler.create_response(
            content=error_message,
            message_type="error",
            session_id=session_id,
            metadata=metadata
        )

    @staticmethod
    def create_system_response(
        message: str,
        session_id: str = None,
        system_type: str = "info"
    ) -> str:
        """Create a system message response"""
        return MessageHandler.create_response(
            content=message,
            message_type="system",
            session_id=session_id,
            metadata={"system_type": system_type}
        )

    @staticmethod
    def create_typing_indicator(session_id: str = None, is_typing: bool = True) -> str:
        """Create a typing indicator message"""
        return MessageHandler.create_response(
            content="",
            message_type="typing",
            session_id=session_id,
            metadata={"is_typing": is_typing}
        )

class ChatMessageProcessor:
    """Processes different types of chat messages"""

    def __init__(self):
        self.command_handlers = {
            "help": self._handle_help_command,
            "status": self._handle_status_command,
            "clear": self._handle_clear_command,
        }

    async def process_message(
        self,
        validated_message: Dict[str, Any],
        session_id: str
    ) -> str:
        """
        Process a validated message and return appropriate response.
        This will be enhanced in Phase 3 with Gemini AI integration.
        """
        message_type = validated_message["type"]
        content = validated_message["content"]

        try:
            if message_type == "ping":
                return MessageHandler.create_response(
                    content="pong",
                    message_type="pong",
                    session_id=session_id
                )

            elif message_type == "command":
                return await self._handle_command(content, session_id)

            elif message_type == "chat":
                return await self._handle_chat_message(content, session_id)

            else:
                return MessageHandler.create_error_response(
                    f"Unknown message type: {message_type}",
                    session_id=session_id,
                    error_code="UNKNOWN_MESSAGE_TYPE"
                )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return MessageHandler.create_error_response(
                "An error occurred while processing your message.",
                session_id=session_id,
                error_code="PROCESSING_ERROR"
            )

    async def _handle_command(self, command: str, session_id: str) -> str:
        """Handle command messages"""
        command_parts = command.lower().split()
        if not command_parts:
            return MessageHandler.create_error_response(
                "Empty command",
                session_id=session_id
            )

        command_name = command_parts[0]

        if command_name in self.command_handlers:
            return await self.command_handlers[command_name](command_parts[1:], session_id)
        else:
            return MessageHandler.create_error_response(
                f"Unknown command: {command_name}. Type 'help' for available commands.",
                session_id=session_id
            )

    async def _handle_chat_message(self, content: str, session_id: str) -> str:
        """
        Handle regular chat messages.
        Currently returns an echo, but will be replaced with Gemini AI in Phase 3.
        """
        # Simple echo for now - this will be replaced with Gemini processing
        echo_content = f"Echo: {content}"

        return MessageHandler.create_response(
            content=echo_content,
            session_id=session_id,
            metadata={
                "processing_time": "0.001s",
                "handler": "echo"
            }
        )

    async def _handle_help_command(self, args: list, session_id: str) -> str:
        """Handle help command"""
        help_text = """
Available commands:
• help - Show this help message
• status - Show connection status
• clear - Clear chat history

For cinema management, try natural language like:
• "Schedule a movie for tonight"
• "Show me today's revenue"
• "What cinemas are available?"

(AI features will be available in Phase 3)
        """.strip()

        return MessageHandler.create_system_response(
            help_text,
            session_id=session_id,
            system_type="help"
        )

    async def _handle_status_command(self, args: list, session_id: str) -> str:
        """Handle status command"""
        status_text = f"""
System Status:
• Session ID: {session_id}
• Status: Connected
• Backend: FastAPI + WebSocket
• Phase: 2 (Core Setup) - Echo Mode
• AI Integration: Coming in Phase 3
        """.strip()

        return MessageHandler.create_system_response(
            status_text,
            session_id=session_id,
            system_type="status"
        )

    async def _handle_clear_command(self, args: list, session_id: str) -> str:
        """Handle clear command"""
        return MessageHandler.create_system_response(
            "Chat history cleared.",
            session_id=session_id,
            system_type="clear"
        )

# Global message processor instance
message_processor = ChatMessageProcessor()