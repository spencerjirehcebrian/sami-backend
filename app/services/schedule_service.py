from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func
from app.database import get_db
from app.models.schedule import Schedule
from app.models.movie import Movie
from app.models.cinema import Cinema, CinemaType
from app.notifications.broadcaster import broadcaster
from datetime import datetime, timedelta
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

class ScheduleService:
    """Service class for schedule management operations"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        # Request-scoped cache for frequently accessed entities
        self._cache = {
            'movies': {},
            'cinemas': {},
            'cinema_types': {}
        }

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

            # Build optimized query with eager loading to avoid N+1 queries
            query = self.db.query(Schedule).options(
                joinedload(Schedule.movie),
                joinedload(Schedule.cinema).joinedload(Cinema.cinema_type)
            )

            # Apply date filters
            if date_from_parsed:
                query = query.filter(Schedule.time_slot >= date_from_parsed)

            if date_to_parsed:
                query = query.filter(Schedule.time_slot <= date_to_parsed)

            if cinema_id:
                query = query.filter(Schedule.cinema_id == cinema_id)

            if movie_id:
                query = query.filter(Schedule.movie_id == movie_id)

            # Get total count before pagination (without eager loading for count)
            count_query = self.db.query(Schedule.id)
            if date_from_parsed:
                count_query = count_query.filter(Schedule.time_slot >= date_from_parsed)
            if date_to_parsed:
                count_query = count_query.filter(Schedule.time_slot <= date_to_parsed)
            if cinema_id:
                count_query = count_query.filter(Schedule.cinema_id == cinema_id)
            if movie_id:
                count_query = count_query.filter(Schedule.movie_id == movie_id)

            total_count = count_query.count()

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
        """Get a specific schedule by ID with optimized relationship loading"""
        try:
            schedule = self.db.query(Schedule).options(
                joinedload(Schedule.movie),
                joinedload(Schedule.cinema).joinedload(Cinema.cinema_type)
            ).filter(
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

    def get_schedules_summary(
        self,
        date_from: str = None,
        date_to: str = None,
        cinema_id: str = None,
        movie_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get schedule summaries with minimal data - optimized for list views.
        Only loads essential columns to reduce memory usage and transfer time.
        """
        try:
            # Parse date filters
            date_from_parsed = None
            date_to_parsed = None

            if date_from:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            if date_to:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))

            # Column-only query for better performance
            query = self.db.query(
                Schedule.id,
                Schedule.time_slot,
                Schedule.unit_price,
                Schedule.service_fee,
                Schedule.current_sales,
                Schedule.max_sales,
                Schedule.status,
                Movie.title.label('movie_title'),
                Movie.duration.label('movie_duration'),
                Cinema.number.label('cinema_number'),
                CinemaType.name.label('cinema_type')
            ).join(Movie).join(Cinema).join(CinemaType)

            # Apply filters
            if date_from_parsed:
                query = query.filter(Schedule.time_slot >= date_from_parsed)
            if date_to_parsed:
                query = query.filter(Schedule.time_slot <= date_to_parsed)
            if cinema_id:
                query = query.filter(Schedule.cinema_id == cinema_id)
            if movie_id:
                query = query.filter(Schedule.movie_id == movie_id)

            # Apply pagination and execute
            schedules = query.offset(offset).limit(limit).all()

            # Format minimal response
            return [
                {
                    "id": str(schedule.id),
                    "time_slot": schedule.time_slot.isoformat(),
                    "movie_title": schedule.movie_title,
                    "movie_duration": schedule.movie_duration,
                    "cinema_number": schedule.cinema_number,
                    "cinema_type": schedule.cinema_type,
                    "unit_price": schedule.unit_price,
                    "service_fee": schedule.service_fee,
                    "current_sales": schedule.current_sales,
                    "max_sales": schedule.max_sales,
                    "available_seats": schedule.max_sales - schedule.current_sales,
                    "occupancy_rate": round((schedule.current_sales / schedule.max_sales) * 100, 2) if schedule.max_sales > 0 else 0,
                    "status": schedule.status
                }
                for schedule in schedules
            ]

        except Exception as e:
            logger.error(f"Error getting schedule summaries: {e}")
            raise

    def get_schedules_for_export(
        self,
        date_from: str = None,
        date_to: str = None,
        cinema_id: str = None,
        movie_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get schedules optimized for export operations.
        Loads only essential columns needed for reports/exports.
        """
        try:
            # Parse date filters
            date_from_parsed = None
            date_to_parsed = None

            if date_from:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            if date_to:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))

            # Export-optimized query with specific columns
            query = self.db.query(
                Schedule.time_slot,
                Movie.title.label('movie'),
                Movie.genre.label('genre'),
                Movie.rating.label('rating'),
                Movie.duration.label('duration'),
                Cinema.number.label('cinema'),
                Cinema.location.label('location'),
                CinemaType.name.label('type'),
                Schedule.unit_price,
                Schedule.service_fee,
                Schedule.current_sales,
                Schedule.max_sales,
                Schedule.status,
                ((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('revenue')
            ).join(Movie).join(Cinema).join(CinemaType)

            # Apply filters
            if date_from_parsed:
                query = query.filter(Schedule.time_slot >= date_from_parsed)
            if date_to_parsed:
                query = query.filter(Schedule.time_slot <= date_to_parsed)
            if cinema_id:
                query = query.filter(Schedule.cinema_id == cinema_id)
            if movie_id:
                query = query.filter(Schedule.movie_id == movie_id)

            schedules = query.all()

            # Format for export
            return [
                {
                    "date": schedule.time_slot.date().isoformat(),
                    "time": schedule.time_slot.strftime("%H:%M"),
                    "movie": schedule.movie,
                    "genre": schedule.genre,
                    "rating": schedule.rating,
                    "duration": schedule.duration,
                    "cinema": f"Cinema {schedule.cinema}",
                    "location": schedule.location,
                    "type": schedule.type,
                    "ticket_price": schedule.unit_price + schedule.service_fee,
                    "tickets_sold": schedule.current_sales,
                    "capacity": schedule.max_sales,
                    "occupancy_rate": round((schedule.current_sales / schedule.max_sales) * 100, 2) if schedule.max_sales > 0 else 0,
                    "revenue": round(float(schedule.revenue or 0), 2),
                    "status": schedule.status
                }
                for schedule in schedules
            ]

        except Exception as e:
            logger.error(f"Error getting schedules for export: {e}")
            raise

    def schedule_exists(
        self,
        cinema_id: str,
        time_slot: datetime,
        exclude_schedule_id: str = None
    ) -> bool:
        """
        Optimized existence check using EXISTS query instead of loading objects.
        Much faster than loading full objects when only checking existence.
        """
        try:
            # Build EXISTS query
            exists_query = self.db.query(Schedule.id).filter(
                Schedule.cinema_id == cinema_id,
                Schedule.time_slot == time_slot
            )

            # Exclude specific schedule if provided
            if exclude_schedule_id:
                exists_query = exists_query.filter(Schedule.id != exclude_schedule_id)

            # Use EXISTS for optimal performance
            return self.db.query(exists_query.exists()).scalar()

        except Exception as e:
            logger.error(f"Error checking schedule existence: {e}")
            raise

    def schedule_exists_by_id(self, schedule_id: str) -> bool:
        """Optimized schedule existence check by ID using EXISTS query."""
        try:
            return self.db.query(
                self.db.query(Schedule.id).filter(Schedule.id == schedule_id).exists()
            ).scalar()
        except Exception as e:
            logger.error(f"Error checking schedule existence by ID: {e}")
            raise

    def cinema_exists(self, cinema_id: str) -> bool:
        """Optimized cinema existence check using EXISTS query."""
        try:
            return self.db.query(
                self.db.query(Cinema.id).filter(Cinema.id == cinema_id).exists()
            ).scalar()
        except Exception as e:
            logger.error(f"Error checking cinema existence: {e}")
            raise

    def movie_exists(self, movie_id: str) -> bool:
        """Optimized movie existence check using EXISTS query."""
        try:
            return self.db.query(
                self.db.query(Movie.id).filter(Movie.id == movie_id).exists()
            ).scalar()
        except Exception as e:
            logger.error(f"Error checking movie existence: {e}")
            raise

    def get_schedules_count(
        self,
        date_from: str = None,
        date_to: str = None,
        cinema_id: str = None,
        movie_id: str = None
    ) -> int:
        """
        Optimized count query without loading objects.
        Much faster than len(get_all_schedules()) for pagination.
        """
        try:
            # Parse date filters
            date_from_parsed = None
            date_to_parsed = None

            if date_from:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            if date_to:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))

            # Count-only query
            query = self.db.query(Schedule.id)

            # Apply filters
            if date_from_parsed:
                query = query.filter(Schedule.time_slot >= date_from_parsed)
            if date_to_parsed:
                query = query.filter(Schedule.time_slot <= date_to_parsed)
            if cinema_id:
                query = query.filter(Schedule.cinema_id == cinema_id)
            if movie_id:
                query = query.filter(Schedule.movie_id == movie_id)

            return query.count()

        except Exception as e:
            logger.error(f"Error getting schedules count: {e}")
            raise

    async def check_schedule_conflicts(
        self,
        cinema_id: str,
        time_slot: datetime,
        movie_duration: int,
        exclude_schedule_id: str = None
    ) -> bool:
        """
        Optimized conflict detection using EXISTS query and database functions.
        Returns True if conflicts exist, False otherwise.
        """
        try:
            # Calculate movie end time using SQL INTERVAL
            movie_end_time = time_slot + timedelta(minutes=movie_duration + 30)  # 30 min cleanup buffer

            # Build base conflict query using EXISTS for performance
            conflict_query = self.db.query(func.count(Schedule.id)).filter(
                and_(
                    Schedule.cinema_id == cinema_id,
                    Schedule.status == "active",
                    # Time overlap logic: two time ranges overlap if:
                    # start1 < end2 AND start2 < end1
                    Schedule.time_slot < movie_end_time,
                    func.datetime(Schedule.time_slot, '+' + func.cast(
                        func.coalesce(
                            self.db.query(Movie.duration).filter(Movie.id == Schedule.movie_id).scalar_subquery(),
                            0
                        ) + 30,
                        func.text('text')
                    ) + ' minutes') > time_slot
                )
            )

            # Exclude specific schedule if provided (for updates)
            if exclude_schedule_id:
                conflict_query = conflict_query.filter(Schedule.id != exclude_schedule_id)

            # Execute optimized count query
            conflict_count = conflict_query.scalar()
            return conflict_count > 0

        except Exception as e:
            logger.error(f"Error checking schedule conflicts: {e}")
            raise

    async def get_detailed_conflicts(
        self,
        cinema_id: str,
        time_slot: datetime,
        movie_duration: int,
        exclude_schedule_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get detailed conflict information for API responses.
        Only called when conflicts are detected.
        """
        try:
            movie_end_time = time_slot + timedelta(minutes=movie_duration + 30)

            # Query for detailed conflict information
            conflicts = self.db.query(Schedule, Movie.title, Movie.duration).join(Movie).filter(
                and_(
                    Schedule.cinema_id == cinema_id,
                    Schedule.status == "active",
                    Schedule.time_slot < movie_end_time,
                    func.datetime(Schedule.time_slot, '+' + func.cast(Movie.duration + 30, func.text()) + ' minutes') > time_slot
                )
            )

            if exclude_schedule_id:
                conflicts = conflicts.filter(Schedule.id != exclude_schedule_id)

            conflict_results = []
            for schedule, movie_title, movie_duration_val in conflicts.all():
                conflict_end = schedule.time_slot + timedelta(minutes=movie_duration_val + 30)
                conflict_results.append({
                    "schedule_id": str(schedule.id),
                    "movie_title": movie_title,
                    "time_slot": schedule.time_slot.isoformat(),
                    "end_time": conflict_end.isoformat(),
                    "display_time": f"{movie_title} at {schedule.time_slot.strftime('%H:%M')}"
                })

            return conflict_results

        except Exception as e:
            logger.error(f"Error getting detailed conflicts: {e}")
            raise

    async def check_conflicts(
        self,
        movie_id: str,
        cinema_id: str = None,
        cinema_number: int = None,
        time_slot: str = None,
        exclude_schedule_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Public API method for conflict checking.
        Supports both cinema_id and cinema_number parameters.
        """
        try:
            # Convert cinema_number to cinema_id if needed
            actual_cinema_id = cinema_id
            if cinema_number and not cinema_id:
                from app.models.cinema import Cinema
                cinema = self.db.query(Cinema).filter(Cinema.number == cinema_number).first()
                if not cinema:
                    raise ValueError(f"Cinema with number {cinema_number} not found")
                actual_cinema_id = str(cinema.id)

            if not actual_cinema_id:
                raise ValueError("Either cinema_id or cinema_number must be provided")

            # Parse time slot
            time_slot_parsed = datetime.fromisoformat(time_slot.replace('Z', '+00:00'))

            # Get movie duration
            movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
            if not movie:
                raise ValueError(f"Movie with ID {movie_id} not found")

            # Check for conflicts using optimized method
            has_conflicts = await self.check_schedule_conflicts(
                cinema_id=actual_cinema_id,
                time_slot=time_slot_parsed,
                movie_duration=movie.duration,
                exclude_schedule_id=exclude_schedule_id
            )

            # Return detailed conflicts only if they exist
            if has_conflicts:
                return await self.get_detailed_conflicts(
                    cinema_id=actual_cinema_id,
                    time_slot=time_slot_parsed,
                    movie_duration=movie.duration,
                    exclude_schedule_id=exclude_schedule_id
                )
            else:
                return []

        except Exception as e:
            logger.error(f"Error in check_conflicts: {e}")
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

            # Use optimized conflict detection
            has_conflicts = await self.check_schedule_conflicts(
                cinema_id=cinema_id,
                time_slot=time_slot_parsed,
                movie_duration=movie.duration
            )

            if has_conflicts:
                # Get detailed conflict information for error message
                conflict_details = await self.get_detailed_conflicts(
                    cinema_id=cinema_id,
                    time_slot=time_slot_parsed,
                    movie_duration=movie.duration
                )
                conflict_messages = [conflict["display_time"] for conflict in conflict_details]
                raise ValueError(f"Schedule conflict detected with: {', '.join(conflict_messages)}")

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

                # Check for conflicts if time is changing using optimized method
                movie = self.db.query(Movie).filter(Movie.id == schedule.movie_id).first()

                has_conflicts = await self.check_schedule_conflicts(
                    cinema_id=str(schedule.cinema_id),
                    time_slot=new_time_slot,
                    movie_duration=movie.duration,
                    exclude_schedule_id=schedule_id
                )

                if has_conflicts:
                    # Get detailed conflict information for error message
                    conflict_details = await self.get_detailed_conflicts(
                        cinema_id=str(schedule.cinema_id),
                        time_slot=new_time_slot,
                        movie_duration=movie.duration,
                        exclude_schedule_id=schedule_id
                    )
                    conflict_messages = [conflict["display_time"] for conflict in conflict_details]
                    raise ValueError(f"Schedule conflict detected with: {', '.join(conflict_messages)}")

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
        """Get available time slots for a cinema on a specific date using optimized conflict detection"""
        try:
            target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            start_of_day = datetime.combine(target_date, datetime.min.time().replace(hour=9))  # Start at 9 AM
            end_of_day = datetime.combine(target_date, datetime.max.time().replace(hour=23, minute=0))  # End at 11 PM

            # Generate potential time slots (every 30 minutes from 9 AM to 11 PM)
            potential_slots = []
            current_time = start_of_day
            while current_time <= end_of_day:
                movie_end_time = current_time + timedelta(minutes=movie_duration + 30)
                # Only include slots where the movie would end before end of day
                if movie_end_time <= end_of_day:
                    potential_slots.append(current_time)
                current_time += timedelta(minutes=30)

            # Use optimized conflict detection for each potential slot
            available_slots = []
            for slot in potential_slots:
                # Use the optimized conflict detection method
                has_conflicts = await self.check_schedule_conflicts(
                    cinema_id=cinema_id,
                    time_slot=slot,
                    movie_duration=movie_duration
                )

                if not has_conflicts:
                    movie_end_time = slot + timedelta(minutes=movie_duration + 30)
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

    async def check_batch_conflicts(
        self,
        cinema_id: str,
        time_slots: List[str],
        movie_duration: int,
        exclude_schedule_ids: List[str] = None
    ) -> Dict[str, bool]:
        """
        Batch conflict checking for multiple time slots.
        Returns a dictionary mapping time_slot -> has_conflicts (bool).
        Optimized for bulk operations.
        """
        try:
            if not time_slots:
                return {}

            exclude_ids = exclude_schedule_ids or []
            results = {}

            # Parse all time slots
            parsed_slots = []
            for slot_str in time_slots:
                try:
                    parsed_slot = datetime.fromisoformat(slot_str.replace('Z', '+00:00'))
                    parsed_slots.append((slot_str, parsed_slot))
                except ValueError:
                    # Mark invalid time slots as having conflicts
                    results[slot_str] = True

            # Check conflicts for valid time slots
            for slot_str, slot_time in parsed_slots:
                has_conflicts = await self.check_schedule_conflicts(
                    cinema_id=cinema_id,
                    time_slot=slot_time,
                    movie_duration=movie_duration,
                    exclude_schedule_id=exclude_ids[0] if exclude_ids else None
                )
                results[slot_str] = has_conflicts

            return results

        except Exception as e:
            logger.error(f"Error in batch conflict checking: {e}")
            raise

    async def get_optimized_available_slots_batch(
        self,
        cinema_id: str,
        date: str,
        movie_duration: int,
        slot_interval_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Highly optimized version that minimizes database queries for available slots.
        Uses a single query to get all existing schedules, then filters in memory for better performance.
        """
        try:
            target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            start_of_day = datetime.combine(target_date, datetime.min.time().replace(hour=9))
            end_of_day = datetime.combine(target_date, datetime.max.time().replace(hour=23, minute=0))

            # Single query to get all existing schedules for the day
            existing_schedules = self.db.query(Schedule.time_slot, Movie.duration).join(Movie).filter(
                and_(
                    Schedule.cinema_id == cinema_id,
                    Schedule.time_slot >= start_of_day,
                    Schedule.time_slot <= end_of_day,
                    Schedule.status == "active"
                )
            ).all()

            # Convert to list of occupied time ranges
            occupied_ranges = []
            for schedule_start, schedule_duration in existing_schedules:
                schedule_end = schedule_start + timedelta(minutes=schedule_duration + 30)
                occupied_ranges.append((schedule_start, schedule_end))

            # Generate and filter potential slots
            available_slots = []
            current_time = start_of_day

            while current_time <= end_of_day:
                movie_end_time = current_time + timedelta(minutes=movie_duration + 30)

                # Skip if movie would end after operating hours
                if movie_end_time > end_of_day:
                    current_time += timedelta(minutes=slot_interval_minutes)
                    continue

                # Check for conflicts with existing schedules
                has_conflict = False
                for occupied_start, occupied_end in occupied_ranges:
                    # Check for time overlap: slot_start < occupied_end AND slot_end > occupied_start
                    if current_time < occupied_end and movie_end_time > occupied_start:
                        has_conflict = True
                        break

                if not has_conflict:
                    available_slots.append({
                        "time_slot": current_time.isoformat(),
                        "display_time": current_time.strftime('%H:%M'),
                        "end_time": movie_end_time.isoformat(),
                        "display_end_time": movie_end_time.strftime('%H:%M')
                    })

                current_time += timedelta(minutes=slot_interval_minutes)

            return available_slots

        except Exception as e:
            logger.error(f"Error getting optimized available slots: {e}")
            raise

    def get_cached_movie(self, movie_id: str) -> Optional[Movie]:
        """
        Get movie from cache or database. Caches movies for the request lifetime
        to avoid repeated queries for the same movie during schedule operations.
        """
        if movie_id in self._cache['movies']:
            return self._cache['movies'][movie_id]

        movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
        if movie:
            self._cache['movies'][movie_id] = movie
        return movie

    def get_cached_cinema(self, cinema_id: str) -> Optional[Cinema]:
        """
        Get cinema from cache or database with eager loading of cinema_type.
        Caches cinemas for the request lifetime to avoid repeated queries.
        """
        if cinema_id in self._cache['cinemas']:
            return self._cache['cinemas'][cinema_id]

        cinema = self.db.query(Cinema).options(
            joinedload(Cinema.cinema_type)
        ).filter(Cinema.id == cinema_id).first()
        if cinema:
            self._cache['cinemas'][cinema_id] = cinema
        return cinema

    def get_cached_cinema_type(self, cinema_type_id: str) -> Optional[CinemaType]:
        """
        Get cinema type from cache or database. Caches cinema types for the
        request lifetime to avoid repeated queries.
        """
        if cinema_type_id in self._cache['cinema_types']:
            return self._cache['cinema_types'][cinema_type_id]

        cinema_type = self.db.query(CinemaType).filter(CinemaType.id == cinema_type_id).first()
        if cinema_type:
            self._cache['cinema_types'][cinema_type_id] = cinema_type
        return cinema_type

    def clear_cache(self):
        """Clear the request-scoped cache. Should be called at the end of requests."""
        self._cache = {
            'movies': {},
            'cinemas': {},
            'cinema_types': {}
        }

# Global schedule service instance
schedule_service = ScheduleService()