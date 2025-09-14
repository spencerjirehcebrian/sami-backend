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
        """Generate revenue report with various breakdowns"""
        try:
            query = self.db.query(Schedule).join(Movie).join(Cinema).join(CinemaType)

            # Apply filters
            if date_from:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(Schedule.time_slot >= date_from_parsed)
            else:
                # Default to last 30 days
                date_from_parsed = datetime.now() - timedelta(days=30)
                query = query.filter(Schedule.time_slot >= date_from_parsed)

            if date_to:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(Schedule.time_slot <= date_to_parsed)

            if cinema_id:
                query = query.filter(Schedule.cinema_id == cinema_id)

            if movie_id:
                query = query.filter(Schedule.movie_id == movie_id)

            schedules = query.all()

            # Calculate total revenue
            total_revenue = sum(
                (schedule.unit_price + schedule.service_fee) * schedule.current_sales
                for schedule in schedules
            )

            total_tickets_sold = sum(schedule.current_sales for schedule in schedules)
            total_possible_tickets = sum(schedule.max_sales for schedule in schedules)

            # Revenue by cinema
            cinema_revenue = {}
            for schedule in schedules:
                cinema_key = f"Cinema {schedule.cinema.number}"
                revenue = (schedule.unit_price + schedule.service_fee) * schedule.current_sales
                if cinema_key not in cinema_revenue:
                    cinema_revenue[cinema_key] = {
                        "cinema_id": str(schedule.cinema_id),
                        "cinema_number": schedule.cinema.number,
                        "revenue": 0,
                        "tickets_sold": 0
                    }
                cinema_revenue[cinema_key]["revenue"] += revenue
                cinema_revenue[cinema_key]["tickets_sold"] += schedule.current_sales

            # Revenue by movie
            movie_revenue = {}
            for schedule in schedules:
                movie_title = schedule.movie.title
                revenue = (schedule.unit_price + schedule.service_fee) * schedule.current_sales
                if movie_title not in movie_revenue:
                    movie_revenue[movie_title] = {
                        "movie_id": str(schedule.movie_id),
                        "title": movie_title,
                        "genre": schedule.movie.genre,
                        "revenue": 0,
                        "tickets_sold": 0,
                        "showings": 0
                    }
                movie_revenue[movie_title]["revenue"] += revenue
                movie_revenue[movie_title]["tickets_sold"] += schedule.current_sales
                movie_revenue[movie_title]["showings"] += 1

            # Daily revenue breakdown
            daily_revenue = {}
            for schedule in schedules:
                date_key = schedule.time_slot.date().isoformat()
                revenue = (schedule.unit_price + schedule.service_fee) * schedule.current_sales
                if date_key not in daily_revenue:
                    daily_revenue[date_key] = {
                        "date": date_key,
                        "revenue": 0,
                        "tickets_sold": 0,
                        "showings": 0
                    }
                daily_revenue[date_key]["revenue"] += revenue
                daily_revenue[date_key]["tickets_sold"] += schedule.current_sales
                daily_revenue[date_key]["showings"] += 1

            # Sort daily revenue by date
            daily_revenue_sorted = sorted(daily_revenue.values(), key=lambda x: x["date"])

            return {
                "period": {
                    "from": date_from if date_from else date_from_parsed.isoformat(),
                    "to": date_to if date_to else datetime.now().isoformat()
                },
                "summary": {
                    "total_revenue": round(total_revenue, 2),
                    "total_tickets_sold": total_tickets_sold,
                    "total_possible_tickets": total_possible_tickets,
                    "overall_occupancy_rate": round((total_tickets_sold / total_possible_tickets) * 100, 2) if total_possible_tickets > 0 else 0,
                    "average_ticket_price": round(total_revenue / total_tickets_sold, 2) if total_tickets_sold > 0 else 0,
                    "total_showings": len(schedules)
                },
                "cinema_breakdown": list(cinema_revenue.values()),
                "movie_breakdown": sorted(movie_revenue.values(), key=lambda x: x["revenue"], reverse=True),
                "daily_breakdown": daily_revenue_sorted
            }
        except Exception as e:
            logger.error(f"Error generating revenue report: {e}")
            raise

    async def get_occupancy_report(
        self,
        date_from: str = None,
        date_to: str = None
    ) -> Dict[str, Any]:
        """Generate occupancy analysis report"""
        try:
            query = self.db.query(Schedule).join(Movie).join(Cinema).join(CinemaType)

            # Apply date filters
            if date_from:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(Schedule.time_slot >= date_from_parsed)
            else:
                date_from_parsed = datetime.now() - timedelta(days=30)
                query = query.filter(Schedule.time_slot >= date_from_parsed)

            if date_to:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(Schedule.time_slot <= date_to_parsed)

            schedules = query.all()

            # Overall occupancy stats
            total_capacity = sum(schedule.max_sales for schedule in schedules)
            total_sold = sum(schedule.current_sales for schedule in schedules)
            overall_occupancy = (total_sold / total_capacity) * 100 if total_capacity > 0 else 0

            # Cinema occupancy rates
            cinema_stats = {}
            for schedule in schedules:
                cinema_key = f"Cinema {schedule.cinema.number}"
                if cinema_key not in cinema_stats:
                    cinema_stats[cinema_key] = {
                        "cinema_id": str(schedule.cinema_id),
                        "cinema_number": schedule.cinema.number,
                        "total_capacity": 0,
                        "total_sold": 0,
                        "showings": 0
                    }
                cinema_stats[cinema_key]["total_capacity"] += schedule.max_sales
                cinema_stats[cinema_key]["total_sold"] += schedule.current_sales
                cinema_stats[cinema_key]["showings"] += 1

            # Calculate occupancy rates for cinemas
            for cinema in cinema_stats.values():
                cinema["occupancy_rate"] = round(
                    (cinema["total_sold"] / cinema["total_capacity"]) * 100, 2
                ) if cinema["total_capacity"] > 0 else 0

            # Time slot analysis (peak hours)
            hourly_stats = {}
            for schedule in schedules:
                hour = schedule.time_slot.hour
                if hour not in hourly_stats:
                    hourly_stats[hour] = {
                        "hour": f"{hour:02d}:00",
                        "total_capacity": 0,
                        "total_sold": 0,
                        "showings": 0
                    }
                hourly_stats[hour]["total_capacity"] += schedule.max_sales
                hourly_stats[hour]["total_sold"] += schedule.current_sales
                hourly_stats[hour]["showings"] += 1

            # Calculate occupancy rates for hours
            hourly_occupancy = []
            for hour_stat in hourly_stats.values():
                hour_stat["occupancy_rate"] = round(
                    (hour_stat["total_sold"] / hour_stat["total_capacity"]) * 100, 2
                ) if hour_stat["total_capacity"] > 0 else 0
                hourly_occupancy.append(hour_stat)

            hourly_occupancy.sort(key=lambda x: int(x["hour"].split(":")[0]))

            # Day of week analysis
            weekday_stats = {}
            for schedule in schedules:
                weekday = schedule.time_slot.strftime("%A")
                if weekday not in weekday_stats:
                    weekday_stats[weekday] = {
                        "day": weekday,
                        "total_capacity": 0,
                        "total_sold": 0,
                        "showings": 0
                    }
                weekday_stats[weekday]["total_capacity"] += schedule.max_sales
                weekday_stats[weekday]["total_sold"] += schedule.current_sales
                weekday_stats[weekday]["showings"] += 1

            # Calculate occupancy rates for weekdays
            for day_stat in weekday_stats.values():
                day_stat["occupancy_rate"] = round(
                    (day_stat["total_sold"] / day_stat["total_capacity"]) * 100, 2
                ) if day_stat["total_capacity"] > 0 else 0

            return {
                "period": {
                    "from": date_from if date_from else date_from_parsed.isoformat(),
                    "to": date_to if date_to else datetime.now().isoformat()
                },
                "overall_occupancy": {
                    "rate": round(overall_occupancy, 2),
                    "total_capacity": total_capacity,
                    "total_sold": total_sold,
                    "total_showings": len(schedules)
                },
                "cinema_occupancy": sorted(cinema_stats.values(), key=lambda x: x["occupancy_rate"], reverse=True),
                "hourly_occupancy": hourly_occupancy,
                "weekday_occupancy": list(weekday_stats.values())
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
        """Get top performing movies analysis"""
        try:
            query = self.db.query(Schedule).join(Movie).join(Cinema)

            # Apply date filters
            if date_from:
                date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(Schedule.time_slot >= date_from_parsed)
            else:
                date_from_parsed = datetime.now() - timedelta(days=30)
                query = query.filter(Schedule.time_slot >= date_from_parsed)

            if date_to:
                date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(Schedule.time_slot <= date_to_parsed)

            schedules = query.all()

            # Aggregate movie performance
            movie_performance = {}
            for schedule in schedules:
                movie_id = str(schedule.movie_id)
                if movie_id not in movie_performance:
                    movie_performance[movie_id] = {
                        "movie_id": movie_id,
                        "title": schedule.movie.title,
                        "genre": schedule.movie.genre,
                        "rating": schedule.movie.rating,
                        "duration": schedule.movie.duration,
                        "total_revenue": 0,
                        "total_tickets_sold": 0,
                        "total_capacity": 0,
                        "showings": 0,
                        "average_price": 0,
                        "occupancy_rate": 0
                    }

                revenue = (schedule.unit_price + schedule.service_fee) * schedule.current_sales
                movie_performance[movie_id]["total_revenue"] += revenue
                movie_performance[movie_id]["total_tickets_sold"] += schedule.current_sales
                movie_performance[movie_id]["total_capacity"] += schedule.max_sales
                movie_performance[movie_id]["showings"] += 1

            # Calculate derived metrics
            for movie in movie_performance.values():
                movie["occupancy_rate"] = round(
                    (movie["total_tickets_sold"] / movie["total_capacity"]) * 100, 2
                ) if movie["total_capacity"] > 0 else 0
                movie["average_price"] = round(
                    movie["total_revenue"] / movie["total_tickets_sold"], 2
                ) if movie["total_tickets_sold"] > 0 else 0

            # Sort by different metrics
            top_by_revenue = sorted(
                movie_performance.values(),
                key=lambda x: x["total_revenue"],
                reverse=True
            )[:limit]

            top_by_tickets = sorted(
                movie_performance.values(),
                key=lambda x: x["total_tickets_sold"],
                reverse=True
            )[:limit]

            top_by_occupancy = sorted(
                movie_performance.values(),
                key=lambda x: x["occupancy_rate"],
                reverse=True
            )[:limit]

            return {
                "period": {
                    "from": date_from if date_from else date_from_parsed.isoformat(),
                    "to": date_to if date_to else datetime.now().isoformat()
                },
                "top_by_revenue": top_by_revenue,
                "top_by_tickets_sold": top_by_tickets,
                "top_by_occupancy_rate": top_by_occupancy,
                "total_movies_analyzed": len(movie_performance)
            }
        except Exception as e:
            logger.error(f"Error generating movie performance report: {e}")
            raise

    async def get_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """Get summary for a specific day"""
        try:
            if date:
                target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            else:
                target_date = datetime.now().date()

            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            schedules = self.db.query(Schedule).join(Movie).join(Cinema).filter(
                and_(
                    Schedule.time_slot >= start_of_day,
                    Schedule.time_slot <= end_of_day
                )
            ).all()

            total_revenue = sum(
                (schedule.unit_price + schedule.service_fee) * schedule.current_sales
                for schedule in schedules
            )
            total_tickets = sum(schedule.current_sales for schedule in schedules)
            total_capacity = sum(schedule.max_sales for schedule in schedules)

            return {
                "date": target_date.isoformat(),
                "total_showings": len(schedules),
                "total_revenue": round(total_revenue, 2),
                "total_tickets_sold": total_tickets,
                "total_capacity": total_capacity,
                "occupancy_rate": round((total_tickets / total_capacity) * 100, 2) if total_capacity > 0 else 0,
                "average_ticket_price": round(total_revenue / total_tickets, 2) if total_tickets > 0 else 0,
                "schedule_details": [
                    {
                        "time": schedule.time_slot.strftime("%H:%M"),
                        "movie": schedule.movie.title,
                        "cinema": f"Cinema {schedule.cinema.number}",
                        "sold": schedule.current_sales,
                        "capacity": schedule.max_sales,
                        "revenue": round((schedule.unit_price + schedule.service_fee) * schedule.current_sales, 2)
                    }
                    for schedule in sorted(schedules, key=lambda x: x.time_slot)
                ]
            }
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            raise

# Global analytics service instance
analytics_service = AnalyticsService()