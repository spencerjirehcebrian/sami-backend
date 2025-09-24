import asyncio
import logging
from typing import Dict, Any, Optional
from app.notifications.broadcaster import broadcaster

logger = logging.getLogger(__name__)

class NotificationHandler:
    """Handle notification processing and routing"""

    @staticmethod
    async def handle_entity_change(
        entity_type: str,
        operation: str,
        entity_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Handle entity change notifications

        Args:
            entity_type: Type of entity that changed
            operation: Operation performed (create, update, delete)
            entity_id: ID of the entity
            data: Additional data about the change
        """
        try:
            await broadcaster.broadcast_change(
                entity_type=entity_type,
                operation=operation,
                entity_id=entity_id,
                data=data
            )

            # Log the notification for debugging
            logger.info(f"Handled {entity_type} {operation} notification for entity {entity_id}")

        except Exception as e:
            logger.error(f"Error handling entity change notification: {e}")

    @staticmethod
    async def handle_cache_invalidation(entity_type: str, entity_id: Optional[str] = None):
        """
        Handle cache invalidation notifications

        Args:
            entity_type: Type of entity that needs cache invalidation
            entity_id: Specific entity ID or None for all
        """
        try:
            cache_notification = {
                "action": "invalidate_cache",
                "entity_type": entity_type,
                "entity_id": entity_id
            }

            await broadcaster.broadcast_change(
                entity_type=entity_type,
                operation="cache_invalidate",
                entity_id=entity_id,
                data=cache_notification
            )

            logger.info(f"Handled cache invalidation for {entity_type} entity {entity_id}")

        except Exception as e:
            logger.error(f"Error handling cache invalidation: {e}")


    @staticmethod
    async def handle_system_notification(message: str, message_type: str = "info"):
        """
        Handle system-wide notifications

        Args:
            message: System message content
            message_type: Type of message (info, warning, error)
        """
        try:
            await broadcaster.broadcast_system_message(message, message_type)
            logger.info(f"Handled system notification: {message}")

        except Exception as e:
            logger.error(f"Error handling system notification: {e}")

# Global notification handler instance
notification_handler = NotificationHandler()