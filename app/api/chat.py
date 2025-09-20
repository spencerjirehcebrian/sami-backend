from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.chat_service import ChatService
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.get("/history", response_model=Dict[str, Any])
async def get_chat_history(
    session_id: Optional[str] = Query(None, description="Filter by specific session ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return (1-100)"),
    offset: int = Query(0, ge=0, description="Number of messages to skip for pagination"),
    start_date: Optional[str] = Query(None, description="Filter messages after this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter messages before this date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Get chat history with optional filtering and pagination

    Returns messages ordered by timestamp (newest first) with pagination metadata.
    If session_id is provided, also includes session information.
    """
    try:
        chat_service = ChatService(db)

        # Parse date parameters if provided
        parsed_start_date = None
        parsed_end_date = None

        if start_date:
            try:
                parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use ISO format (e.g., 2023-12-01T00:00:00Z)"
                )

        if end_date:
            try:
                parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use ISO format (e.g., 2023-12-01T23:59:59Z)"
                )

        # Validate date range
        if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be after end_date"
            )

        return await chat_service.get_chat_history(
            session_id=session_id,
            limit=limit,
            offset=offset,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions", response_model=Dict[str, Any])
async def get_chat_sessions(
    limit: int = Query(20, ge=1, le=50, description="Number of sessions to return (1-50)"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get all chat sessions with pagination

    Returns sessions ordered by last activity (newest first) with message counts.
    """
    try:
        chat_service = ChatService(db)
        return await chat_service.get_all_sessions(limit=limit, offset=offset)

    except Exception as e:
        logger.error(f"Error getting chat sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete chat history for a specific session

    Returns all messages for the session ordered chronologically.
    """
    try:
        chat_service = ChatService(db)
        session_data = await chat_service.get_session_history(session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        return session_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session history for {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")