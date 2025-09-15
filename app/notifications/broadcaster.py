from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationBroadcaster:
    """Handles broadcasting database change notifications to connected WebSocket clients"""

    def __init__(self):
        self.subscribers: Dict[str, List[str]] = {
            "movies": [],
            "cinemas": [],
            "schedules": [],
            "analytics": []
        }

    async def broadcast_change(
        self,
        entity_type: str,
        operation: str,
        entity_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Broadcast database change to all connected clients

        Args:
            entity_type: Type of entity (movies, cinemas, schedules, analytics)
            operation: Type of operation (create, update, delete)
            entity_id: ID of the affected entity
            data: Additional data about the change
        """
        try:
            # Import here to avoid circular imports
            from app.websocket.manager import manager

            notification = {
                "type": "db_change",
                "entity_type": entity_type,
                "operation": operation,
                "entity_id": entity_id,
                "data": data or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            message = json.dumps(notification)
            await manager.broadcast_message(message)

            logger.info(f"Broadcasted {entity_type} {operation} notification for entity {entity_id}")

        except Exception as e:
            logger.error(f"Error broadcasting notification: {e}")

    async def broadcast_system_message(self, message: str, message_type: str = "info"):
        """
        Broadcast a system message to all connected clients

        Args:
            message: The message content
            message_type: Type of message (info, warning, error)
        """
        try:
            # Import here to avoid circular imports
            from app.websocket.manager import manager

            notification = {
                "type": "system_message",
                "message_type": message_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }

            json_message = json.dumps(notification)
            await manager.broadcast_message(json_message)

            logger.info(f"Broadcasted system message: {message}")

        except Exception as e:
            logger.error(f"Error broadcasting system message: {e}")

    async def subscribe_to_entity(self, session_id: str, entity_type: str):
        """
        Subscribe a session to specific entity changes

        Args:
            session_id: WebSocket session ID
            entity_type: Type of entity to subscribe to
        """
        if entity_type in self.subscribers:
            if session_id not in self.subscribers[entity_type]:
                self.subscribers[entity_type].append(session_id)
                logger.info(f"Session {session_id} subscribed to {entity_type} changes")

    async def unsubscribe_from_entity(self, session_id: str, entity_type: str):
        """
        Unsubscribe a session from entity changes

        Args:
            session_id: WebSocket session ID
            entity_type: Type of entity to unsubscribe from
        """
        if entity_type in self.subscribers:
            if session_id in self.subscribers[entity_type]:
                self.subscribers[entity_type].remove(session_id)
                logger.info(f"Session {session_id} unsubscribed from {entity_type} changes")

    async def unsubscribe_session(self, session_id: str):
        """
        Unsubscribe a session from all entity changes (e.g., when disconnecting)

        Args:
            session_id: WebSocket session ID
        """
        for entity_type in self.subscribers:
            if session_id in self.subscribers[entity_type]:
                self.subscribers[entity_type].remove(session_id)

        logger.info(f"Session {session_id} unsubscribed from all notifications")

    async def get_subscription_status(self, session_id: str) -> Dict[str, bool]:
        """
        Get subscription status for a session

        Args:
            session_id: WebSocket session ID

        Returns:
            Dictionary showing subscription status for each entity type
        """
        return {
            entity_type: session_id in subscribers
            for entity_type, subscribers in self.subscribers.items()
        }

    def get_subscriber_count(self, entity_type: Optional[str] = None) -> Dict[str, int]:
        """
        Get number of subscribers for entity types

        Args:
            entity_type: Specific entity type, or None for all

        Returns:
            Dictionary with subscriber counts
        """
        if entity_type:
            return {entity_type: len(self.subscribers.get(entity_type, []))}
        else:
            return {
                entity_type: len(subscribers)
                for entity_type, subscribers in self.subscribers.items()
            }

# Global broadcaster instance
broadcaster = NotificationBroadcaster()