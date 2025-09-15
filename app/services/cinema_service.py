from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.models.cinema import Cinema, CinemaType
from app.notifications.broadcaster import broadcaster
import logging

logger = logging.getLogger(__name__)

class CinemaService:
    """Service class for cinema management operations"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def get_all_cinemas(self) -> List[Dict[str, Any]]:
        """Get all cinemas with their details"""
        try:
            cinemas = self.db.query(Cinema).join(CinemaType).all()
            return [
                {
                    "id": str(cinema.id),
                    "number": cinema.number,
                    "type": cinema.cinema_type.name,
                    "type_description": cinema.cinema_type.description,
                    "total_seats": cinema.total_seats,
                    "location": cinema.location,
                    "features": cinema.features or [],
                    "price_multiplier": cinema.cinema_type.price_multiplier,
                    "created_at": cinema.created_at.isoformat(),
                    "updated_at": cinema.updated_at.isoformat()
                }
                for cinema in cinemas
            ]
        except Exception as e:
            logger.error(f"Error getting all cinemas: {e}")
            raise

    async def get_cinema_by_id(self, cinema_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific cinema by ID"""
        try:
            cinema = self.db.query(Cinema).join(CinemaType).filter(Cinema.id == cinema_id).first()
            if not cinema:
                return None

            return {
                "id": str(cinema.id),
                "number": cinema.number,
                "type": cinema.cinema_type.name,
                "type_description": cinema.cinema_type.description,
                "total_seats": cinema.total_seats,
                "location": cinema.location,
                "features": cinema.features or [],
                "price_multiplier": cinema.cinema_type.price_multiplier,
                "created_at": cinema.created_at.isoformat(),
                "updated_at": cinema.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting cinema by ID {cinema_id}: {e}")
            raise

    async def get_cinema_by_number(self, cinema_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific cinema by number"""
        try:
            cinema = self.db.query(Cinema).join(CinemaType).filter(Cinema.number == cinema_number).first()
            if not cinema:
                return None

            return {
                "id": str(cinema.id),
                "number": cinema.number,
                "type": cinema.cinema_type.name,
                "type_description": cinema.cinema_type.description,
                "total_seats": cinema.total_seats,
                "location": cinema.location,
                "features": cinema.features or [],
                "price_multiplier": cinema.cinema_type.price_multiplier,
                "created_at": cinema.created_at.isoformat(),
                "updated_at": cinema.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting cinema by number {cinema_number}: {e}")
            raise

    async def get_available_cinemas(
        self,
        datetime_slot: str = None,
        min_seats: int = None
    ) -> List[Dict[str, Any]]:
        """Get available cinemas based on criteria"""
        try:
            query = self.db.query(Cinema).join(CinemaType)

            if min_seats:
                query = query.filter(Cinema.total_seats >= min_seats)

            # TODO: Add schedule conflict checking when datetime_slot is provided
            # This would require joining with Schedule table to check for conflicts

            cinemas = query.all()
            return [
                {
                    "id": str(cinema.id),
                    "number": cinema.number,
                    "type": cinema.cinema_type.name,
                    "type_description": cinema.cinema_type.description,
                    "total_seats": cinema.total_seats,
                    "location": cinema.location,
                    "features": cinema.features or [],
                    "price_multiplier": cinema.cinema_type.price_multiplier,
                    "available": True  # TODO: Calculate actual availability
                }
                for cinema in cinemas
            ]
        except Exception as e:
            logger.error(f"Error getting available cinemas: {e}")
            raise

    async def create_cinema(
        self,
        number: int,
        cinema_type: str,
        total_seats: int,
        location: str,
        features: List[str] = None
    ) -> Dict[str, Any]:
        """Create a new cinema"""
        try:
            # Check if cinema number already exists
            existing = self.db.query(Cinema).filter(Cinema.number == number).first()
            if existing:
                raise ValueError(f"Cinema number {number} already exists")

            # Check if cinema type exists
            cinema_type_obj = self.db.query(CinemaType).filter(CinemaType.id == cinema_type).first()
            if not cinema_type_obj:
                raise ValueError(f"Cinema type {cinema_type} not found")

            cinema = Cinema(
                number=number,
                type=cinema_type,
                total_seats=total_seats,
                location=location,
                features=features or []
            )

            self.db.add(cinema)
            self.db.commit()
            self.db.refresh(cinema)

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="cinemas",
                operation="create",
                entity_id=str(cinema.id),
                data={
                    "number": cinema.number,
                    "total_seats": cinema.total_seats,
                    "location": cinema.location
                }
            )

            return {
                "id": str(cinema.id),
                "number": cinema.number,
                "type": cinema_type_obj.name,
                "type_description": cinema_type_obj.description,
                "total_seats": cinema.total_seats,
                "location": cinema.location,
                "features": cinema.features or [],
                "price_multiplier": cinema_type_obj.price_multiplier,
                "created_at": cinema.created_at.isoformat(),
                "updated_at": cinema.updated_at.isoformat(),
                "message": f"Cinema {number} created successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating cinema: {e}")
            raise

    async def update_cinema(
        self,
        cinema_id: str,
        total_seats: int = None,
        location: str = None,
        features: List[str] = None
    ) -> Dict[str, Any]:
        """Update an existing cinema"""
        try:
            cinema = self.db.query(Cinema).filter(Cinema.id == cinema_id).first()
            if not cinema:
                raise ValueError(f"Cinema with ID {cinema_id} not found")

            if total_seats is not None:
                cinema.total_seats = total_seats
            if location is not None:
                cinema.location = location
            if features is not None:
                cinema.features = features

            self.db.commit()
            self.db.refresh(cinema)

            cinema_type_obj = self.db.query(CinemaType).filter(CinemaType.id == cinema.type).first()

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="cinemas",
                operation="update",
                entity_id=cinema_id,
                data={
                    "number": cinema.number,
                    "total_seats": cinema.total_seats,
                    "location": cinema.location
                }
            )

            return {
                "id": str(cinema.id),
                "number": cinema.number,
                "type": cinema_type_obj.name if cinema_type_obj else cinema.type,
                "total_seats": cinema.total_seats,
                "location": cinema.location,
                "features": cinema.features or [],
                "updated_at": cinema.updated_at.isoformat(),
                "message": f"Cinema {cinema.number} updated successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating cinema: {e}")
            raise

    async def delete_cinema(self, cinema_number: int) -> Dict[str, Any]:
        """Delete a cinema (if no schedules exist)"""
        try:
            cinema = self.db.query(Cinema).filter(Cinema.number == cinema_number).first()
            if not cinema:
                raise ValueError(f"Cinema with number {cinema_number} not found")

            # Check if cinema has any schedules
            # This would require importing Schedule model, but avoiding circular imports
            # For now, we'll assume it's safe to delete
            # TODO: Add schedule check once schedule_service is implemented

            cinema_id = str(cinema.id)
            self.db.delete(cinema)
            self.db.commit()

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="cinemas",
                operation="delete",
                entity_id=cinema_id,
                data={
                    "number": cinema_number
                }
            )

            return {
                "id": cinema_id,
                "message": f"Cinema {cinema_number} deleted successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting cinema: {e}")
            raise

    async def get_cinema_types(self) -> List[Dict[str, Any]]:
        """Get all available cinema types"""
        try:
            cinema_types = self.db.query(CinemaType).all()
            return [
                {
                    "id": cinema_type.id,
                    "name": cinema_type.name,
                    "description": cinema_type.description,
                    "price_multiplier": cinema_type.price_multiplier
                }
                for cinema_type in cinema_types
            ]
        except Exception as e:
            logger.error(f"Error getting cinema types: {e}")
            raise

# Global cinema service instance
cinema_service = CinemaService()