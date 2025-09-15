from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.schedule_service import ScheduleService
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedules", tags=["schedules"])

class ScheduleCreate(BaseModel):
    movie_id: str
    cinema_number: int
    time_slot: str  # ISO format datetime string
    price: float
    expected_attendance: Optional[int] = None

class ScheduleUpdate(BaseModel):
    movie_id: Optional[str] = None
    cinema_number: Optional[int] = None
    time_slot: Optional[str] = None
    price: Optional[float] = None
    expected_attendance: Optional[int] = None
    actual_attendance: Optional[int] = None

@router.get("", response_model=List[Dict[str, Any]])
async def get_schedules(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    cinema_number: Optional[int] = Query(None, description="Filter by cinema number"),
    movie_id: Optional[str] = Query(None, description="Filter by movie ID"),
    db: Session = Depends(get_db)
):
    """Get all schedules with optional filtering"""
    try:
        schedule_service = ScheduleService(db)

        if date:
            return await schedule_service.get_schedules_by_date(date)
        else:
            schedules = await schedule_service.get_all_schedules()

            # Apply additional filters
            if cinema_number:
                schedules = [s for s in schedules if s.get("cinema_number") == cinema_number]

            if movie_id:
                schedules = [s for s in schedules if s.get("movie_id") == movie_id]

            return schedules
    except Exception as e:
        logger.error(f"Error getting schedules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{schedule_id}", response_model=Dict[str, Any])
async def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """Get a specific schedule by ID"""
    try:
        schedule_service = ScheduleService(db)
        schedule = await schedule_service.get_schedule_by_id(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return schedule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("", response_model=Dict[str, Any])
async def create_schedule(schedule_data: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new schedule"""
    try:
        schedule_service = ScheduleService(db)

        # Validate time slot format
        try:
            datetime.fromisoformat(schedule_data.time_slot.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time_slot format. Use ISO 8601 format.")

        schedule_dict = schedule_data.dict()
        return await schedule_service.create_schedule(**schedule_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        if "conflict" in str(e).lower():
            raise HTTPException(status_code=409, detail="Schedule conflict detected")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{schedule_id}", response_model=Dict[str, Any])
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing schedule"""
    try:
        schedule_service = ScheduleService(db)

        # Check if schedule exists
        existing_schedule = await schedule_service.get_schedule_by_id(schedule_id)
        if not existing_schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Validate time slot format if provided
        if schedule_data.time_slot:
            try:
                datetime.fromisoformat(schedule_data.time_slot.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid time_slot format. Use ISO 8601 format.")

        # Update with only provided fields
        update_dict = schedule_data.dict(exclude_unset=True)
        return await schedule_service.update_schedule(schedule_id, **update_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating schedule {schedule_id}: {e}")
        if "conflict" in str(e).lower():
            raise HTTPException(status_code=409, detail="Schedule conflict detected")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{schedule_id}")
async def cancel_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """Cancel/delete a schedule"""
    try:
        schedule_service = ScheduleService(db)

        # Check if schedule exists
        existing_schedule = await schedule_service.get_schedule_by_id(schedule_id)
        if not existing_schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        await schedule_service.cancel_schedule(schedule_id)
        return {"message": "Schedule cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/availability/time-slots")
async def get_available_time_slots(
    date: str = Query(..., description="Date to check (YYYY-MM-DD)"),
    cinema_number: Optional[int] = Query(None, description="Specific cinema number"),
    db: Session = Depends(get_db)
):
    """Get available time slots for a specific date and optional cinema"""
    try:
        schedule_service = ScheduleService(db)
        return await schedule_service.get_available_time_slots(date, cinema_number)
    except Exception as e:
        logger.error(f"Error getting available time slots for {date}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conflicts/check")
async def check_schedule_conflicts(
    movie_id: str = Query(..., description="Movie ID"),
    cinema_number: int = Query(..., description="Cinema number"),
    time_slot: str = Query(..., description="Time slot (ISO format)"),
    exclude_schedule_id: Optional[str] = Query(None, description="Schedule ID to exclude from conflict check"),
    db: Session = Depends(get_db)
):
    """Check for scheduling conflicts before creating/updating a schedule"""
    try:
        schedule_service = ScheduleService(db)

        # Validate time slot format
        try:
            datetime.fromisoformat(time_slot.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time_slot format. Use ISO 8601 format.")

        # This would be implemented in the schedule service
        conflicts = await schedule_service.check_conflicts(
            movie_id=movie_id,
            cinema_number=cinema_number,
            time_slot=time_slot,
            exclude_schedule_id=exclude_schedule_id
        )

        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
            "message": "No conflicts found" if len(conflicts) == 0 else f"Found {len(conflicts)} conflict(s)"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking schedule conflicts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cinema/{cinema_number}/schedule")
async def get_cinema_schedule(
    cinema_number: int,
    date: Optional[str] = Query(None, description="Date to filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get schedule for a specific cinema"""
    try:
        schedule_service = ScheduleService(db)

        if date:
            schedules = await schedule_service.get_schedules_by_date(date)
            schedules = [s for s in schedules if s.get("cinema_number") == cinema_number]
        else:
            schedules = await schedule_service.get_all_schedules()
            schedules = [s for s in schedules if s.get("cinema_number") == cinema_number]

        return {
            "cinema_number": cinema_number,
            "date": date or "all",
            "schedules": schedules,
            "total_schedules": len(schedules)
        }
    except Exception as e:
        logger.error(f"Error getting cinema {cinema_number} schedule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")