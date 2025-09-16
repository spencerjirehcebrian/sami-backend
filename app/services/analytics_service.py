from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from app.database import get_db
from app.models.schedule import Schedule
from app.models.movie import Movie
from app.models.cinema import Cinema, CinemaType
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service class for analytics and reporting operations"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def get_revenue_report(
        self,
        date_from: str = None,
        date_to: str = None,
        cinema_id: str = None,
        movie_id: str = None
    ) -> Dict[str, Any]:
        """Generate revenue report with SQL aggregations for optimal performance"""
        try:
            # Parse and validate date filters
            if date_from:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            else:
                # Default to last 30 days
                date_from_parsed = datetime.now() - timedelta(days=30)

            if date_to:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            else:
                date_to_parsed = datetime.now()

            # Build base filter conditions for reuse
            filter_conditions = [
                Schedule.time_slot >= date_from_parsed,
                Schedule.time_slot <= date_to_parsed
            ]

            if cinema_id:
                filter_conditions.append(Schedule.cinema_id == cinema_id)
            if movie_id:
                filter_conditions.append(Schedule.movie_id == movie_id)

            # Overall summary with SQL aggregations
            summary_query = self.db.query(
                func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('total_revenue'),
                func.sum(Schedule.current_sales).label('total_tickets_sold'),
                func.sum(Schedule.max_sales).label('total_possible_tickets'),
                func.count(Schedule.id).label('total_showings')
            ).filter(and_(*filter_conditions))

            summary_result = summary_query.first()

            total_revenue = float(summary_result.total_revenue or 0)
            total_tickets_sold = int(summary_result.total_tickets_sold or 0)
            total_possible_tickets = int(summary_result.total_possible_tickets or 0)
            total_showings = int(summary_result.total_showings or 0)

            # Cinema breakdown with SQL GROUP BY
            cinema_breakdown = self.db.query(
                Cinema.id.label('cinema_id'),
                Cinema.number.label('cinema_number'),
                func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('revenue'),
                func.sum(Schedule.current_sales).label('tickets_sold')
            ).join(Schedule).filter(and_(*filter_conditions)).group_by(
                Cinema.id, Cinema.number
            ).order_by(func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).desc()).all()

            # Movie breakdown with SQL GROUP BY
            movie_breakdown = self.db.query(
                Movie.id.label('movie_id'),
                Movie.title.label('title'),
                Movie.genre.label('genre'),
                func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('revenue'),
                func.sum(Schedule.current_sales).label('tickets_sold'),
                func.count(Schedule.id).label('showings')
            ).join(Schedule).filter(and_(*filter_conditions)).group_by(
                Movie.id, Movie.title, Movie.genre
            ).order_by(func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).desc()).all()

            # Daily breakdown with SQL GROUP BY using date functions
            daily_breakdown = self.db.query(
                func.date(Schedule.time_slot).label('date'),
                func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('revenue'),
                func.sum(Schedule.current_sales).label('tickets_sold'),
                func.count(Schedule.id).label('showings')
            ).filter(and_(*filter_conditions)).group_by(
                func.date(Schedule.time_slot)
            ).order_by(func.date(Schedule.time_slot)).all()

            # Format results
            cinema_breakdown_formatted = [
                {
                    "cinema_id": str(row.cinema_id),
                    "cinema_number": row.cinema_number,
                    "revenue": round(float(row.revenue or 0), 2),
                    "tickets_sold": int(row.tickets_sold or 0)
                }
                for row in cinema_breakdown
            ]

            movie_breakdown_formatted = [
                {
                    "movie_id": str(row.movie_id),
                    "title": row.title,
                    "genre": row.genre,
                    "revenue": round(float(row.revenue or 0), 2),
                    "tickets_sold": int(row.tickets_sold or 0),
                    "showings": int(row.showings or 0)
                }
                for row in movie_breakdown
            ]

            daily_breakdown_formatted = [
                {
                    "date": row.date.isoformat() if row.date else None,
                    "revenue": round(float(row.revenue or 0), 2),
                    "tickets_sold": int(row.tickets_sold or 0),
                    "showings": int(row.showings or 0)
                }
                for row in daily_breakdown
            ]

            return {
                "period": {
                    "from": date_from_parsed.isoformat(),
                    "to": date_to_parsed.isoformat()
                },
                "summary": {
                    "total_revenue": round(total_revenue, 2),
                    "total_tickets_sold": total_tickets_sold,
                    "total_possible_tickets": total_possible_tickets,
                    "overall_occupancy_rate": round((total_tickets_sold / total_possible_tickets) * 100, 2) if total_possible_tickets > 0 else 0,
                    "average_ticket_price": round(total_revenue / total_tickets_sold, 2) if total_tickets_sold > 0 else 0,
                    "total_showings": total_showings
                },
                "cinema_breakdown": cinema_breakdown_formatted,
                "movie_breakdown": movie_breakdown_formatted,
                "daily_breakdown": daily_breakdown_formatted
            }
        except Exception as e:
            logger.error(f"Error generating revenue report: {e}")
            raise

    async def get_occupancy_report(
        self,
        date_from: str = None,
        date_to: str = None
    ) -> Dict[str, Any]:
        """Generate occupancy analysis report using SQL aggregations"""
        try:
            # Parse date filters
            if date_from:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            else:
                date_from_parsed = datetime.now() - timedelta(days=30)

            if date_to:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            else:
                date_to_parsed = datetime.now()

            # Base filter conditions
            filter_conditions = [
                Schedule.time_slot >= date_from_parsed,
                Schedule.time_slot <= date_to_parsed
            ]

            # Overall occupancy stats with SQL aggregations
            overall_stats = self.db.query(
                func.sum(Schedule.max_sales).label('total_capacity'),
                func.sum(Schedule.current_sales).label('total_sold'),
                func.count(Schedule.id).label('total_showings')
            ).filter(and_(*filter_conditions)).first()

            total_capacity = int(overall_stats.total_capacity or 0)
            total_sold = int(overall_stats.total_sold or 0)
            total_showings = int(overall_stats.total_showings or 0)
            overall_occupancy = (total_sold / total_capacity) * 100 if total_capacity > 0 else 0

            # Cinema occupancy with SQL GROUP BY
            cinema_occupancy = self.db.query(
                Cinema.id.label('cinema_id'),
                Cinema.number.label('cinema_number'),
                func.sum(Schedule.max_sales).label('total_capacity'),
                func.sum(Schedule.current_sales).label('total_sold'),
                func.count(Schedule.id).label('showings')
            ).join(Schedule).filter(and_(*filter_conditions)).group_by(
                Cinema.id, Cinema.number
            ).all()

            # Format cinema occupancy with calculated rates
            cinema_occupancy_formatted = []
            for row in cinema_occupancy:
                capacity = int(row.total_capacity or 0)
                sold = int(row.total_sold or 0)
                occupancy_rate = round((sold / capacity) * 100, 2) if capacity > 0 else 0

                cinema_occupancy_formatted.append({
                    "cinema_id": str(row.cinema_id),
                    "cinema_number": row.cinema_number,
                    "total_capacity": capacity,
                    "total_sold": sold,
                    "showings": int(row.showings or 0),
                    "occupancy_rate": occupancy_rate
                })

            # Sort by occupancy rate
            cinema_occupancy_formatted.sort(key=lambda x: x["occupancy_rate"], reverse=True)

            # Hourly occupancy with SQL GROUP BY using EXTRACT
            hourly_occupancy = self.db.query(
                func.extract('hour', Schedule.time_slot).label('hour'),
                func.sum(Schedule.max_sales).label('total_capacity'),
                func.sum(Schedule.current_sales).label('total_sold'),
                func.count(Schedule.id).label('showings')
            ).filter(and_(*filter_conditions)).group_by(
                func.extract('hour', Schedule.time_slot)
            ).order_by(func.extract('hour', Schedule.time_slot)).all()

            # Format hourly occupancy
            hourly_occupancy_formatted = []
            for row in hourly_occupancy:
                hour = int(row.hour)
                capacity = int(row.total_capacity or 0)
                sold = int(row.total_sold or 0)
                occupancy_rate = round((sold / capacity) * 100, 2) if capacity > 0 else 0

                hourly_occupancy_formatted.append({
                    "hour": f"{hour:02d}:00",
                    "total_capacity": capacity,
                    "total_sold": sold,
                    "showings": int(row.showings or 0),
                    "occupancy_rate": occupancy_rate
                })

            # Weekday occupancy with SQL GROUP BY using date functions
            weekday_occupancy = self.db.query(
                func.extract('dow', Schedule.time_slot).label('day_of_week'),
                func.sum(Schedule.max_sales).label('total_capacity'),
                func.sum(Schedule.current_sales).label('total_sold'),
                func.count(Schedule.id).label('showings')
            ).filter(and_(*filter_conditions)).group_by(
                func.extract('dow', Schedule.time_slot)
            ).order_by(func.extract('dow', Schedule.time_slot)).all()

            # Format weekday occupancy with day names
            weekday_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            weekday_occupancy_formatted = []
            for row in weekday_occupancy:
                day_num = int(row.day_of_week)
                day_name = weekday_names[day_num]
                capacity = int(row.total_capacity or 0)
                sold = int(row.total_sold or 0)
                occupancy_rate = round((sold / capacity) * 100, 2) if capacity > 0 else 0

                weekday_occupancy_formatted.append({
                    "day": day_name,
                    "total_capacity": capacity,
                    "total_sold": sold,
                    "showings": int(row.showings or 0),
                    "occupancy_rate": occupancy_rate
                })

            return {
                "period": {
                    "from": date_from_parsed.isoformat(),
                    "to": date_to_parsed.isoformat()
                },
                "overall_occupancy": {
                    "rate": round(overall_occupancy, 2),
                    "total_capacity": total_capacity,
                    "total_sold": total_sold,
                    "total_showings": total_showings
                },
                "cinema_occupancy": cinema_occupancy_formatted,
                "hourly_occupancy": hourly_occupancy_formatted,
                "weekday_occupancy": weekday_occupancy_formatted
            }
        except Exception as e:
            logger.error(f"Error generating occupancy report: {e}")
            raise

    async def get_movie_performance(
        self,
        date_from: str = None,
        date_to: str = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get top performing movies analysis using SQL aggregations and rankings"""
        try:
            # Parse date filters
            if date_from:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            else:
                date_from_parsed = datetime.now() - timedelta(days=30)

            if date_to:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            else:
                date_to_parsed = datetime.now()

            # Base filter conditions
            filter_conditions = [
                Schedule.time_slot >= date_from_parsed,
                Schedule.time_slot <= date_to_parsed
            ]

            # Movie performance aggregation with SQL GROUP BY
            movie_performance_query = self.db.query(
                Movie.id.label('movie_id'),
                Movie.title.label('title'),
                Movie.genre.label('genre'),
                Movie.rating.label('rating'),
                Movie.duration.label('duration'),
                func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('total_revenue'),
                func.sum(Schedule.current_sales).label('total_tickets_sold'),
                func.sum(Schedule.max_sales).label('total_capacity'),
                func.count(Schedule.id).label('showings')
            ).join(Schedule).filter(and_(*filter_conditions)).group_by(
                Movie.id, Movie.title, Movie.genre, Movie.rating, Movie.duration
            )

            # Get all movie performance data
            movie_performance_data = movie_performance_query.all()

            # Format with calculated metrics
            all_movies = []
            for row in movie_performance_data:
                total_revenue = float(row.total_revenue or 0)
                total_tickets = int(row.total_tickets_sold or 0)
                total_capacity = int(row.total_capacity or 0)
                showings = int(row.showings or 0)

                occupancy_rate = round((total_tickets / total_capacity) * 100, 2) if total_capacity > 0 else 0
                average_price = round(total_revenue / total_tickets, 2) if total_tickets > 0 else 0

                movie_data = {
                    "movie_id": str(row.movie_id),
                    "title": row.title,
                    "genre": row.genre,
                    "rating": row.rating,
                    "duration": row.duration,
                    "total_revenue": round(total_revenue, 2),
                    "total_tickets_sold": total_tickets,
                    "total_capacity": total_capacity,
                    "showings": showings,
                    "average_price": average_price,
                    "occupancy_rate": occupancy_rate
                }
                all_movies.append(movie_data)

            # Create rankings using SQL-style sorting
            top_by_revenue = sorted(all_movies, key=lambda x: x["total_revenue"], reverse=True)[:limit]
            top_by_tickets = sorted(all_movies, key=lambda x: x["total_tickets_sold"], reverse=True)[:limit]
            top_by_occupancy = sorted(all_movies, key=lambda x: x["occupancy_rate"], reverse=True)[:limit]

            return {
                "period": {
                    "from": date_from_parsed.isoformat(),
                    "to": date_to_parsed.isoformat()
                },
                "top_by_revenue": top_by_revenue,
                "top_by_tickets_sold": top_by_tickets,
                "top_by_occupancy_rate": top_by_occupancy,
                "total_movies_analyzed": len(all_movies)
            }
        except Exception as e:
            logger.error(f"Error generating movie performance report: {e}")
            raise

    async def get_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """Get summary for a specific day using SQL aggregations"""
        try:
            if date:
                target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            else:
                target_date = datetime.now().date()

            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            # Summary statistics with SQL aggregations
            summary_stats = self.db.query(
                func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('total_revenue'),
                func.sum(Schedule.current_sales).label('total_tickets'),
                func.sum(Schedule.max_sales).label('total_capacity'),
                func.count(Schedule.id).label('total_showings')
            ).filter(
                and_(
                    Schedule.time_slot >= start_of_day,
                    Schedule.time_slot <= end_of_day
                )
            ).first()

            total_revenue = float(summary_stats.total_revenue or 0)
            total_tickets = int(summary_stats.total_tickets or 0)
            total_capacity = int(summary_stats.total_capacity or 0)
            total_showings = int(summary_stats.total_showings or 0)

            # Schedule details with optimized query (only when needed)
            schedule_details_query = self.db.query(
                Schedule.time_slot,
                Movie.title.label('movie_title'),
                Cinema.number.label('cinema_number'),
                Schedule.current_sales,
                Schedule.max_sales,
                ((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('revenue')
            ).join(Movie).join(Cinema).filter(
                and_(
                    Schedule.time_slot >= start_of_day,
                    Schedule.time_slot <= end_of_day
                )
            ).order_by(Schedule.time_slot).all()

            # Format schedule details
            schedule_details = [
                {
                    "time": row.time_slot.strftime("%H:%M"),
                    "movie": row.movie_title,
                    "cinema": f"Cinema {row.cinema_number}",
                    "sold": row.current_sales,
                    "capacity": row.max_sales,
                    "revenue": round(float(row.revenue or 0), 2)
                }
                for row in schedule_details_query
            ]

            return {
                "date": target_date.isoformat(),
                "total_showings": total_showings,
                "total_revenue": round(total_revenue, 2),
                "total_tickets_sold": total_tickets,
                "total_capacity": total_capacity,
                "occupancy_rate": round((total_tickets / total_capacity) * 100, 2) if total_capacity > 0 else 0,
                "average_ticket_price": round(total_revenue / total_tickets, 2) if total_tickets > 0 else 0,
                "schedule_details": schedule_details
            }
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            raise

    def _build_date_filters(self, date_from: str = None, date_to: str = None, default_days: int = 30):
        """Helper method to build standardized date filters"""
        if date_from:
            date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        else:
            date_from_parsed = datetime.now() - timedelta(days=default_days)

        if date_to:
            date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        else:
            date_to_parsed = datetime.now()

        return date_from_parsed, date_to_parsed

    async def get_performance_metrics(self, date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """Get comprehensive performance metrics using optimized SQL queries"""
        try:
            date_from_parsed, date_to_parsed = self._build_date_filters(date_from, date_to)

            filter_conditions = [
                Schedule.time_slot >= date_from_parsed,
                Schedule.time_slot <= date_to_parsed
            ]

            # High-level metrics in a single query
            metrics = self.db.query(
                func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('total_revenue'),
                func.sum(Schedule.current_sales).label('total_tickets'),
                func.sum(Schedule.max_sales).label('total_capacity'),
                func.count(Schedule.id).label('total_showings'),
                func.count(func.distinct(Schedule.movie_id)).label('unique_movies'),
                func.count(func.distinct(Schedule.cinema_id)).label('unique_cinemas'),
                func.avg(Schedule.unit_price + Schedule.service_fee).label('avg_ticket_price')
            ).filter(and_(*filter_conditions)).first()

            total_revenue = float(metrics.total_revenue or 0)
            total_tickets = int(metrics.total_tickets or 0)
            total_capacity = int(metrics.total_capacity or 0)

            return {
                "period": {
                    "from": date_from_parsed.isoformat(),
                    "to": date_to_parsed.isoformat()
                },
                "metrics": {
                    "total_revenue": round(total_revenue, 2),
                    "total_tickets_sold": total_tickets,
                    "total_capacity": total_capacity,
                    "total_showings": int(metrics.total_showings or 0),
                    "unique_movies": int(metrics.unique_movies or 0),
                    "unique_cinemas": int(metrics.unique_cinemas or 0),
                    "overall_occupancy_rate": round((total_tickets / total_capacity) * 100, 2) if total_capacity > 0 else 0,
                    "average_ticket_price": round(float(metrics.avg_ticket_price or 0), 2),
                    "revenue_per_showing": round(total_revenue / int(metrics.total_showings or 1), 2)
                }
            }
        except Exception as e:
            logger.error(f"Error generating performance metrics: {e}")
            raise

    async def get_quick_stats(self) -> Dict[str, Any]:
        """Get quick dashboard statistics using optimized queries"""
        try:
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())

            # Today's stats
            today_stats = self.db.query(
                func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('revenue'),
                func.sum(Schedule.current_sales).label('tickets'),
                func.count(Schedule.id).label('showings')
            ).filter(
                and_(
                    Schedule.time_slot >= today_start,
                    Schedule.time_slot <= today_end
                )
            ).first()

            # This month's stats
            month_start = today.replace(day=1)
            month_start_dt = datetime.combine(month_start, datetime.min.time())

            month_stats = self.db.query(
                func.sum((Schedule.unit_price + Schedule.service_fee) * Schedule.current_sales).label('revenue'),
                func.sum(Schedule.current_sales).label('tickets'),
                func.count(Schedule.id).label('showings')
            ).filter(
                Schedule.time_slot >= month_start_dt
            ).first()

            return {
                "today": {
                    "revenue": round(float(today_stats.revenue or 0), 2),
                    "tickets_sold": int(today_stats.tickets or 0),
                    "showings": int(today_stats.showings or 0)
                },
                "this_month": {
                    "revenue": round(float(month_stats.revenue or 0), 2),
                    "tickets_sold": int(month_stats.tickets or 0),
                    "showings": int(month_stats.showings or 0)
                }
            }
        except Exception as e:
            logger.error(f"Error generating quick stats: {e}")
            raise

# Global analytics service instance
analytics_service = AnalyticsService()