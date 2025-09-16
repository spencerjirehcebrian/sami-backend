from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.schedule_service import ScheduleService
from app.exceptions import ValidationError, BusinessLogicError, ResourceNotFoundError, ConflictError
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

@router.get("", response_model=Dict[str, Any])
async def get_schedules(
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD) - legacy parameter"),
    cinema_id: Optional[str] = Query(None, description="Filter by cinema ID"),
    cinema_number: Optional[int] = Query(None, description="Filter by cinema number"),
    movie_id: Optional[str] = Query(None, description="Filter by movie ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return (1-1000)"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    page: Optional[int] = Query(None, ge=1, description="Page number (alternative to offset)"),
    require_date_filter: bool = Query(True, description="Require date filter for large queries"),
    db: Session = Depends(get_db)
):
    """Get all schedules with optional filtering, pagination, and safety guards"""
    try:
        schedule_service = ScheduleService(db)

        # Handle legacy date parameter
        if date and not date_from and not date_to:
            # Convert single date to date range for that day
            try:
                target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
                date_from = datetime.combine(target_date, datetime.min.time()).isoformat()
                date_to = datetime.combine(target_date, datetime.max.time()).isoformat()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or ISO format.")

        # Convert page to offset if provided
        if page is not None:
            offset = (page - 1) * limit

        # Find cinema_id from cinema_number if provided
        actual_cinema_id = cinema_id
        if cinema_number and not cinema_id:
            from app.models.cinema import Cinema
            cinema = db.query(Cinema).filter(Cinema.number == cinema_number).first()
            if cinema:
                actual_cinema_id = str(cinema.id)

        return await schedule_service.get_all_schedules(
            date_from=date_from,
            date_to=date_to,
            cinema_id=actual_cinema_id,
            movie_id=movie_id,
            limit=limit,
            offset=offset,
            require_date_filter=require_date_filter
        )
    except ValidationError as e:
        logger.warning(f"Validation error in get_schedules: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        # Handle legacy ValueError exceptions as validation errors
        logger.warning(f"Validation error in get_schedules: {e}")
        error_msg = str(e)

        # Provide helpful error messages for common validation issues
        if "Date filter" in error_msg and "required" in error_msg:
            detail = "Date filter is required. Please provide either 'date_from', 'date_to', or 'date' parameter."
        elif "Date range cannot exceed" in error_msg:
            detail = "Date range is too large. Maximum allowed range is 6 months (180 days)."
        elif "Invalid date" in error_msg and "format" in error_msg:
            detail = "Invalid date format. Please use ISO 8601 format (YYYY-MM-DDTHH:MM:SS) or YYYY-MM-DD for date-only."
        elif "Limit must be between" in error_msg:
            detail = "Invalid limit parameter. Must be between 1 and 1000."
        elif "Offset must be non-negative" in error_msg:
            detail = "Invalid offset parameter. Must be 0 or greater."
        else:
            detail = f"Validation error: {error_msg}"

        raise HTTPException(status_code=400, detail=detail)
    except BusinessLogicError as e:
        logger.warning(f"Business logic error in get_schedules: {e.message}")
        raise HTTPException(status_code=422, detail=e.message)
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in get_schedules: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error getting schedules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/summary", response_model=List[Dict[str, Any]])
async def get_schedules_summary(
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    cinema_id: Optional[str] = Query(None, description="Filter by cinema ID"),
    movie_id: Optional[str] = Query(None, description="Filter by movie ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return (1-1000)"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    """Get schedule summaries with minimal data - optimized for list views"""
    try:
        schedule_service = ScheduleService(db)

        return schedule_service.get_schedules_summary(
            date_from=date_from,
            date_to=date_to,
            cinema_id=cinema_id,
            movie_id=movie_id,
            limit=limit,
            offset=offset
        )
    except ValidationError as e:
        logger.warning(f"Validation error in get_schedules_summary: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in get_schedules_summary: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting schedule summaries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/export", response_model=List[Dict[str, Any]])
async def get_schedules_for_export(
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    cinema_id: Optional[str] = Query(None, description="Filter by cinema ID"),
    movie_id: Optional[str] = Query(None, description="Filter by movie ID"),
    db: Session = Depends(get_db)
):
    """Get schedules formatted for export - includes all necessary fields"""
    try:
        schedule_service = ScheduleService(db)

        return schedule_service.get_schedules_for_export(
            date_from=date_from,
            date_to=date_to,
            cinema_id=cinema_id,
            movie_id=movie_id
        )
    except ValidationError as e:
        logger.warning(f"Validation error in get_schedules_for_export: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in get_schedules_for_export: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting schedules for export: {e}")
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
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in get_schedule: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error in get_schedule: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in get_schedule: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid schedule ID format: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting schedule {schedule_id}: {e}")
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
    except ConflictError as e:
        logger.warning(f"Schedule conflict in create_schedule: {e.message}")
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error in create_schedule: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in create_schedule: {e}")
        error_msg = str(e)
        if "conflict" in error_msg.lower():
            raise HTTPException(status_code=409, detail=f"Schedule conflict: {error_msg}")
        elif "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=f"Validation error: {error_msg}")
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in create_schedule: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error creating schedule: {e}")
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
    except ConflictError as e:
        logger.warning(f"Schedule conflict in update_schedule: {e.message}")
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error in update_schedule: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in update_schedule: {e}")
        error_msg = str(e)
        if "conflict" in error_msg.lower():
            raise HTTPException(status_code=409, detail=f"Schedule conflict: {error_msg}")
        elif "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=f"Validation error: {error_msg}")
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in update_schedule: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error updating schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{schedule_id}")
async def cancel_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """Cancel/delete a schedule"""
    try:
        schedule_service = ScheduleService(db)

        # Check if schedule exists (optimized existence check)
        if not schedule_service.schedule_exists_by_id(schedule_id):
            raise HTTPException(status_code=404, detail="Schedule not found")

        await schedule_service.cancel_schedule(schedule_id)
        return {"message": "Schedule cancelled successfully"}
    except HTTPException:
        raise
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in cancel_schedule: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error in cancel_schedule: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in cancel_schedule: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error cancelling schedule {schedule_id}: {e}")
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
    except ValidationError as e:
        logger.warning(f"Validation error in get_available_time_slots: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in get_available_time_slots: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting available time slots for {date}: {e}")
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
    except ValidationError as e:
        logger.warning(f"Validation error in check_schedule_conflicts: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in check_schedule_conflicts: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error checking schedule conflicts: {e}")
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
            # Use the new paginated API with date filter disabled for backward compatibility
            result = await schedule_service.get_all_schedules(require_date_filter=False)
            schedules = [s for s in result["data"] if s.get("cinema_number") == cinema_number]

        return {
            "cinema_number": cinema_number,
            "date": date or "all",
            "schedules": schedules,
            "total_schedules": len(schedules)
        }
    except ValidationError as e:
        logger.warning(f"Validation error in get_cinema_schedule: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in get_cinema_schedule: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting cinema {cinema_number} schedule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")