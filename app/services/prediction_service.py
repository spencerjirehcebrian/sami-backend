from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.schedule import Schedule
from app.models.forecast import Forecast, PredictionData
from app.models.movie import Movie
from app.models.cinema import Cinema
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class PredictionService:
    """Service class for generating predictions and metrics for forecasts"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def generate_predictions(self, forecast_id: str, schedules: List[Schedule]) -> PredictionData:
        """Main entry point for generating prediction data for a forecast"""
        try:
            logger.info(f"Generating predictions for forecast {forecast_id} with {len(schedules)} schedules")

            # Calculate various metrics
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
                    "error_margin_percent": int(error_margin * 100)
                }
            )

            # Create and save prediction data
            prediction_data = PredictionData(
                forecast_id=forecast_id,
                metrics=metrics_json,
                confidence_score=confidence_score,
                error_margin=error_margin
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
        """Calculate metrics about the schedule structure"""
        if not schedules:
            return {
                "shows": 0,
                "cinemas": 0,
                "days": 0,
                "movies": 0,
                "new_movies": 0,
                "efficiency_percent": 0,
                "cleanup_minutes": 0,
                "usable_minutes": 0
            }

        # Basic counts
        total_shows = len(schedules)
        unique_cinemas = len(set(schedule.cinema_id for schedule in schedules))
        unique_movies = len(set(schedule.movie_id for schedule in schedules))

        # Calculate date range
        time_slots = [schedule.time_slot for schedule in schedules]
        if time_slots:
            start_date = min(time_slots).date()
            end_date = max(time_slots).date()
            total_days = (end_date - start_date).days + 1
        else:
            total_days = 0

        # Simulate new movies count (assume 20-30% are "new releases")
        new_movies = int(unique_movies * random.uniform(0.2, 0.3))

        # Calculate efficiency metrics
        # This is a mock calculation - in real implementation would analyze
        # actual theater utilization patterns
        theoretical_max_shows = unique_cinemas * total_days * 28  # 28 shows per cinema per day (30min slots, 14 hours)
        efficiency_percent = int((total_shows / max(theoretical_max_shows, 1)) * 100) if theoretical_max_shows > 0 else 0

        # Mock cleanup and usable minutes
        # These would be calculated based on actual movie durations and transitions
        total_runtime_minutes = sum(self._estimate_movie_duration(schedule) for schedule in schedules)
        cleanup_minutes = total_shows * 15  # 15 min cleanup between shows
        usable_minutes = total_runtime_minutes

        return {
            "shows": total_shows,
            "cinemas": unique_cinemas,
            "days": total_days,
            "movies": unique_movies,
            "new_movies": new_movies,
            "efficiency_percent": min(efficiency_percent, 100),  # Cap at 100%
            "cleanup_minutes": cleanup_minutes,
            "usable_minutes": usable_minutes
        }

    def _calculate_occupancy_metrics(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate aggregated occupancy metrics"""
        if not schedules:
            return {"sold": 0, "total": 0, "percent": 0}

        total_seats_sold = sum(schedule.max_sales for schedule in schedules)
        total_seats_available = sum(self._get_cinema_capacity(schedule) for schedule in schedules)

        occupancy_percent = int((total_seats_sold / max(total_seats_available, 1)) * 100) if total_seats_available > 0 else 0

        return {
            "sold": total_seats_sold,
            "total": total_seats_available,
            "percent": occupancy_percent
        }

    def _calculate_revenue_metrics(self, schedules: List[Schedule]) -> float:
        """Calculate total projected revenue"""
        total_revenue = 0.0

        for schedule in schedules:
            # Revenue = (unit_price + service_fee) * max_sales
            ticket_revenue = (schedule.unit_price + schedule.service_fee) * schedule.max_sales
            total_revenue += ticket_revenue

        return round(total_revenue, 2)

    def _generate_confidence_score(self, schedules: List[Schedule]) -> float:
        """Generate a mock confidence score (70-85%)"""
        # In a real implementation, this would be based on:
        # - Historical accuracy of similar forecasts
        # - Data quality and completeness
        # - Market volatility factors
        # - Seasonal patterns

        base_confidence = 0.75  # 75% base confidence

        # Adjust based on schedule count (more data = higher confidence)
        schedule_factor = min(len(schedules) / 1000, 0.1)  # Up to 10% bonus for large datasets

        # Add some randomization
        random_factor = random.uniform(-0.05, 0.05)

        final_confidence = base_confidence + schedule_factor + random_factor
        return max(0.70, min(0.85, final_confidence))  # Clamp between 70% and 85%

    def _calculate_error_margin(self, schedules: List[Schedule]) -> float:
        """Calculate mock error margin (10-20%)"""
        # In a real implementation, this would be based on:
        # - Historical prediction accuracy
        # - Market volatility
        # - External factors (seasonality, competition, events)

        base_error = 0.15  # 15% base error margin

        # Adjust based on data quality (more schedules = lower error)
        data_quality_factor = max(0.05, 0.2 - (len(schedules) / 10000))  # Better quality with more data

        # Add some randomization
        random_factor = random.uniform(-0.02, 0.02)

        final_error = base_error + data_quality_factor + random_factor
        return max(0.10, min(0.20, final_error))  # Clamp between 10% and 20%

    def _format_metrics_json(
        self,
        schedule_metrics: Dict[str, Any],
        forecast_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format metrics into the standard JSON structure"""
        return {
            "schedule": schedule_metrics,
            "forecast": forecast_metrics
        }

    def _estimate_movie_duration(self, schedule: Schedule) -> int:
        """Estimate movie duration in minutes (mock implementation)"""
        # In real implementation, would query actual movie duration
        # For now, return typical durations based on random selection
        typical_durations = [90, 105, 120, 135, 150, 165, 180]
        return random.choice(typical_durations)

    def _get_cinema_capacity(self, schedule: Schedule) -> int:
        """Get the total seat capacity for a cinema (mock implementation)"""
        # In real implementation, would query actual cinema capacity
        # For now, estimate based on max_sales with some buffer
        return int(schedule.max_sales * random.uniform(1.3, 1.7))  # Assume max_sales is 60-75% of capacity

    async def get_prediction_summary(self, forecast_id: str) -> Dict[str, Any]:
        """Get a summary of prediction data for a forecast"""
        try:
            prediction = self.db.query(PredictionData).filter(PredictionData.forecast_id == forecast_id).first()
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
                    "occupancy_percent": prediction.metrics["forecast"]["occupancy"]["percent"],
                    "cinemas_utilized": prediction.metrics["schedule"]["cinemas"],
                    "movies_scheduled": prediction.metrics["schedule"]["movies"]
                },
                "created_at": prediction.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting prediction summary: {e}")
            raise

# Global prediction service instance
prediction_service = PredictionService()