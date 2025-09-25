from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models.chat import ChatSession, ChatMessage
from datetime import datetime
import logging
import uuid
import hashlib

logger = logging.getLogger(__name__)

class ChatPersistenceService:
    """Service for persisting chat data to database"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def _normalize_session_id(self, session_id: str) -> str:
        """
        Normalize session ID to ensure it's a valid UUID.
        For test sessions or non-UUID strings, generate a deterministic UUID.
        """
        try:
            # Try to parse as UUID first
            uuid.UUID(session_id)
            return session_id
        except ValueError:
            # Not a valid UUID, generate one deterministically from the session_id
            # This ensures same session_id always maps to same UUID
            namespace = uuid.UUID('12345678-1234-5678-1234-567812345678')
            deterministic_uuid = uuid.uuid5(namespace, session_id)
            logger.debug(f"Converted session_id '{session_id}' to UUID: {deterministic_uuid}")
            return str(deterministic_uuid)

    async def ensure_chat_session(self, session_id: str, context: Optional[Dict[str, Any]] = None) -> ChatSession:
        """
        Ensure a chat session exists, create if it doesn't

        Args:
            session_id: WebSocket session identifier
            context: Optional session context data

        Returns:
            ChatSession object
        """
        try:
            # Normalize session ID to ensure it's a valid UUID
            normalized_session_id = self._normalize_session_id(session_id)

            # Try to find existing session
            session = self.db.query(ChatSession).filter(ChatSession.id == normalized_session_id).first()

            if not session:
                # Create new session
                session = ChatSession(
                    id=normalized_session_id,
                    started_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                    context=context
                )
                self.db.add(session)
                self.db.commit()
                self.db.refresh(session)
                logger.info(f"Created new chat session: {session_id} -> {normalized_session_id}")
            else:
                # Update last activity
                session.last_activity = datetime.utcnow()
                if context:
                    session.context = {**(session.context or {}), **context}
                self.db.commit()
                logger.debug(f"Updated existing chat session: {session_id} -> {normalized_session_id}")

            return session

        except SQLAlchemyError as e:
            logger.error(f"Database error ensuring chat session {session_id}: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error ensuring chat session {session_id}: {e}")
            self.db.rollback()
            raise

    async def save_user_message(
        self,
        session_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Save a user message to the database

        Args:
            session_id: Chat session identifier
            content: Message content
            message_type: Type of message (text, command, etc.)
            metadata: Optional message metadata

        Returns:
            ChatMessage object
        """
        try:
            # Normalize session ID
            normalized_session_id = self._normalize_session_id(session_id)

            # Ensure session exists
            await self.ensure_chat_session(session_id)

            # Create user message
            message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=normalized_session_id,
                sender="user",
                content=content,
                message_type=message_type,
                message_metadata=metadata,
                timestamp=datetime.utcnow()
            )

            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            logger.debug(f"Saved user message in session {session_id}: {content[:50]}...")
            return message

        except SQLAlchemyError as e:
            logger.error(f"Database error saving user message in session {session_id}: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving user message in session {session_id}: {e}")
            self.db.rollback()
            raise

    async def save_ai_message(
        self,
        session_id: str,
        content: str,
        message_type: str = "response",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Save an AI response message to the database

        Args:
            session_id: Chat session identifier
            content: AI response content
            message_type: Type of response (response, error, system)
            metadata: Optional response metadata (processing time, function calls, etc.)

        Returns:
            ChatMessage object
        """
        try:
            # Normalize session ID
            normalized_session_id = self._normalize_session_id(session_id)

            # Update session activity
            await self.update_session_activity(session_id)

            # Create AI message
            message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=normalized_session_id,
                sender="ai",
                content=content,
                message_type=message_type,
                message_metadata=metadata,
                timestamp=datetime.utcnow()
            )

            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            logger.debug(f"Saved AI message in session {session_id}: {content[:50]}...")
            return message

        except SQLAlchemyError as e:
            logger.error(f"Database error saving AI message in session {session_id}: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving AI message in session {session_id}: {e}")
            self.db.rollback()
            raise

    async def update_session_activity(self, session_id: str) -> None:
        """
        Update the last activity timestamp for a session

        Args:
            session_id: Chat session identifier
        """
        try:
            # Normalize session ID
            normalized_session_id = self._normalize_session_id(session_id)

            session = self.db.query(ChatSession).filter(ChatSession.id == normalized_session_id).first()
            if session:
                session.last_activity = datetime.utcnow()
                self.db.commit()
                logger.debug(f"Updated activity for session {session_id} -> {normalized_session_id}")
            else:
                logger.warning(f"Attempted to update activity for non-existent session: {session_id} -> {normalized_session_id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error updating session activity {session_id}: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating session activity {session_id}: {e}")
            self.db.rollback()
            raise

    async def get_session_with_messages(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a complete session with all its messages

        Args:
            session_id: Chat session identifier

        Returns:
            Dictionary with session info and messages, or None if not found
        """
        try:
            # Normalize session ID
            normalized_session_id = self._normalize_session_id(session_id)

            session = self.db.query(ChatSession).filter(ChatSession.id == normalized_session_id).first()
            if not session:
                return None

            messages = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == normalized_session_id)
                .order_by(ChatMessage.timestamp)
                .all()
            )

            return {
                "session": {
                    "id": str(session.id),
                    "started_at": session.started_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "context": session.context
                },
                "messages": [
                    {
                        "id": str(message.id),
                        "sender": message.sender,
                        "content": message.content,
                        "message_type": message.message_type,
                        "message_metadata": message.message_metadata,
                        "timestamp": message.timestamp.isoformat()
                    }
                    for message in messages
                ]
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error getting session with messages {session_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting session with messages {session_id}: {e}")
            raise

    def close(self):
        """Close the database session"""
        if self.db:
            self.db.close()