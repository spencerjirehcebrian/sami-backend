from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.cinema_service import CinemaService
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cinemas", tags=["cinemas"])

class CinemaCreate(BaseModel):
    number: int
    type_id: str
    total_seats: int
    location: Optional[str] = None
    features: Optional[str] = None

class CinemaUpdate(BaseModel):
    number: Optional[int] = None
    type_id: Optional[str] = None
    total_seats: Optional[int] = None
    location: Optional[str] = None
    features: Optional[str] = None

@router.get("/", response_model=List[Dict[str, Any]])
async def get_cinemas(
    cinema_type: Optional[str] = Query(None, description="Filter by cinema type"),
    available_only: Optional[bool] = Query(False, description="Show only available cinemas"),
    db: Session = Depends(get_db)
):
    """Get all cinemas with optional filtering"""
    try:
        cinema_service = CinemaService(db)

        if available_only:
            return await cinema_service.get_available_cinemas()
        else:
            cinemas = await cinema_service.get_all_cinemas()

            # Filter by type if specified
            if cinema_type:
                cinemas = [cinema for cinema in cinemas if cinema.get("type_name", "").lower() == cinema_type.lower()]

            return cinemas
    except Exception as e:
        logger.error(f"Error getting cinemas: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/types", response_model=List[Dict[str, Any]])
async def get_cinema_types(db: Session = Depends(get_db)):
    """Get all available cinema types"""
    try:
        cinema_service = CinemaService(db)
        return await cinema_service.get_cinema_types()
    except Exception as e:
        logger.error(f"Error getting cinema types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{cinema_number}", response_model=Dict[str, Any])
async def get_cinema(cinema_number: int, db: Session = Depends(get_db)):
    """Get a specific cinema by number"""
    try:
        cinema_service = CinemaService(db)
        cinema = await cinema_service.get_cinema_by_number(cinema_number)
        if not cinema:
            raise HTTPException(status_code=404, detail="Cinema not found")
        return cinema
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cinema {cinema_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=Dict[str, Any])
async def create_cinema(cinema_data: CinemaCreate, db: Session = Depends(get_db)):
    """Create a new cinema"""
    try:
        cinema_service = CinemaService(db)

        # Check if cinema number already exists
        existing_cinema = await cinema_service.get_cinema_by_number(cinema_data.number)
        if existing_cinema:
            raise HTTPException(status_code=400, detail="Cinema number already exists")

        cinema_dict = cinema_data.dict()
        return await cinema_service.create_cinema(**cinema_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating cinema: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{cinema_number}", response_model=Dict[str, Any])
async def update_cinema(
    cinema_number: int,
    cinema_data: CinemaUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing cinema"""
    try:
        cinema_service = CinemaService(db)

        # Check if cinema exists
        existing_cinema = await cinema_service.get_cinema_by_number(cinema_number)
        if not existing_cinema:
            raise HTTPException(status_code=404, detail="Cinema not found")

        # If updating number, check that new number doesn't exist
        if cinema_data.number and cinema_data.number != cinema_number:
            number_exists = await cinema_service.get_cinema_by_number(cinema_data.number)
            if number_exists:
                raise HTTPException(status_code=400, detail="Cinema number already exists")

        # Update with only provided fields
        update_dict = cinema_data.dict(exclude_unset=True)
        return await cinema_service.update_cinema(cinema_number, **update_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cinema {cinema_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{cinema_number}")
async def delete_cinema(cinema_number: int, db: Session = Depends(get_db)):
    """Delete a cinema"""
    try:
        cinema_service = CinemaService(db)

        # Check if cinema exists
        existing_cinema = await cinema_service.get_cinema_by_number(cinema_number)
        if not existing_cinema:
            raise HTTPException(status_code=404, detail="Cinema not found")

        await cinema_service.delete_cinema(cinema_number)
        return {"message": "Cinema deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cinema {cinema_number}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{cinema_number}/availability")
async def get_cinema_availability(
    cinema_number: int,
    date: Optional[str] = Query(None, description="Date to check (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get cinema availability for a specific date"""
    try:
        cinema_service = CinemaService(db)

        # Check if cinema exists
        existing_cinema = await cinema_service.get_cinema_by_number(cinema_number)
        if not existing_cinema:
            raise HTTPException(status_code=404, detail="Cinema not found")

        # Get availability (this would integrate with schedule service)
        availability = {
            "cinema_number": cinema_number,
            "date": date or "today",
            "available": True,  # This would be calculated based on schedules
            "message": "Cinema availability check - integrate with schedule service"
        }

        return availability
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking cinema {cinema_number} availability: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")