from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.movie import Movie
from app.models.cinema import Cinema, CinemaType
from app.models.schedule import Schedule
from app.models.forecast import Forecast
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class OptimizationService:
    """Service class for schedule generation and optimization"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def generate_schedules_for_forecast(self, forecast: Forecast) -> List[Schedule]:
        """Main entry point for generating optimized schedules for a forecast"""
        try:
            logger.info(f"Starting schedule generation for forecast {forecast.id}")

            # Get available resources
            movies = await self._get_available_movies()
            cinemas = await self._get_available_cinemas()

            if not movies or not cinemas:
                raise ValueError("No movies or cinemas available for scheduling")

            # Generate time slots for the date range
            time_slots = self._generate_time_slots(forecast.date_range_start, forecast.date_range_end)
            logger.info(f"Generated {len(time_slots)} time slots")

            # Generate schedules
            schedules = []
            for time_slot in time_slots:
                for cinema in cinemas:
                    # Select movie based on time slot and parameters
                    movie = self._select_movie_for_slot(
                        time_slot,
                        movies,
                        forecast.optimization_parameters or {}
                    )

                    if movie:
                        schedule = self._create_realistic_schedule(
                            movie,
                            cinema,
                            time_slot,
                            forecast
                        )
                        schedules.append(schedule)

            # Apply optimization parameters
            schedules = self._apply_parameters(schedules, forecast.optimization_parameters or {})

            # Save schedules to database
            for schedule in schedules:
                self.db.add(schedule)

            self.db.commit()
            logger.info(f"Generated {len(schedules)} schedules for forecast {forecast.id}")

            return schedules

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating schedules for forecast: {e}")
            raise

    async def _get_available_movies(self) -> List[Movie]:
        """Get all available movies for scheduling"""
        try:
            movies = self.db.query(Movie).all()
            logger.info(f"Found {len(movies)} available movies")
            return movies
        except Exception as e:
            logger.error(f"Error getting available movies: {e}")
            raise

    async def _get_available_cinemas(self) -> List[Tuple[Cinema, CinemaType]]:
        """Get all available cinemas with their types"""
        try:
            cinemas_with_types = (
                self.db.query(Cinema, CinemaType)
                .join(CinemaType, Cinema.type == CinemaType.id)
                .all()
            )
            logger.info(f"Found {len(cinemas_with_types)} available cinemas")
            return cinemas_with_types
        except Exception as e:
            logger.error(f"Error getting available cinemas: {e}")
            raise

    def _generate_time_slots(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Generate 30-minute time slots from 9 AM to 11 PM for each day in range"""
        time_slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()

        while current_date <= end_date_only:
            # Generate slots for this day (9 AM to 11 PM, every 30 minutes)
            for hour in range(9, 23):  # 9 AM to 10:30 PM (last slot)
                for minute in [0, 30]:
                    slot_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                    time_slots.append(slot_time)

            current_date += timedelta(days=1)

        return time_slots

    def _select_movie_for_slot(
        self,
        time_slot: datetime,
        movies: List[Movie],
        parameters: Dict[str, Any]
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
                if movie.genre.lower() in ['action', 'adventure', 'thriller', 'drama']:
                    base_weight *= 1.5

            # Add some randomization to avoid perfect patterns
            random_factor = random.uniform(0.8, 1.2)
            final_weight = base_weight * random_factor

            weighted_movies.append((movie, final_weight))

        # Select movie based on weights
        if weighted_movies:
            # Sort by weight and pick from top choices with some randomization
            weighted_movies.sort(key=lambda x: x[1], reverse=True)
            top_choices = weighted_movies[:max(3, len(weighted_movies) // 3)]
            return random.choice(top_choices)[0]

        return random.choice(movies)

    def _create_realistic_schedule(
        self,
        movie: Movie,
        cinema_info: Tuple[Cinema, CinemaType],
        time_slot: datetime,
        forecast: Forecast
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
        occupancy_goal = forecast.optimization_parameters.get("occupancy_goal", 0.7) if forecast.optimization_parameters else 0.7
        if occupancy_goal:
            # Adjust towards goal with some variance
            target_rate = occupancy_goal * random.uniform(0.8, 1.2)
            occupancy_rate = (occupancy_rate + target_rate) / 2
            occupancy_rate = max(0.1, min(0.9, occupancy_rate))  # Clamp between 10% and 90%

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
            status="active"
        )

    def _calculate_pricing(self, cinema_type: CinemaType, time_slot: datetime) -> float:
        """Calculate realistic pricing based on cinema type and time slot"""
        # Base price varies by time
        base_prices = {
            "morning": 8.50,    # 9 AM - 12 PM
            "afternoon": 10.00, # 12 PM - 6 PM
            "evening": 12.50,   # 6 PM - 11 PM
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

    def _apply_parameters(self, schedules: List[Schedule], parameters: Dict[str, Any]) -> List[Schedule]:
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

        # Additional parameter applications could be added here
        # For example: adjusting time slot distributions, cinema preferences, etc.

        return schedules

    def _validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize optimization parameters"""
        validated = {}

        # Validate revenue_goal (0.5 to 2.0 multiplier)
        if "revenue_goal" in parameters:
            revenue_goal = parameters["revenue_goal"]
            if isinstance(revenue_goal, (int, float)) and 0.5 <= revenue_goal <= 2.0:
                validated["revenue_goal"] = float(revenue_goal)
            else:
                logger.warning(f"Invalid revenue_goal {revenue_goal}, using default 1.0")
                validated["revenue_goal"] = 1.0

        # Validate occupancy_goal (0.3 to 0.9 target rate)
        if "occupancy_goal" in parameters:
            occupancy_goal = parameters["occupancy_goal"]
            if isinstance(occupancy_goal, (int, float)) and 0.3 <= occupancy_goal <= 0.9:
                validated["occupancy_goal"] = float(occupancy_goal)
            else:
                logger.warning(f"Invalid occupancy_goal {occupancy_goal}, using default 0.7")
                validated["occupancy_goal"] = 0.7

        # Validate movie_preferences (dict with movie_id -> weight 0.1-2.0)
        if "movie_preferences" in parameters:
            movie_prefs = parameters["movie_preferences"]
            if isinstance(movie_prefs, dict):
                validated_prefs = {}
                for movie_id, weight in movie_prefs.items():
                    if isinstance(weight, (int, float)) and 0.1 <= weight <= 2.0:
                        validated_prefs[str(movie_id)] = float(weight)
                    else:
                        logger.warning(f"Invalid weight {weight} for movie {movie_id}, skipping")
                validated["movie_preferences"] = validated_prefs

        return validated

# Global optimization service instance
optimization_service = OptimizationService()