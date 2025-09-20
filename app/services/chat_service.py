from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.database import get_db
from app.models.chat import ChatSession, ChatMessage
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChatService:
    """Service class for chat history management operations"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def get_chat_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get chat history with optional filtering and pagination

        Args:
            session_id: Filter by specific session ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip for pagination
            start_date: Filter messages after this date
            end_date: Filter messages before this date

        Returns:
            Dictionary containing messages, session info, and pagination metadata
        """
        try:
            query = self.db.query(ChatMessage).join(ChatSession)

            # Apply filters
            if session_id:
                query = query.filter(ChatMessage.session_id == session_id)

            if start_date:
                query = query.filter(ChatMessage.timestamp >= start_date)

            if end_date:
                query = query.filter(ChatMessage.timestamp <= end_date)

            # Get total count for pagination
            total_count = query.count()

            # Apply pagination and ordering
            messages = (
                query.order_by(desc(ChatMessage.timestamp))
                .offset(offset)
                .limit(limit)
                .all()
            )

            # Convert to response format
            message_list = []
            for message in messages:
                message_list.append({
                    "id": str(message.id),
                    "session_id": str(message.session_id),
                    "sender": message.sender,
                    "content": message.content,
                    "message_type": message.message_type,
                    "message_metadata": message.message_metadata,
                    "timestamp": message.timestamp.isoformat()
                })

            # Get session information if filtering by session_id
            session_info = None
            if session_id and messages:
                session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
                if session:
                    session_info = {
                        "id": str(session.id),
                        "started_at": session.started_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "context": session.context
                    }

            return {
                "messages": message_list,
                "session": session_info,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count
                }
            }

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            raise

    async def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete history for a specific session"""
        try:
            session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                return None

            messages = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
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

        except Exception as e:
            logger.error(f"Error getting session history for {session_id}: {e}")
            raise

    async def get_all_sessions(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get all chat sessions with pagination"""
        try:
            query = self.db.query(ChatSession)
            total_count = query.count()

            sessions = (
                query.order_by(desc(ChatSession.last_activity))
                .offset(offset)
                .limit(limit)
                .all()
            )

            session_list = []
            for session in sessions:
                # Get message count for each session
                message_count = (
                    self.db.query(ChatMessage)
                    .filter(ChatMessage.session_id == session.id)
                    .count()
                )

                session_list.append({
                    "id": str(session.id),
                    "started_at": session.started_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "context": session.context,
                    "message_count": message_count
                })

            return {
                "sessions": session_list,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count
                }
            }

        except Exception as e:
            logger.error(f"Error getting all sessions: {e}")
            raise