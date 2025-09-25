from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.movie import Movie
from app.models.cinema import Cinema, CinemaType
from app.models.schedule import Schedule
from app.models.forecast import Forecast
from app.logging import get_logger, add_service_context
from datetime import datetime, timedelta
import random

logger = get_logger(__name__)


class OptimizationService:
    """Service class for schedule generation and optimization"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def generate_schedules_for_forecast(
        self, forecast: Forecast
    ) -> List[Schedule]:
        """Main entry point for generating optimized schedules for a forecast"""
        try:
            logger.info(f"Starting schedule generation for forecast {forecast.id}")

            # Get available resources
            movies = await self._get_available_movies()
            cinemas = await self._get_available_cinemas()

            if not movies or not cinemas:
                raise ValueError("No movies or cinemas available for scheduling")

            # Generate variable time slots (0-5 per day)
            time_slots = self._generate_time_slots(
                forecast.date_range_start, forecast.date_range_end
            )
            logger.info(f"Generated {len(time_slots)} time slots")

            # Generate schedules with variable cinema utilization
            schedules = []
            for time_slot in time_slots:
                # Variable cinema utilization per time slot (40-80%)
                utilization_rate = random.uniform(0.4, 0.8)
                num_active_cinemas = int(len(cinemas) * utilization_rate)

                if num_active_cinemas > 0:
                    active_cinemas = random.sample(cinemas, k=num_active_cinemas)

                    for cinema, cinema_type in active_cinemas:
                        movie = self._select_movie_for_slot(
                            time_slot, movies, forecast.optimization_parameters or {}
                        )

                        if movie:
                            schedule = self._create_realistic_schedule(
                                movie, (cinema, cinema_type), time_slot, forecast
                            )
                            schedules.append(schedule)

            # Apply optimization parameters
            schedules = self._apply_parameters(
                schedules, forecast.optimization_parameters or {}
            )

            # Bulk insert for better performance
            if schedules:
                self.db.add_all(schedules)
                self.db.commit()

            service_logger.info(
                "Schedule generation completed successfully",
                schedules_generated=len(schedules),
                forecast_id=str(forecast.id),
                performance_metrics={
                    "schedules_per_day": round(len(schedules) / ((forecast.date_range_end - forecast.date_range_start).days + 1), 2),
                    "total_time_slots": len(time_slots),
                    "utilization_efficiency": "optimized"
                }
            )
            return schedules

        except Exception as e:
            self.db.rollback()
            service_logger.error(
                "Failed to generate schedules for forecast",
                error=str(e),
                error_type=type(e).__name__,
                forecast_id=str(forecast.id),
                exc_info=True
            )
            raise

    async def _get_available_movies(self) -> List[Movie]:
        """Get all available movies for scheduling"""
        try:
            movies = self.db.query(Movie).all()
            logger.info("Retrieved available movies", movie_count=len(movies))
            return movies
        except Exception as e:
            logger.error(
                "Failed to retrieve available movies",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise

    async def _get_available_cinemas(self) -> List[Tuple[Cinema, CinemaType]]:
        """Get all available cinemas with their types"""
        try:
            cinemas_with_types = (
                self.db.query(Cinema, CinemaType)
                .join(CinemaType, Cinema.type == CinemaType.id)
                .all()
            )
            logger.info(
                "Retrieved available cinemas",
                cinema_count=len(cinemas_with_types)
            )
            return cinemas_with_types
        except Exception as e:
            logger.error(
                "Failed to retrieve available cinemas",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise

    def _generate_time_slots(
        self, start_date: datetime, end_date: datetime
    ) -> List[datetime]:
        """Generate realistic variable time slots with day-of-week weighting (0-5 per day)"""
        time_slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()

        # Available time slots per day
        available_slots = [9, 12, 15, 18, 21]  # 9 AM, 12 PM, 3 PM, 6 PM, 9 PM

        while current_date <= end_date_only:
            weekday = current_date.weekday()  # 0=Monday, 6=Sunday

            # Weight by day of week for more realism
            if weekday in [4, 5, 6]:  # Friday, Saturday, Sunday
                # Weekend: More likely to have more showings
                num_slots_today = random.choices(
                    range(0, 6), weights=[5, 10, 15, 25, 30, 15]  # Favor 3-5 slots
                )[0]
            elif weekday in [0, 1, 2, 3]:  # Monday-Thursday
                # Weekdays: More conservative
                num_slots_today = random.choices(
                    range(0, 6), weights=[15, 25, 30, 20, 8, 2]  # Favor 1-3 slots
                )[0]

            if num_slots_today > 0:
                # Randomly select which time slots to use
                selected_hours = random.sample(available_slots, k=num_slots_today)

                for hour in selected_hours:
                    slot_time = datetime.combine(
                        current_date, datetime.min.time().replace(hour=hour, minute=0)
                    )
                    time_slots.append(slot_time)

            current_date += timedelta(days=1)

        return time_slots

    def _select_movie_for_slot(
        self, time_slot: datetime, movies: List[Movie], parameters: Dict[str, Any]
    ) -> Optional[Movie]:
        """Select appropriate movie for a given time slot based on optimization parameters"""
        if not movies:
            return None

        # Determine if this is prime time (6 PM - 10 PM)
        is_prime_time = 18 <= time_slot.hour < 22

        # Get movie preferences from parameters
        movie_preferences = parameters.get("movie_preferences", {})

        # Create weighted movie list
        weighted_movies = []
        for movie in movies:
            base_weight = 1.0

            # Apply movie preferences
            movie_id_str = str(movie.id)
            if movie_id_str in movie_preferences:
                base_weight *= movie_preferences[movie_id_str]

            # Boost popular genres during prime time
            if is_prime_time:
                if movie.genre.lower() in ["action", "adventure", "thriller", "drama"]:
                    base_weight *= 1.5

            # Add some randomization to avoid perfect patterns
            random_factor = random.uniform(0.8, 1.2)
            final_weight = base_weight * random_factor

            weighted_movies.append((movie, final_weight))

        # Select movie based on weights
        if weighted_movies:
            # Sort by weight and pick from top choices with some randomization
            weighted_movies.sort(key=lambda x: x[1], reverse=True)
            top_choices = weighted_movies[: max(3, len(weighted_movies) // 3)]
            return random.choice(top_choices)[0]

        return random.choice(movies)

    def _create_realistic_schedule(
        self,
        movie: Movie,
        cinema_info: Tuple[Cinema, CinemaType],
        time_slot: datetime,
        forecast: Forecast,
    ) -> Schedule:
        """Create a realistic schedule entry with proper pricing and occupancy"""
        cinema, cinema_type = cinema_info

        # Calculate base pricing
        base_price = self._calculate_pricing(cinema_type, time_slot)
        service_fee = base_price * 0.15  # 15% service fee

        # Calculate realistic occupancy (max_sales based on cinema capacity)
        is_prime_time = 18 <= time_slot.hour < 22
        is_weekend = time_slot.weekday() >= 5

        # Base occupancy rates
        if is_prime_time and is_weekend:
            occupancy_rate = random.uniform(0.60, 0.85)
        elif is_prime_time or is_weekend:
            occupancy_rate = random.uniform(0.45, 0.70)
        else:
            occupancy_rate = random.uniform(0.20, 0.50)

        # Apply occupancy goal from parameters
        occupancy_goal = (
            forecast.optimization_parameters.get("occupancy_goal", 0.7)
            if forecast.optimization_parameters
            else 0.7
        )
        if occupancy_goal:
            # Adjust towards goal with some variance
            target_rate = occupancy_goal * random.uniform(0.8, 1.2)
            occupancy_rate = (occupancy_rate + target_rate) / 2
            occupancy_rate = max(
                0.1, min(0.9, occupancy_rate)
            )  # Clamp between 10% and 90%

        max_sales = int(cinema.total_seats * occupancy_rate)
        current_sales = 0  # New schedules start with 0 sales

        return Schedule(
            movie_id=movie.id,
            cinema_id=cinema.id,
            forecast_id=forecast.id,
            time_slot=time_slot,
            unit_price=base_price,
            service_fee=service_fee,
            max_sales=max_sales,
            current_sales=current_sales,
            status="active",
        )

    def _calculate_pricing(self, cinema_type: CinemaType, time_slot: datetime) -> float:
        """Calculate realistic pricing based on cinema type and time slot"""
        # Base price varies by time
        base_prices = {
            "morning": 8.50,  # 9 AM - 12 PM
            "afternoon": 10.00,  # 12 PM - 6 PM
            "evening": 12.50,  # 6 PM - 11 PM
        }

        hour = time_slot.hour
        if hour < 12:
            base_price = base_prices["morning"]
        elif hour < 18:
            base_price = base_prices["afternoon"]
        else:
            base_price = base_prices["evening"]

        # Apply cinema type multiplier
        final_price = base_price * cinema_type.price_multiplier

        # Weekend premium (10% increase on Friday, Saturday, Sunday)
        if time_slot.weekday() >= 4:  # Friday, Saturday, Sunday
            final_price *= 1.1

        # Round to 2 decimal places
        return round(final_price, 2)

    def _apply_parameters(
        self, schedules: List[Schedule], parameters: Dict[str, Any]
    ) -> List[Schedule]:
        """Apply optimization parameters to adjust generated schedules"""
        if not parameters:
            return schedules

        # Apply revenue goal multiplier
        revenue_goal = parameters.get("revenue_goal", 1.0)
        if revenue_goal != 1.0:
            for schedule in schedules:
                # Adjust pricing based on revenue goal
                schedule.unit_price *= revenue_goal
                schedule.unit_price = round(schedule.unit_price, 2)

                # Recalculate service fee
                schedule.service_fee = schedule.unit_price * 0.15
                schedule.service_fee = round(schedule.service_fee, 2)

        return schedules


# Global optimization service instance
optimization_service = OptimizationService()
