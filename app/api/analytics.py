from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import AnalyticsService
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/revenue", response_model=Dict[str, Any])
async def get_revenue_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    cinema_number: Optional[int] = Query(None, description="Filter by cinema number"),
    movie_id: Optional[str] = Query(None, description="Filter by movie ID"),
    breakdown: Optional[str] = Query("daily", description="Breakdown type: daily, cinema, movie"),
    db: Session = Depends(get_db)
):
    """Get revenue reports with various breakdowns and filters"""
    try:
        analytics_service = AnalyticsService(db)

        # Validate date formats if provided
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")

        # Build filter parameters
        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if cinema_number:
            filters["cinema_number"] = cinema_number
        if movie_id:
            filters["movie_id"] = movie_id

        # Map API parameters to service parameters
        service_params = {}
        if start_date:
            service_params["date_from"] = start_date
        if end_date:
            service_params["date_to"] = end_date
        if cinema_number:
            # Need to map cinema_number to cinema_id - this requires a lookup
            pass  # For now, skip this mapping
        if movie_id:
            service_params["movie_id"] = movie_id

        return await analytics_service.get_revenue_report(**service_params)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revenue report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/occupancy", response_model=Dict[str, Any])
async def get_occupancy_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    cinema_number: Optional[int] = Query(None, description="Filter by cinema number"),
    movie_id: Optional[str] = Query(None, description="Filter by movie ID"),
    db: Session = Depends(get_db)
):
    """Get occupancy analysis reports"""
    try:
        analytics_service = AnalyticsService(db)

        # Validate date formats if provided
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")

        # Build filter parameters
        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if cinema_number:
            filters["cinema_number"] = cinema_number
        if movie_id:
            filters["movie_id"] = movie_id

        return await analytics_service.get_occupancy_report(**filters)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting occupancy report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/movies/performance", response_model=Dict[str, Any])
async def get_movie_performance(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    movie_id: Optional[str] = Query(None, description="Specific movie ID"),
    limit: Optional[int] = Query(10, description="Number of top movies to return"),
    db: Session = Depends(get_db)
):
    """Get movie performance analytics"""
    try:
        analytics_service = AnalyticsService(db)

        # Validate date formats if provided
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")

        # Build filter parameters
        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if movie_id:
            filters["movie_id"] = movie_id
        if limit:
            filters["limit"] = limit

        return await analytics_service.get_movie_performance(**filters)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting movie performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/daily-summary", response_model=Dict[str, Any])
async def get_daily_summary(
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db)
):
    """Get comprehensive daily summary"""
    try:
        analytics_service = AnalyticsService(db)

        # Use today if no date provided
        if not target_date:
            target_date = date.today().strftime("%Y-%m-%d")
        else:
            # Validate date format
            try:
                datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid target_date format. Use YYYY-MM-DD.")

        return await analytics_service.get_daily_summary(target_date)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily summary for {target_date}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trends/revenue")
async def get_revenue_trends(
    period: str = Query("week", description="Trend period: week, month, quarter"),
    cinema_number: Optional[int] = Query(None, description="Filter by cinema number"),
    db: Session = Depends(get_db)
):
    """Get revenue trend analysis"""
    try:
        analytics_service = AnalyticsService(db)

        if period not in ["week", "month", "quarter"]:
            raise HTTPException(status_code=400, detail="Period must be 'week', 'month', or 'quarter'")

        # Calculate date range based on period
        today = date.today()
        if period == "week":
            days_back = 7
        elif period == "month":
            days_back = 30
        else:  # quarter
            days_back = 90

        from datetime import timedelta
        start_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        filters = {
            "start_date": start_date,
            "end_date": end_date
        }
        if cinema_number:
            filters["cinema_number"] = cinema_number

        service_params = {}
        if start_date:
            service_params["date_from"] = start_date
        if end_date:
            service_params["date_to"] = end_date
        if cinema_number:
            # Skip cinema mapping for now
            pass

        return await analytics_service.get_revenue_report(**service_params)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revenue trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trends/occupancy")
async def get_occupancy_trends(
    period: str = Query("week", description="Trend period: week, month, quarter"),
    cinema_number: Optional[int] = Query(None, description="Filter by cinema number"),
    db: Session = Depends(get_db)
):
    """Get occupancy trend analysis"""
    try:
        analytics_service = AnalyticsService(db)

        if period not in ["week", "month", "quarter"]:
            raise HTTPException(status_code=400, detail="Period must be 'week', 'month', or 'quarter'")

        # Calculate date range based on period
        today = date.today()
        if period == "week":
            days_back = 7
        elif period == "month":
            days_back = 30
        else:  # quarter
            days_back = 90

        from datetime import timedelta
        start_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        filters = {
            "start_date": start_date,
            "end_date": end_date
        }
        if cinema_number:
            filters["cinema_number"] = cinema_number

        return await analytics_service.get_occupancy_report(**filters)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting occupancy trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/summary/overview")
async def get_analytics_overview(db: Session = Depends(get_db)):
    """Get high-level analytics overview"""
    try:
        analytics_service = AnalyticsService(db)

        # Get today's summary
        today = date.today().strftime("%Y-%m-%d")
        daily_summary = await analytics_service.get_daily_summary(today)

        # Get this week's revenue
        from datetime import timedelta
        week_ago = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_revenue = await analytics_service.get_revenue_report(
            breakdown="daily",
            start_date=week_ago,
            end_date=today
        )

        # Get movie performance
        movie_performance = await analytics_service.get_movie_performance(limit=5)

        return {
            "overview": {
                "daily_summary": daily_summary,
                "weekly_revenue": week_revenue,
                "top_movies": movie_performance,
                "generated_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")