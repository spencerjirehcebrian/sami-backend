from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.database import get_db
from app.models.schedule import Schedule
from app.models.movie import Movie
from app.models.cinema import Cinema, CinemaType
from app.notifications.broadcaster import broadcaster
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ScheduleService:
    """Service class for schedule management operations"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def get_all_schedules(
        self,
        date_from: str = None,
        date_to: str = None,
        cinema_id: str = None,
        movie_id: str = None,
        limit: int = 100,
        offset: int = 0,
        require_date_filter: bool = True
    ) -> Dict[str, Any]:
        """Get schedules with optional filtering, pagination, and safety guards"""
        try:
            # Validate datetime formats early
            date_from_parsed = None
            date_to_parsed = None

            if date_from:
                try:
                    date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                except ValueError:
                    raise ValueError(f"Invalid date_from format: {date_from}. Use ISO 8601 format.")

            if date_to:
                try:
                    date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                except ValueError:
                    raise ValueError(f"Invalid date_to format: {date_to}. Use ISO 8601 format.")

            # Validate date range - maximum 6 months
            if date_from_parsed and date_to_parsed:
                date_range = date_to_parsed - date_from_parsed
                if date_range.days > 180:  # 6 months
                    raise ValueError("Date range cannot exceed 6 months (180 days)")

            # Require date filters for large datasets (unless explicitly disabled)
            if require_date_filter and not (date_from or date_to):
                raise ValueError("Date filter (date_from or date_to) is required for schedule queries")

            # Validate pagination parameters
            if limit < 1 or limit > 1000:
                raise ValueError("Limit must be between 1 and 1000")
            if offset < 0:
                raise ValueError("Offset must be non-negative")

            # Build query with filters
            query = self.db.query(Schedule).join(Movie).join(Cinema).join(CinemaType)

            # Apply date filters
            if date_from_parsed:
                query = query.filter(Schedule.time_slot >= date_from_parsed)

            if date_to_parsed:
                query = query.filter(Schedule.time_slot <= date_to_parsed)

            if cinema_id:
                query = query.filter(Schedule.cinema_id == cinema_id)

            if movie_id:
                query = query.filter(Schedule.movie_id == movie_id)

            # Get total count before pagination
            total_count = query.count()

            # Apply pagination
            schedules = query.offset(offset).limit(limit).all()

            # Build schedule data
            schedule_data = [
                {
                    "id": str(schedule.id),
                    "movie_id": str(schedule.movie_id),
                    "movie_title": schedule.movie.title,
                    "movie_duration": schedule.movie.duration,
                    "movie_genre": schedule.movie.genre,
                    "movie_rating": schedule.movie.rating,
                    "cinema_id": str(schedule.cinema_id),
                    "cinema_number": schedule.cinema.number,
                    "cinema_type": schedule.cinema.cinema_type.name,
                    "cinema_location": schedule.cinema.location,
                    "total_seats": schedule.cinema.total_seats,
                    "time_slot": schedule.time_slot.isoformat(),
                    "unit_price": schedule.unit_price,
                    "service_fee": schedule.service_fee,
                    "max_sales": schedule.max_sales,
                    "current_sales": schedule.current_sales,
                    "available_seats": schedule.max_sales - schedule.current_sales,
                    "occupancy_rate": round((schedule.current_sales / schedule.max_sales) * 100, 2) if schedule.max_sales > 0 else 0,
                    "status": schedule.status,
                    "created_at": schedule.created_at.isoformat(),
                    "updated_at": schedule.updated_at.isoformat()
                }
                for schedule in schedules
            ]

            # Calculate pagination metadata
            has_next = (offset + limit) < total_count
            has_prev = offset > 0
            total_pages = (total_count + limit - 1) // limit  # Ceiling division
            current_page = (offset // limit) + 1

            return {
                "data": schedule_data,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
        except Exception as e:
            logger.error(f"Error getting schedules: {e}")
            raise

    async def get_schedule_by_id(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific schedule by ID"""
        try:
            schedule = self.db.query(Schedule).join(Movie).join(Cinema).join(CinemaType).filter(
                Schedule.id == schedule_id
            ).first()

            if not schedule:
                return None

            return {
                "id": str(schedule.id),
                "movie_id": str(schedule.movie_id),
                "movie_title": schedule.movie.title,
                "movie_duration": schedule.movie.duration,
                "movie_genre": schedule.movie.genre,
                "movie_rating": schedule.movie.rating,
                "cinema_id": str(schedule.cinema_id),
                "cinema_number": schedule.cinema.number,
                "cinema_type": schedule.cinema.cinema_type.name,
                "cinema_location": schedule.cinema.location,
                "total_seats": schedule.cinema.total_seats,
                "time_slot": schedule.time_slot.isoformat(),
                "unit_price": schedule.unit_price,
                "service_fee": schedule.service_fee,
                "max_sales": schedule.max_sales,
                "current_sales": schedule.current_sales,
                "available_seats": schedule.max_sales - schedule.current_sales,
                "occupancy_rate": round((schedule.current_sales / schedule.max_sales) * 100, 2) if schedule.max_sales > 0 else 0,
                "status": schedule.status,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting schedule by ID {schedule_id}: {e}")
            raise

    async def create_schedule(
        self,
        movie_id: str,
        cinema_id: str,
        time_slot: str,
        unit_price: float,
        service_fee: float = 0.0,
        max_sales: int = None
    ) -> Dict[str, Any]:
        """Create a new schedule"""
        try:
            # Parse time slot
            time_slot_parsed = datetime.fromisoformat(time_slot.replace('Z', '+00:00'))

            # Validate movie exists
            movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
            if not movie:
                raise ValueError(f"Movie with ID {movie_id} not found")

            # Validate cinema exists
            cinema = self.db.query(Cinema).filter(Cinema.id == cinema_id).first()
            if not cinema:
                raise ValueError(f"Cinema with ID {cinema_id} not found")

            # Calculate movie end time for conflict checking
            movie_end_time = time_slot_parsed + timedelta(minutes=movie.duration + 30)  # 30 min cleanup buffer

            # Check for schedule conflicts
            conflicts = self.db.query(Schedule).join(Movie).filter(
                and_(
                    Schedule.cinema_id == cinema_id,
                    Schedule.status == "active",
                    or_(
                        # New movie starts during existing movie
                        and_(
                            Schedule.time_slot <= time_slot_parsed,
                            func.datetime(Schedule.time_slot, '+' + func.cast(Movie.duration + 30, func.text()) + ' minutes') > time_slot_parsed
                        ),
                        # Existing movie starts during new movie
                        and_(
                            Schedule.time_slot < movie_end_time,
                            Schedule.time_slot >= time_slot_parsed
                        )
                    )
                )
            ).all()

            if conflicts:
                conflict_details = [
                    f"{conflict.movie.title} at {conflict.time_slot.strftime('%H:%M')}"
                    for conflict in conflicts
                ]
                raise ValueError(f"Schedule conflict detected with: {', '.join(conflict_details)}")

            # Set max_sales to cinema capacity if not provided
            if max_sales is None:
                max_sales = cinema.total_seats

            # Validate max_sales doesn't exceed cinema capacity
            if max_sales > cinema.total_seats:
                raise ValueError(f"Max sales ({max_sales}) cannot exceed cinema capacity ({cinema.total_seats})")

            schedule = Schedule(
                movie_id=movie_id,
                cinema_id=cinema_id,
                time_slot=time_slot_parsed,
                unit_price=unit_price,
                service_fee=service_fee,
                max_sales=max_sales,
                current_sales=0,
                status="active"
            )

            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="schedules",
                operation="create",
                entity_id=str(schedule.id),
                data={
                    "movie_id": str(schedule.movie_id),
                    "cinema_id": str(schedule.cinema_id),
                    "time_slot": schedule.time_slot.isoformat(),
                    "unit_price": float(schedule.unit_price)
                }
            )

            # Get the full schedule details for response
            full_schedule = await self.get_schedule_by_id(str(schedule.id))
            full_schedule["message"] = f"Schedule created for {movie.title} in Cinema {cinema.number} at {time_slot_parsed.strftime('%Y-%m-%d %H:%M')}"

            return full_schedule
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating schedule: {e}")
            raise

    async def update_schedule(
        self,
        schedule_id: str,
        time_slot: str = None,
        unit_price: float = None,
        service_fee: float = None,
        max_sales: int = None,
        status: str = None
    ) -> Dict[str, Any]:
        """Update an existing schedule"""
        try:
            schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule:
                raise ValueError(f"Schedule with ID {schedule_id} not found")

            # Update fields if provided
            if time_slot is not None:
                new_time_slot = datetime.fromisoformat(time_slot.replace('Z', '+00:00'))

                # Check for conflicts if time is changing
                movie = self.db.query(Movie).filter(Movie.id == schedule.movie_id).first()
                movie_end_time = new_time_slot + timedelta(minutes=movie.duration + 30)

                conflicts = self.db.query(Schedule).join(Movie).filter(
                    and_(
                        Schedule.cinema_id == schedule.cinema_id,
                        Schedule.id != schedule_id,
                        Schedule.status == "active",
                        or_(
                            and_(
                                Schedule.time_slot <= new_time_slot,
                                func.datetime(Schedule.time_slot, '+' + func.cast(Movie.duration + 30, func.text()) + ' minutes') > new_time_slot
                            ),
                            and_(
                                Schedule.time_slot < movie_end_time,
                                Schedule.time_slot >= new_time_slot
                            )
                        )
                    )
                ).all()

                if conflicts:
                    conflict_details = [
                        f"{conflict.movie.title} at {conflict.time_slot.strftime('%H:%M')}"
                        for conflict in conflicts
                    ]
                    raise ValueError(f"Schedule conflict detected with: {', '.join(conflict_details)}")

                schedule.time_slot = new_time_slot

            if unit_price is not None:
                schedule.unit_price = unit_price
            if service_fee is not None:
                schedule.service_fee = service_fee
            if max_sales is not None:
                cinema = self.db.query(Cinema).filter(Cinema.id == schedule.cinema_id).first()
                if max_sales > cinema.total_seats:
                    raise ValueError(f"Max sales ({max_sales}) cannot exceed cinema capacity ({cinema.total_seats})")
                schedule.max_sales = max_sales
            if status is not None:
                if status not in ["active", "cancelled", "completed"]:
                    raise ValueError(f"Invalid status: {status}")
                schedule.status = status

            self.db.commit()
            self.db.refresh(schedule)

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="schedules",
                operation="update",
                entity_id=schedule_id,
                data={
                    "movie_id": str(schedule.movie_id),
                    "cinema_id": str(schedule.cinema_id),
                    "time_slot": schedule.time_slot.isoformat(),
                    "unit_price": float(schedule.unit_price),
                    "status": schedule.status
                }
            )

            full_schedule = await self.get_schedule_by_id(str(schedule.id))
            full_schedule["message"] = f"Schedule updated successfully"

            return full_schedule
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating schedule: {e}")
            raise

    async def cancel_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Cancel a schedule"""
        try:
            schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule:
                raise ValueError(f"Schedule with ID {schedule_id} not found")

            schedule.status = "cancelled"
            self.db.commit()

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="schedules",
                operation="delete",
                entity_id=schedule_id,
                data={
                    "cinema_id": str(schedule.cinema_id),
                    "time_slot": schedule.time_slot.isoformat(),
                    "status": "cancelled"
                }
            )

            return {
                "id": str(schedule.id),
                "status": "cancelled",
                "message": f"Schedule cancelled successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling schedule: {e}")
            raise

    async def get_schedules_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Get all schedules for a specific date"""
        try:
            target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            result = await self.get_all_schedules(
                date_from=start_of_day.isoformat(),
                date_to=end_of_day.isoformat(),
                require_date_filter=False  # Don't require additional date filters since we're providing them
            )
            return result["data"]  # Return just the data for backward compatibility
        except Exception as e:
            logger.error(f"Error getting schedules by date {date}: {e}")
            raise

    async def get_available_time_slots(
        self,
        cinema_id: str,
        date: str,
        movie_duration: int
    ) -> List[Dict[str, Any]]:
        """Get available time slots for a cinema on a specific date"""
        try:
            target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            start_of_day = datetime.combine(target_date, datetime.min.time().replace(hour=9))  # Start at 9 AM
            end_of_day = datetime.combine(target_date, datetime.max.time().replace(hour=23, minute=0))  # End at 11 PM

            # Get existing schedules for the cinema on that date
            existing_schedules = self.db.query(Schedule).join(Movie).filter(
                and_(
                    Schedule.cinema_id == cinema_id,
                    Schedule.time_slot >= start_of_day,
                    Schedule.time_slot <= end_of_day,
                    Schedule.status == "active"
                )
            ).all()

            # Generate potential time slots (every 30 minutes from 9 AM to 11 PM)
            potential_slots = []
            current_time = start_of_day
            while current_time <= end_of_day:
                potential_slots.append(current_time)
                current_time += timedelta(minutes=30)

            # Filter out conflicting slots
            available_slots = []
            for slot in potential_slots:
                movie_end_time = slot + timedelta(minutes=movie_duration + 30)

                # Check if this slot conflicts with any existing schedule
                conflict = False
                for existing in existing_schedules:
                    existing_end_time = existing.time_slot + timedelta(minutes=existing.movie.duration + 30)

                    if (slot < existing_end_time and movie_end_time > existing.time_slot):
                        conflict = True
                        break

                if not conflict and movie_end_time <= end_of_day:
                    available_slots.append({
                        "time_slot": slot.isoformat(),
                        "display_time": slot.strftime('%H:%M'),
                        "end_time": movie_end_time.isoformat(),
                        "display_end_time": movie_end_time.strftime('%H:%M')
                    })

            return available_slots
        except Exception as e:
            logger.error(f"Error getting available time slots: {e}")
            raise

# Global schedule service instance
schedule_service = ScheduleService()