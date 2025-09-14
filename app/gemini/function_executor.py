"""
Function executor for Gemini AI function calling
Routes function calls to appropriate service methods
"""

import logging
from typing import Dict, Any, List
from app.services.cinema_service import cinema_service
from app.services.movie_service import movie_service
from app.services.schedule_service import schedule_service
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

class FunctionExecutor:
    """Executes functions called by Gemini AI"""

    def __init__(self):
        """Initialize function executor with service mappings"""
        self.function_map = {
            # Cinema functions
            "get_all_cinemas": self._execute_cinema_function,
            "get_cinema_by_number": self._execute_cinema_function,
            "get_available_cinemas": self._execute_cinema_function,
            "create_cinema": self._execute_cinema_function,
            "update_cinema": self._execute_cinema_function,
            "get_cinema_types": self._execute_cinema_function,

            # Movie functions
            "get_all_movies": self._execute_movie_function,
            "get_movie_by_id": self._execute_movie_function,
            "search_movies": self._execute_movie_function,
            "create_movie": self._execute_movie_function,
            "update_movie": self._execute_movie_function,
            "get_movies_by_genre": self._execute_movie_function,
            "get_movie_statistics": self._execute_movie_function,

            # Schedule functions
            "get_all_schedules": self._execute_schedule_function,
            "get_schedules_by_date": self._execute_schedule_function,
            "create_schedule": self._execute_schedule_function,
            "update_schedule": self._execute_schedule_function,
            "cancel_schedule": self._execute_schedule_function,
            "get_available_time_slots": self._execute_schedule_function,

            # Analytics functions
            "get_revenue_report": self._execute_analytics_function,
            "get_occupancy_report": self._execute_analytics_function,
            "get_movie_performance": self._execute_analytics_function,
            "get_daily_summary": self._execute_analytics_function,
        }

    async def execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a function called by Gemini AI

        Args:
            function_name: Name of the function to execute
            args: Function arguments

        Returns:
            Dict containing function result or error
        """
        try:
            logger.info(f"Executing function: {function_name} with args: {args}")

            if function_name not in self.function_map:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}",
                    "function_name": function_name
                }

            # Execute the function through the appropriate service
            result = await self.function_map[function_name](function_name, args)

            logger.info(f"Function {function_name} executed successfully")
            return {
                "success": True,
                "result": result,
                "function_name": function_name
            }

        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "function_name": function_name
            }

    async def execute_multiple_functions(self, function_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple functions in sequence

        Args:
            function_calls: List of function calls with 'name' and 'args' keys

        Returns:
            List of execution results
        """
        results = []
        for call in function_calls:
            function_name = call.get("name")
            args = call.get("args", {})

            result = await self.execute_function(function_name, args)
            results.append(result)

        return results

    async def _execute_cinema_function(self, function_name: str, args: Dict[str, Any]) -> Any:
        """Execute cinema-related functions"""
        method = getattr(cinema_service, function_name)

        # Handle different function signatures
        if function_name == "get_all_cinemas":
            return await method()
        elif function_name == "get_cinema_by_number":
            return await method(args["cinema_number"])
        elif function_name == "get_available_cinemas":
            return await method(
                datetime_slot=args.get("datetime_slot"),
                min_seats=args.get("min_seats")
            )
        elif function_name == "create_cinema":
            return await method(
                number=args["number"],
                cinema_type=args["cinema_type"],
                total_seats=args["total_seats"],
                location=args["location"],
                features=args.get("features")
            )
        elif function_name == "update_cinema":
            return await method(
                cinema_id=args["cinema_id"],
                total_seats=args.get("total_seats"),
                location=args.get("location"),
                features=args.get("features")
            )
        elif function_name == "get_cinema_types":
            return await method()
        else:
            raise ValueError(f"Unknown cinema function: {function_name}")

    async def _execute_movie_function(self, function_name: str, args: Dict[str, Any]) -> Any:
        """Execute movie-related functions"""
        method = getattr(movie_service, function_name)

        if function_name == "get_all_movies":
            return await method()
        elif function_name == "get_movie_by_id":
            return await method(args["movie_id"])
        elif function_name == "search_movies":
            return await method(
                title=args.get("title"),
                genre=args.get("genre"),
                rating=args.get("rating")
            )
        elif function_name == "create_movie":
            return await method(
                title=args["title"],
                duration=args["duration"],
                genre=args["genre"],
                rating=args["rating"],
                description=args["description"],
                release_date=args.get("release_date")
            )
        elif function_name == "update_movie":
            return await method(
                movie_id=args["movie_id"],
                title=args.get("title"),
                duration=args.get("duration"),
                genre=args.get("genre"),
                rating=args.get("rating"),
                description=args.get("description"),
                release_date=args.get("release_date")
            )
        elif function_name == "get_movies_by_genre":
            return await method(args["genre"])
        elif function_name == "get_movie_statistics":
            return await method()
        else:
            raise ValueError(f"Unknown movie function: {function_name}")

    async def _execute_schedule_function(self, function_name: str, args: Dict[str, Any]) -> Any:
        """Execute schedule-related functions"""
        method = getattr(schedule_service, function_name)

        if function_name == "get_all_schedules":
            return await method(
                date_from=args.get("date_from"),
                date_to=args.get("date_to"),
                cinema_id=args.get("cinema_id"),
                movie_id=args.get("movie_id")
            )
        elif function_name == "get_schedules_by_date":
            return await method(args["date"])
        elif function_name == "create_schedule":
            return await method(
                movie_id=args["movie_id"],
                cinema_id=args["cinema_id"],
                time_slot=args["time_slot"],
                unit_price=args["unit_price"],
                service_fee=args.get("service_fee", 0.0),
                max_sales=args.get("max_sales")
            )
        elif function_name == "update_schedule":
            return await method(
                schedule_id=args["schedule_id"],
                time_slot=args.get("time_slot"),
                unit_price=args.get("unit_price"),
                service_fee=args.get("service_fee"),
                max_sales=args.get("max_sales"),
                status=args.get("status")
            )
        elif function_name == "cancel_schedule":
            return await method(args["schedule_id"])
        elif function_name == "get_available_time_slots":
            return await method(
                cinema_id=args["cinema_id"],
                date=args["date"],
                movie_duration=args["movie_duration"]
            )
        else:
            raise ValueError(f"Unknown schedule function: {function_name}")

    async def _execute_analytics_function(self, function_name: str, args: Dict[str, Any]) -> Any:
        """Execute analytics-related functions"""
        method = getattr(analytics_service, function_name)

        if function_name == "get_revenue_report":
            return await method(
                date_from=args.get("date_from"),
                date_to=args.get("date_to"),
                cinema_id=args.get("cinema_id"),
                movie_id=args.get("movie_id")
            )
        elif function_name == "get_occupancy_report":
            return await method(
                date_from=args.get("date_from"),
                date_to=args.get("date_to")
            )
        elif function_name == "get_movie_performance":
            return await method(
                date_from=args.get("date_from"),
                date_to=args.get("date_to"),
                limit=args.get("limit", 10)
            )
        elif function_name == "get_daily_summary":
            return await method(args.get("date"))
        else:
            raise ValueError(f"Unknown analytics function: {function_name}")

    def get_available_functions(self) -> List[str]:
        """Get list of all available function names"""
        return list(self.function_map.keys())

    def is_function_available(self, function_name: str) -> bool:
        """Check if a function is available for execution"""
        return function_name in self.function_map

# Global function executor instance
function_executor = FunctionExecutor()