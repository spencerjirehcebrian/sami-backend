from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.schedule import Schedule
from app.models.forecast import Forecast, PredictionData
from app.models.movie import Movie
from app.models.cinema import Cinema
from app.logging import get_logger, add_service_context
from datetime import datetime, timedelta
import random

logger = get_logger(__name__)


class PredictionService:
    """Service class for generating predictions and metrics for forecasts"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def generate_predictions(
        self, forecast_id: str, schedules: List[Schedule]
    ) -> PredictionData:
        """Main entry point for generating prediction data for a forecast"""
        service_logger = add_service_context(
            logger, "prediction_service", "generate_predictions",
            forecast_id=forecast_id,
            schedules_count=len(schedules)
        )
        service_logger.info("Starting prediction generation for forecast")

        try:

            # Calculate simplified metrics for faster processing
            schedule_metrics = self._calculate_schedule_metrics(schedules)
            occupancy_metrics = self._calculate_occupancy_metrics(schedules)
            revenue_metrics = self._calculate_revenue_metrics(schedules)

            # Generate confidence and error metrics
            confidence_score = self._generate_confidence_score(schedules)
            error_margin = self._calculate_error_margin(schedules)

            # Format metrics into structured JSON
            metrics_json = self._format_metrics_json(
                schedule_metrics,
                {
                    "occupancy": occupancy_metrics,
                    "revenue": revenue_metrics,
                    "confidence_percent": int(confidence_score * 100),
                    "error_margin_percent": int(error_margin * 100),
                },
            )

            # Create and save prediction data
            prediction_data = PredictionData(
                forecast_id=forecast_id,
                metrics=metrics_json,
                confidence_score=confidence_score,
                error_margin=error_margin,
            )

            self.db.add(prediction_data)
            self.db.commit()
            self.db.refresh(prediction_data)

            logger.info(f"Created prediction data for forecast {forecast_id}")
            return prediction_data

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating predictions: {e}")
            raise

    def _calculate_schedule_metrics(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate simplified metrics about the schedule structure"""
        if not schedules:
            return {
                "shows": 0,
                "cinemas": 0,
                "days": 0,
                "movies": 0,
                "new_movies": 0,
                "efficiency_percent": 0,
                "average_shows_per_day": 0.0,
                "peak_day_shows": 0,
            }

        # Basic counts using set comprehensions for efficiency
        total_shows = len(schedules)
        unique_cinemas = len(set(schedule.cinema_id for schedule in schedules))
        unique_movies = len(set(schedule.movie_id for schedule in schedules))

        # Calculate date range efficiently
        time_slots = [schedule.time_slot for schedule in schedules]
        if time_slots:
            start_date = min(time_slots).date()
            end_date = max(time_slots).date()
            total_days = (end_date - start_date).days + 1

            # Calculate shows per day distribution
            shows_by_day = {}
            for schedule in schedules:
                day = schedule.time_slot.date()
                shows_by_day[day] = shows_by_day.get(day, 0) + 1

            average_shows_per_day = total_shows / total_days if total_days > 0 else 0
            peak_day_shows = max(shows_by_day.values()) if shows_by_day else 0
        else:
            total_days = 0
            average_shows_per_day = 0.0
            peak_day_shows = 0

        # Simulate new movies count (assume 20-30% are "new releases")
        new_movies = max(1, int(unique_movies * random.uniform(0.2, 0.3)))

        # Simplified efficiency calculation
        if unique_cinemas > 0 and total_days > 0:
            # Assume maximum realistic capacity is 4 shows per cinema per day
            theoretical_max_shows = unique_cinemas * total_days * 4
            efficiency_percent = min(
                int((total_shows / theoretical_max_shows) * 100), 100
            )
        else:
            efficiency_percent = 0

        return {
            "shows": total_shows,
            "cinemas": unique_cinemas,
            "days": total_days,
            "movies": unique_movies,
            "new_movies": new_movies,
            "efficiency_percent": efficiency_percent,
            "average_shows_per_day": round(average_shows_per_day, 1),
            "peak_day_shows": peak_day_shows,
        }

    def _calculate_occupancy_metrics(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate aggregated occupancy metrics"""
        if not schedules:
            return {"sold": 0, "total": 0, "percent": 0}

        total_seats_sold = sum(schedule.max_sales for schedule in schedules)

        # Estimate total capacity based on typical cinema sizes
        # This is simplified - in reality you'd query actual cinema capacities
        estimated_total_capacity = 0
        for schedule in schedules:
            # Estimate cinema capacity as max_sales / occupancy_rate
            # Assume average occupancy rate used in generation was ~65%
            estimated_capacity = int(schedule.max_sales / 0.65)
            estimated_total_capacity += estimated_capacity

        occupancy_percent = (
            int((total_seats_sold / max(estimated_total_capacity, 1)) * 100)
            if estimated_total_capacity > 0
            else 0
        )

        return {
            "sold": total_seats_sold,
            "total": estimated_total_capacity,
            "percent": min(occupancy_percent, 100),  # Cap at 100%
        }

    def _calculate_revenue_metrics(self, schedules: List[Schedule]) -> float:
        """Calculate total projected revenue"""
        if not schedules:
            return 0.0

        total_revenue = 0.0
        for schedule in schedules:
            # Revenue = (unit_price + service_fee) * max_sales
            ticket_revenue = (
                schedule.unit_price + schedule.service_fee
            ) * schedule.max_sales
            total_revenue += ticket_revenue

        return round(total_revenue, 2)

    def _generate_confidence_score(self, schedules: List[Schedule]) -> float:
        """Generate a confidence score based on schedule data quality"""
        if not schedules:
            return 0.5  # 50% confidence for empty schedules

        base_confidence = 0.75  # 75% base confidence

        # Adjust based on schedule count (more data = higher confidence, but with diminishing returns)
        schedule_count = len(schedules)
        if schedule_count < 50:
            schedule_factor = -0.1  # Lower confidence for very few schedules
        elif schedule_count > 500:
            schedule_factor = 0.05  # Slight boost for large datasets
        else:
            schedule_factor = 0.0  # Normal confidence for typical datasets

        # Adjust based on schedule distribution (more even distribution = higher confidence)
        time_slots = [schedule.time_slot for schedule in schedules]
        if len(time_slots) > 1:
            # Simple measure of distribution: check if schedules span multiple days
            dates = set(dt.date() for dt in time_slots)
            if len(dates) > 1:
                distribution_factor = 0.05  # Boost for multi-day schedules
            else:
                distribution_factor = -0.05  # Lower for single-day schedules
        else:
            distribution_factor = -0.1

        # Add controlled randomization
        random_factor = random.uniform(-0.03, 0.03)

        final_confidence = (
            base_confidence + schedule_factor + distribution_factor + random_factor
        )
        return max(0.60, min(0.90, final_confidence))  # Clamp between 60% and 90%

    def _calculate_error_margin(self, schedules: List[Schedule]) -> float:
        """Calculate error margin inversely related to confidence"""
        if not schedules:
            return 0.25  # 25% error margin for empty schedules

        base_error = 0.15  # 15% base error margin

        # Adjust based on data size (more data = lower error)
        schedule_count = len(schedules)
        if schedule_count < 50:
            size_factor = 0.08  # Higher error for small datasets
        elif schedule_count > 500:
            size_factor = -0.03  # Lower error for large datasets
        else:
            size_factor = 0.0

        # Add controlled randomization
        random_factor = random.uniform(-0.02, 0.02)

        final_error = base_error + size_factor + random_factor
        return max(0.08, min(0.25, final_error))  # Clamp between 8% and 25%

    def _format_metrics_json(
        self, schedule_metrics: Dict[str, Any], forecast_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format metrics into the standard JSON structure"""
        return {
            "schedule": schedule_metrics,
            "forecast": forecast_metrics,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics_version": "1.0",
        }

    async def get_prediction_summary(self, forecast_id: str) -> Dict[str, Any]:
        """Get a summary of prediction data for a forecast"""
        try:
            prediction = (
                self.db.query(PredictionData)
                .filter(PredictionData.forecast_id == forecast_id)
                .first()
            )
            if not prediction:
                return None

            return {
                "forecast_id": forecast_id,
                "confidence_score": prediction.confidence_score,
                "confidence_percent": int(prediction.confidence_score * 100),
                "error_margin": prediction.error_margin,
                "error_margin_percent": int(prediction.error_margin * 100),
                "key_metrics": {
                    "total_shows": prediction.metrics["schedule"]["shows"],
                    "total_revenue": prediction.metrics["forecast"]["revenue"],
                    "occupancy_percent": prediction.metrics["forecast"]["occupancy"][
                        "percent"
                    ],
                    "cinemas_utilized": prediction.metrics["schedule"]["cinemas"],
                    "movies_scheduled": prediction.metrics["schedule"]["movies"],
                    "average_shows_per_day": prediction.metrics["schedule"].get(
                        "average_shows_per_day", 0
                    ),
                    "efficiency_percent": prediction.metrics["schedule"][
                        "efficiency_percent"
                    ],
                },
                "created_at": prediction.created_at.isoformat(),
                "quality_indicators": {
                    "confidence_level": (
                        "high"
                        if prediction.confidence_score > 0.8
                        else "medium" if prediction.confidence_score > 0.65 else "low"
                    ),
                    "error_level": (
                        "low"
                        if prediction.error_margin < 0.12
                        else "medium" if prediction.error_margin < 0.20 else "high"
                    ),
                    "data_size": prediction.metrics["schedule"]["shows"],
                },
            }
        except Exception as e:
            logger.error(f"Error getting prediction summary: {e}")
            raise


# Global prediction service instance
prediction_service = PredictionService()
