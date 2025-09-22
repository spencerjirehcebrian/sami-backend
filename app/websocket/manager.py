from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from app.database import get_db
from app.services.chat_persistence_service import ChatPersistenceService
import json
import uuid
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

websocket_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection and store it"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

        # Ensure chat session exists in database
        try:
            db = next(get_db())
            chat_persistence = ChatPersistenceService(db)
            await chat_persistence.ensure_chat_session(session_id)
            logger.info(f"WebSocket connection established for session: {session_id}")
        except Exception as e:
            logger.error(f"Error ensuring chat session {session_id}: {e}")
        finally:
            if "db" in locals():
                db.close()

        logger.info(f"Total active connections: {len(self.active_connections)}")

    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket connection closed for session: {session_id}")
            logger.info(f"Total active connections: {len(self.active_connections)}")

    async def send_message(self, session_id: str, message: str):
        """Send a message to a specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(message)
                logger.info(f"Message sent to session {session_id}: {message[:100]}...")
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                # Remove the connection if it's no longer valid
                self.disconnect(session_id)

    async def broadcast_message(self, message: str, exclude_session: str = None):
        """Send a message to all connected sessions (excluding one if specified)"""
        disconnected_sessions = []

        for session_id, websocket in self.active_connections.items():
            if session_id != exclude_session:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to session {session_id}: {e}")
                    disconnected_sessions.append(session_id)

        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            self.disconnect(session_id)

    async def process_user_message(self, session_id: str, message: str) -> str:
        """
        Process a user message and return a response.
        Uses the message handlers for validation and processing.
        """
        db = None
        try:
            # Import here to avoid circular imports
            from app.websocket.handlers import MessageHandler, message_processor

            # Validate the incoming message
            validated_message = MessageHandler.validate_message(message)

            if not validated_message["valid"]:
                return MessageHandler.create_error_response(
                    f"Invalid message format: {validated_message.get('error', 'Unknown error')}",
                    session_id=session_id,
                )

            logger.info(
                f"Processing {validated_message['type']} message from session {session_id}: {validated_message['content'][:100]}..."
            )

            # Save user message to database
            db = next(get_db())
            chat_persistence = ChatPersistenceService(db)

            await chat_persistence.save_user_message(
                session_id=session_id,
                content=validated_message["content"],
                message_type=validated_message["type"],
                metadata=validated_message.get("metadata"),
            )

            # Process the validated message
            response = await message_processor.process_message(
                validated_message, session_id
            )

            # Parse response to extract content and metadata for saving
            try:
                response_data = json.loads(response)
                await chat_persistence.save_ai_message(
                    session_id=session_id,
                    content=response_data.get("content", ""),
                    message_type=response_data.get("type", "response"),
                    metadata=response_data.get("metadata"),
                )
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                await chat_persistence.save_ai_message(
                    session_id=session_id, content=response, message_type="response"
                )

            return response

        except Exception as e:
            logger.error(f"Error processing message from session {session_id}: {e}")
            # Import here to avoid circular imports
            from app.websocket.handlers import MessageHandler

            return MessageHandler.create_error_response(
                "I apologize, but I encountered an error processing your message. Please try again.",
                session_id=session_id,
                error_code="PROCESSING_ERROR",
            )
        finally:
            if db:
                db.close()

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

    def get_active_sessions(self) -> List[str]:
        """Get a list of active session IDs"""
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()


@websocket_router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for chat communication.
    Each client connects with a unique session_id for message routing.
    """
    await manager.connect(websocket, session_id)

    try:
        # Send welcome message
        welcome_content = f"""Welcome to SAMi Backend AI Assistant!

I'm here to help you with:
• Movie scheduling and management
• Cinema operations and reporting
• Booking assistance and customer service
• Real-time data queries and analytics

Type 'help' for available commands or just chat naturally!"""

        welcome_message = {
            "type": "system",
            "content": welcome_content,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {"system_type": "welcome", "session_established": True},
        }
        await manager.send_message(session_id, json.dumps(welcome_message))

        # Listen for messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            # Process the message and get response
            response = await manager.process_user_message(session_id, data)

            # Send response back to client
            await manager.send_message(session_id, response)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(
            f"Unexpected error in WebSocket connection for session {session_id}: {e}"
        )
        manager.disconnect(session_id)


@websocket_router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": manager.get_connection_count(),
        "active_sessions": manager.get_active_sessions(),
    }
