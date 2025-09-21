from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.chat_persistence_service import ChatPersistenceService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.get("/history/{session_id}", response_model=Dict[str, Any])
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete chat history for a specific session

    Returns all messages for the session ordered chronologically with session metadata.
    """
    try:
        chat_persistence = ChatPersistenceService(db)
        session_data = await chat_persistence.get_session_with_messages(session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Chat session not found")

        return session_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")