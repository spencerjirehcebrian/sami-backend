from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.forecast_service import ForecastService
from app.exceptions import ValidationError, ResourceNotFoundError
from app.logging import get_logger, add_request_context
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

logger = get_logger(__name__)

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])


class ForecastCreate(BaseModel):
    date_range_start: str = Field(..., description="Start date for forecast (ISO format)")
    date_range_end: str = Field(..., description="End date for forecast (ISO format)")
    description: Optional[str] = Field(None, description="Optional description for the forecast")
    optimization_parameters: Optional[Dict[str, Any]] = Field(None, description="Optimization parameters")
    created_by: str = Field(default="user", description="Creator of the forecast")


class ForecastResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    date_range_start: str
    date_range_end: str
    status: str
    optimization_parameters: Optional[Dict[str, Any]]
    created_at: str
    created_by: str
    total_schedules_generated: int


class ForecastDetailResponse(ForecastResponse):
    actual_schedules_count: int
    has_predictions: bool
    prediction_data: Optional[Dict[str, Any]]


@router.get("", response_model=List[ForecastResponse])
async def get_all_forecasts(db: Session = Depends(get_db)):
    """Get all forecasts with basic details"""
    try:
        forecast_service = ForecastService(db)
        forecasts = await forecast_service.get_all_forecasts()
        return forecasts
    except Exception as e:
        logger.error(f"Error getting all forecasts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=Dict[str, Any])
async def create_forecast(
    forecast_data: ForecastCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new forecast and trigger schedule optimization"""
    request_logger = add_request_context(
        logger,
        request_id=getattr(request.state, 'request_id', 'unknown'),
        method=request.method,
        path=str(request.url.path),
        operation="create_forecast",
        date_range_start=forecast_data.date_range_start,
        date_range_end=forecast_data.date_range_end,
        created_by=forecast_data.created_by
    )
    request_logger.info("Processing forecast creation request")

    try:
        forecast_service = ForecastService(db)

        # Parse datetime strings
        try:
            date_start = datetime.fromisoformat(forecast_data.date_range_start.replace('Z', '+00:00'))
            date_end = datetime.fromisoformat(forecast_data.date_range_end.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)"
            )

        # Validate date range
        if date_start >= date_end:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before end date"
            )

        # Create forecast and generate complete optimization
        request_logger.info(
            "Starting forecast generation",
            date_range_days=(date_end - date_start).days + 1
        )

        result = await forecast_service.generate_complete_forecast(
            date_range_start=date_start,
            date_range_end=date_end,
            optimization_parameters=forecast_data.optimization_parameters,
            created_by=forecast_data.created_by,
            description=forecast_data.description
        )

        request_logger.info(
            "Forecast creation completed successfully",
            forecast_id=result.get("id"),
            forecast_name=result.get("name"),
            schedules_generated=result.get("total_schedules_generated", 0),
            status=result.get("status")
        )

        return result
    except HTTPException:
        raise
    except ValidationError as e:
        request_logger.warning(
            "Validation error in forecast creation",
            error=e.message,
            error_type="ValidationError"
        )
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        request_logger.warning(
            "Value validation error in forecast creation",
            error=str(e),
            error_type="ValueError"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        request_logger.error(
            "Unexpected error during forecast creation",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{forecast_id}", response_model=ForecastDetailResponse)
async def get_forecast_details(forecast_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific forecast"""
    try:
        forecast_service = ForecastService(db)
        forecast = await forecast_service.get_forecast_by_id(forecast_id)

        if not forecast:
            raise HTTPException(status_code=404, detail="Forecast not found")

        return forecast
    except HTTPException:
        raise
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in get_forecast_details: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error in get_forecast_details: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in get_forecast_details: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid forecast ID format: {e}")
    except Exception as e:
        logger.error(f"Error getting forecast {forecast_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{forecast_id}")
async def delete_forecast(forecast_id: str, db: Session = Depends(get_db)):
    """Delete a forecast and all associated schedules and predictions"""
    try:
        forecast_service = ForecastService(db)

        # Check if forecast exists first
        existing_forecast = await forecast_service.get_forecast_by_id(forecast_id)
        if not existing_forecast:
            raise HTTPException(status_code=404, detail="Forecast not found")

        result = await forecast_service.delete_forecast(forecast_id)
        return result
    except HTTPException:
        raise
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in delete_forecast: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in delete_forecast: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Error deleting forecast {forecast_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{forecast_id}/schedules", response_model=List[Dict[str, Any]])
async def get_forecast_schedules(
    forecast_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Number of schedules to return"),
    offset: int = Query(0, ge=0, description="Number of schedules to skip"),
    db: Session = Depends(get_db)
):
    """Get all schedules associated with a forecast"""
    try:
        forecast_service = ForecastService(db)

        # Verify forecast exists
        forecast = await forecast_service.get_forecast_by_id(forecast_id)
        if not forecast:
            raise HTTPException(status_code=404, detail="Forecast not found")

        schedules = await forecast_service.get_forecast_schedules(forecast_id)

        # Apply pagination
        total_count = len(schedules)
        paginated_schedules = schedules[offset:offset + limit]

        return {
            "data": paginated_schedules,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "forecast": {
                "id": forecast_id,
                "name": forecast["name"],
                "status": forecast["status"]
            }
        }
    except HTTPException:
        raise
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in get_forecast_schedules: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in get_forecast_schedules: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Error getting schedules for forecast {forecast_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{forecast_id}/predictions", response_model=Dict[str, Any])
async def get_forecast_predictions(forecast_id: str, db: Session = Depends(get_db)):
    """Get prediction data for a forecast"""
    try:
        forecast_service = ForecastService(db)

        # Verify forecast exists
        forecast = await forecast_service.get_forecast_by_id(forecast_id)
        if not forecast:
            raise HTTPException(status_code=404, detail="Forecast not found")

        predictions = await forecast_service.get_forecast_predictions(forecast_id)

        if not predictions:
            raise HTTPException(
                status_code=404,
                detail="Predictions not found for this forecast. The forecast may still be generating."
            )

        return predictions
    except HTTPException:
        raise
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in get_forecast_predictions: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in get_forecast_predictions: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Error getting predictions for forecast {forecast_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{forecast_id}/regenerate", response_model=Dict[str, Any])
async def regenerate_forecast(forecast_id: str, db: Session = Depends(get_db)):
    """Regenerate schedules and predictions for an existing forecast"""
    try:
        forecast_service = ForecastService(db)

        # Check if forecast exists first
        existing_forecast = await forecast_service.get_forecast_by_id(forecast_id)
        if not existing_forecast:
            raise HTTPException(status_code=404, detail="Forecast not found")

        # Check if forecast is not currently generating
        if existing_forecast["status"] == "generating":
            raise HTTPException(
                status_code=409,
                detail="Forecast is already generating. Please wait for completion before regenerating."
            )

        result = await forecast_service.regenerate_forecast(forecast_id)
        return result
    except HTTPException:
        raise
    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found in regenerate_forecast: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except ValueError as e:
        logger.warning(f"Validation error in regenerate_forecast: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Error regenerating forecast {forecast_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
