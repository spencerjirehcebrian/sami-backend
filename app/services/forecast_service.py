from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.models.forecast import Forecast, PredictionData
from app.models.schedule import Schedule
from app.notifications.broadcaster import broadcaster
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ForecastService:
    """Service class for forecast management operations"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def create_forecast(
        self,
        date_range_start: datetime,
        date_range_end: datetime,
        optimization_parameters: Dict[str, Any] = None,
        created_by: str = "user",
        description: str = None
    ) -> Dict[str, Any]:
        """Create a new forecast with auto-generated name"""
        try:
            # Auto-generate name based on date range
            start_str = date_range_start.strftime('%Y-%m-%d')
            end_str = date_range_end.strftime('%Y-%m-%d')
            name = f"Forecast {start_str} to {end_str}"

            # Validate date range
            if date_range_start >= date_range_end:
                raise ValueError("Start date must be before end date")

            forecast = Forecast(
                name=name,
                description=description,
                date_range_start=date_range_start,
                date_range_end=date_range_end,
                status="generating",
                optimization_parameters=optimization_parameters,
                created_by=created_by,
                total_schedules_generated=0
            )

            self.db.add(forecast)
            self.db.commit()
            self.db.refresh(forecast)

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="forecasts",
                operation="create",
                entity_id=str(forecast.id),
                data={
                    "name": forecast.name,
                    "status": forecast.status,
                    "date_range_start": forecast.date_range_start.isoformat(),
                    "date_range_end": forecast.date_range_end.isoformat()
                }
            )

            return {
                "id": str(forecast.id),
                "name": forecast.name,
                "description": forecast.description,
                "date_range_start": forecast.date_range_start.isoformat(),
                "date_range_end": forecast.date_range_end.isoformat(),
                "status": forecast.status,
                "optimization_parameters": forecast.optimization_parameters,
                "created_at": forecast.created_at.isoformat(),
                "created_by": forecast.created_by,
                "total_schedules_generated": forecast.total_schedules_generated,
                "message": f"Forecast '{name}' created successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating forecast: {e}")
            raise

    async def get_all_forecasts(self) -> List[Dict[str, Any]]:
        """Get all forecasts with their basic details"""
        try:
            forecasts = self.db.query(Forecast).order_by(Forecast.created_at.desc()).all()
            return [
                {
                    "id": str(forecast.id),
                    "name": forecast.name,
                    "description": forecast.description,
                    "date_range_start": forecast.date_range_start.isoformat(),
                    "date_range_end": forecast.date_range_end.isoformat(),
                    "status": forecast.status,
                    "optimization_parameters": forecast.optimization_parameters,
                    "created_at": forecast.created_at.isoformat(),
                    "created_by": forecast.created_by,
                    "total_schedules_generated": forecast.total_schedules_generated
                }
                for forecast in forecasts
            ]
        except Exception as e:
            logger.error(f"Error getting all forecasts: {e}")
            raise

    async def get_forecast_by_id(self, forecast_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific forecast by ID with detailed information"""
        try:
            forecast = self.db.query(Forecast).filter(Forecast.id == forecast_id).first()
            if not forecast:
                return None

            # Get schedule count
            schedule_count = self.db.query(Schedule).filter(Schedule.forecast_id == forecast_id).count()

            # Get prediction data
            prediction = self.db.query(PredictionData).filter(PredictionData.forecast_id == forecast_id).first()

            return {
                "id": str(forecast.id),
                "name": forecast.name,
                "description": forecast.description,
                "date_range_start": forecast.date_range_start.isoformat(),
                "date_range_end": forecast.date_range_end.isoformat(),
                "status": forecast.status,
                "optimization_parameters": forecast.optimization_parameters,
                "created_at": forecast.created_at.isoformat(),
                "created_by": forecast.created_by,
                "total_schedules_generated": forecast.total_schedules_generated,
                "actual_schedules_count": schedule_count,
                "has_predictions": prediction is not None,
                "prediction_data": {
                    "metrics": prediction.metrics,
                    "confidence_score": prediction.confidence_score,
                    "error_margin": prediction.error_margin,
                    "created_at": prediction.created_at.isoformat()
                } if prediction else None
            }
        except Exception as e:
            logger.error(f"Error getting forecast by ID {forecast_id}: {e}")
            raise

    async def delete_forecast(self, forecast_id: str) -> Dict[str, Any]:
        """Delete a forecast and all associated schedules and predictions (cascade)"""
        try:
            forecast = self.db.query(Forecast).filter(Forecast.id == forecast_id).first()
            if not forecast:
                raise ValueError(f"Forecast with ID {forecast_id} not found")

            forecast_name = forecast.name
            schedule_count = self.db.query(Schedule).filter(Schedule.forecast_id == forecast_id).count()

            # Delete forecast (cascade will handle schedules and predictions)
            self.db.delete(forecast)
            self.db.commit()

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="forecasts",
                operation="delete",
                entity_id=forecast_id,
                data={
                    "name": forecast_name,
                    "schedules_deleted": schedule_count
                }
            )

            return {
                "id": forecast_id,
                "message": f"Forecast '{forecast_name}' and {schedule_count} schedules deleted successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting forecast: {e}")
            raise

    async def update_forecast_status(self, forecast_id: str, status: str) -> Dict[str, Any]:
        """Update the status of a forecast"""
        try:
            valid_statuses = ["generating", "completed", "failed"]
            if status not in valid_statuses:
                raise ValueError(f"Status must be one of: {valid_statuses}")

            forecast = self.db.query(Forecast).filter(Forecast.id == forecast_id).first()
            if not forecast:
                raise ValueError(f"Forecast with ID {forecast_id} not found")

            old_status = forecast.status
            forecast.status = status
            self.db.commit()
            self.db.refresh(forecast)

            # Trigger notification
            await broadcaster.broadcast_change(
                entity_type="forecasts",
                operation="update",
                entity_id=forecast_id,
                data={
                    "name": forecast.name,
                    "status": forecast.status,
                    "previous_status": old_status
                }
            )

            return {
                "id": str(forecast.id),
                "name": forecast.name,
                "status": forecast.status,
                "previous_status": old_status,
                "message": f"Forecast status updated from '{old_status}' to '{status}'"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating forecast status: {e}")
            raise

    async def get_forecast_schedules(self, forecast_id: str) -> List[Dict[str, Any]]:
        """Get all schedules associated with a forecast"""
        try:
            # Verify forecast exists
            forecast = self.db.query(Forecast).filter(Forecast.id == forecast_id).first()
            if not forecast:
                raise ValueError(f"Forecast with ID {forecast_id} not found")

            # Get schedules with movie and cinema details
            schedules = (
                self.db.query(Schedule)
                .filter(Schedule.forecast_id == forecast_id)
                .join(Schedule.movie)
                .join(Schedule.cinema)
                .order_by(Schedule.time_slot)
                .all()
            )

            return [
                {
                    "id": str(schedule.id),
                    "forecast_id": str(schedule.forecast_id),
                    "movie": {
                        "id": str(schedule.movie.id),
                        "title": schedule.movie.title,
                        "genre": schedule.movie.genre,
                        "duration": schedule.movie.duration
                    },
                    "cinema": {
                        "id": str(schedule.cinema.id),
                        "number": schedule.cinema.number,
                        "location": schedule.cinema.location,
                        "total_seats": schedule.cinema.total_seats
                    },
                    "time_slot": schedule.time_slot.isoformat(),
                    "unit_price": schedule.unit_price,
                    "service_fee": schedule.service_fee,
                    "max_sales": schedule.max_sales,
                    "current_sales": schedule.current_sales,
                    "status": schedule.status,
                    "created_at": schedule.created_at.isoformat()
                }
                for schedule in schedules
            ]
        except Exception as e:
            logger.error(f"Error getting forecast schedules: {e}")
            raise

    async def get_forecast_predictions(self, forecast_id: str) -> Optional[Dict[str, Any]]:
        """Get prediction data for a forecast"""
        try:
            # Verify forecast exists
            forecast = self.db.query(Forecast).filter(Forecast.id == forecast_id).first()
            if not forecast:
                raise ValueError(f"Forecast with ID {forecast_id} not found")

            prediction = self.db.query(PredictionData).filter(PredictionData.forecast_id == forecast_id).first()
            if not prediction:
                return None

            return {
                "id": str(prediction.id),
                "forecast_id": str(prediction.forecast_id),
                "metrics": prediction.metrics,
                "confidence_score": prediction.confidence_score,
                "error_margin": prediction.error_margin,
                "created_at": prediction.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting forecast predictions: {e}")
            raise

    async def update_total_schedules_generated(self, forecast_id: str, count: int) -> None:
        """Update the total schedules generated count for a forecast"""
        try:
            forecast = self.db.query(Forecast).filter(Forecast.id == forecast_id).first()
            if forecast:
                forecast.total_schedules_generated = count
                self.db.commit()
        except Exception as e:
            logger.error(f"Error updating schedules count: {e}")
            raise

    async def generate_complete_forecast(
        self,
        date_range_start: datetime,
        date_range_end: datetime,
        optimization_parameters: Dict[str, Any] = None,
        created_by: str = "user",
        description: str = None
    ) -> Dict[str, Any]:
        """Create forecast and generate schedules and predictions in one operation"""
        try:
            logger.info(f"Starting complete forecast generation from {date_range_start} to {date_range_end}")

            # Step 1: Create basic forecast
            forecast_data = await self.create_forecast(
                date_range_start=date_range_start,
                date_range_end=date_range_end,
                optimization_parameters=optimization_parameters,
                created_by=created_by,
                description=description
            )

            forecast_id = forecast_data["id"]
            forecast = self.db.query(Forecast).filter(Forecast.id == forecast_id).first()

            try:
                # Try to import and use AI services
                try:
                    from .optimization_service import optimization_service
                    from .prediction_service import prediction_service

                    # Step 2: Generate schedules using optimization service
                    schedules = await optimization_service.generate_schedules_for_forecast(forecast)

                    # Update the forecast with actual schedule count
                    await self.update_total_schedules_generated(forecast_id, len(schedules))

                    # Step 3: Generate predictions using prediction service
                    prediction_data = await prediction_service.generate_predictions(forecast_id, schedules)

                    # Step 4: Update status to completed
                    await self.update_forecast_status(forecast_id, "completed")

                    logger.info(f"Complete forecast generation successful for {forecast_id}")
                    return {
                        "id": forecast_id,
                        "name": forecast.name,
                        "description": forecast.description,
                        "date_range_start": forecast.date_range_start.isoformat(),
                        "date_range_end": forecast.date_range_end.isoformat(),
                        "status": "completed",
                        "optimization_parameters": forecast.optimization_parameters,
                        "created_at": forecast.created_at.isoformat(),
                        "created_by": forecast.created_by,
                        "total_schedules_generated": len(schedules),
                        "message": f"Forecast generated successfully with {len(schedules)} schedules"
                    }

                except (ImportError, ModuleNotFoundError, AttributeError) as import_error:
                    # AI services not available - create basic forecast without optimization
                    logger.warning(f"AI services not available, creating basic forecast: {import_error}")

                    # Update status to completed (basic forecast)
                    await self.update_forecast_status(forecast_id, "completed")

                    return {
                        "id": forecast_id,
                        "name": forecast.name,
                        "description": forecast.description,
                        "date_range_start": forecast.date_range_start.isoformat(),
                        "date_range_end": forecast.date_range_end.isoformat(),
                        "status": "completed",
                        "optimization_parameters": forecast.optimization_parameters,
                        "created_at": forecast.created_at.isoformat(),
                        "created_by": forecast.created_by,
                        "total_schedules_generated": 0,
                        "message": "Basic forecast created successfully (AI optimization unavailable)"
                    }

            except Exception as generation_error:
                # Mark forecast as failed and provide fallback response
                await self.update_forecast_status(forecast_id, "failed")
                logger.error(f"Forecast generation failed: {generation_error}")

                # Return the basic forecast data even if processing failed
                return {
                    "id": forecast_id,
                    "name": forecast.name,
                    "description": forecast.description,
                    "date_range_start": forecast.date_range_start.isoformat(),
                    "date_range_end": forecast.date_range_end.isoformat(),
                    "status": "failed",
                    "optimization_parameters": forecast.optimization_parameters,
                    "created_at": forecast.created_at.isoformat(),
                    "created_by": forecast.created_by,
                    "total_schedules_generated": 0,
                    "message": f"Forecast created but processing failed: {str(generation_error)}"
                }

        except Exception as e:
            logger.error(f"Error in complete forecast generation: {e}")
            raise

    async def regenerate_forecast(self, forecast_id: str) -> Dict[str, Any]:
        """Regenerate schedules and predictions for an existing forecast"""
        try:
            # Import here to avoid circular imports
            from .optimization_service import optimization_service
            from .prediction_service import prediction_service

            forecast = self.db.query(Forecast).filter(Forecast.id == forecast_id).first()
            if not forecast:
                raise ValueError(f"Forecast with ID {forecast_id} not found")

            logger.info(f"Regenerating forecast {forecast_id}")

            # Set status to generating
            await self.update_forecast_status(forecast_id, "generating")

            try:
                # Delete existing schedules and predictions (cascade will handle this)
                existing_schedules = self.db.query(Schedule).filter(Schedule.forecast_id == forecast_id).all()
                for schedule in existing_schedules:
                    self.db.delete(schedule)

                existing_predictions = self.db.query(PredictionData).filter(PredictionData.forecast_id == forecast_id).all()
                for prediction in existing_predictions:
                    self.db.delete(prediction)

                self.db.commit()

                # Generate new schedules and predictions
                schedules = await optimization_service.generate_schedules_for_forecast(forecast)
                await self.update_total_schedules_generated(forecast_id, len(schedules))

                prediction_data = await prediction_service.generate_predictions(forecast_id, schedules)

                # Update status to completed
                await self.update_forecast_status(forecast_id, "completed")

                return {
                    "forecast_id": forecast_id,
                    "schedules_generated": len(schedules),
                    "predictions": {
                        "confidence_score": prediction_data.confidence_score,
                        "error_margin": prediction_data.error_margin
                    },
                    "message": f"Forecast regenerated successfully with {len(schedules)} schedules"
                }

            except Exception as generation_error:
                await self.update_forecast_status(forecast_id, "failed")
                logger.error(f"Forecast regeneration failed: {generation_error}")
                raise

        except Exception as e:
            logger.error(f"Error regenerating forecast: {e}")
            raise

# Global forecast service instance
forecast_service = ForecastService()