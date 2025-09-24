"""
Function schemas for Gemini AI function calling
Defines all available cinema management operations
"""

# Cinema Management Functions
CINEMA_FUNCTIONS = [
    {
        "name": "get_all_cinemas",
        "description": "Get list of all cinemas with their details including capacity, type, and location",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_cinema_by_number",
        "description": "Get specific cinema information by cinema number",
        "parameters": {
            "type": "object",
            "properties": {
                "cinema_number": {
                    "type": "integer",
                    "description": "The cinema number (e.g., 1, 2, 3)"
                }
            },
            "required": ["cinema_number"]
        }
    },
    {
        "name": "get_available_cinemas",
        "description": "Get available cinemas based on criteria like minimum seats or time slot",
        "parameters": {
            "type": "object",
            "properties": {
                "datetime_slot": {
                    "type": "string",
                    "description": "ISO datetime string for checking availability (optional)"
                },
                "min_seats": {
                    "type": "integer",
                    "description": "Minimum number of seats required (optional)"
                }
            },
            "required": []
        }
    },
    {
        "name": "create_cinema",
        "description": "Create a new cinema with specified details",
        "parameters": {
            "type": "object",
            "properties": {
                "number": {
                    "type": "integer",
                    "description": "Unique cinema number"
                },
                "cinema_type": {
                    "type": "string",
                    "description": "Cinema type ID (standard, premium, imax, etc.)"
                },
                "total_seats": {
                    "type": "integer",
                    "description": "Total seating capacity"
                },
                "location": {
                    "type": "string",
                    "description": "Physical location or floor description"
                },
                "features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of cinema features (e.g., 'Dolby Atmos', '4K Projection')"
                }
            },
            "required": ["number", "cinema_type", "total_seats", "location"]
        }
    },
    {
        "name": "update_cinema",
        "description": "Update existing cinema details",
        "parameters": {
            "type": "object",
            "properties": {
                "cinema_id": {
                    "type": "string",
                    "description": "Cinema UUID"
                },
                "total_seats": {
                    "type": "integer",
                    "description": "Updated seating capacity (optional)"
                },
                "location": {
                    "type": "string",
                    "description": "Updated location (optional)"
                },
                "features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Updated list of features (optional)"
                }
            },
            "required": ["cinema_id"]
        }
    },
    {
        "name": "get_cinema_types",
        "description": "Get all available cinema types with their pricing multipliers",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# Movie Management Functions
MOVIE_FUNCTIONS = [
    {
        "name": "get_all_movies",
        "description": "Get complete movie catalog with all details",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_movie_by_id",
        "description": "Get specific movie details by ID",
        "parameters": {
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "string",
                    "description": "Movie UUID"
                }
            },
            "required": ["movie_id"]
        }
    },
    {
        "name": "search_movies",
        "description": "Search movies by title, genre, or rating",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Movie title or partial title to search for"
                },
                "genre": {
                    "type": "string",
                    "description": "Genre to filter by (e.g., 'Action', 'Comedy')"
                },
                "rating": {
                    "type": "string",
                    "description": "Rating to filter by (e.g., 'PG', 'PG-13', 'R')"
                }
            },
            "required": []
        }
    },
    {
        "name": "create_movie",
        "description": "Add a new movie to the catalog",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Movie title"
                },
                "duration": {
                    "type": "integer",
                    "description": "Movie duration in minutes"
                },
                "genre": {
                    "type": "string",
                    "description": "Movie genre"
                },
                "rating": {
                    "type": "string",
                    "description": "Movie rating (G, PG, PG-13, R, etc.)"
                },
                "description": {
                    "type": "string",
                    "description": "Movie plot description"
                },
                "release_date": {
                    "type": "string",
                    "description": "Release date in ISO format (optional)"
                }
            },
            "required": ["title", "duration", "genre", "rating", "description"]
        }
    },
    {
        "name": "update_movie",
        "description": "Update existing movie information",
        "parameters": {
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "string",
                    "description": "Movie UUID"
                },
                "title": {
                    "type": "string",
                    "description": "Updated movie title (optional)"
                },
                "duration": {
                    "type": "integer",
                    "description": "Updated duration in minutes (optional)"
                },
                "genre": {
                    "type": "string",
                    "description": "Updated genre (optional)"
                },
                "rating": {
                    "type": "string",
                    "description": "Updated rating (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "Updated description (optional)"
                },
                "release_date": {
                    "type": "string",
                    "description": "Updated release date in ISO format (optional)"
                }
            },
            "required": ["movie_id"]
        }
    },
    {
        "name": "get_movies_by_genre",
        "description": "Get all movies of a specific genre",
        "parameters": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "string",
                    "description": "Genre name to filter by"
                }
            },
            "required": ["genre"]
        }
    },
    {
        "name": "get_movie_statistics",
        "description": "Get statistics about the movie catalog including genre and rating distributions",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# Schedule Management Functions
SCHEDULE_FUNCTIONS = [
    {
        "name": "get_all_schedules",
        "description": "Get movie schedules with optional filtering by date range, cinema, or movie",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Start date in ISO format (optional)"
                },
                "date_to": {
                    "type": "string",
                    "description": "End date in ISO format (optional)"
                },
                "cinema_id": {
                    "type": "string",
                    "description": "Filter by specific cinema UUID (optional)"
                },
                "movie_id": {
                    "type": "string",
                    "description": "Filter by specific movie UUID (optional)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_schedules_by_date",
        "description": "Get all schedules for a specific date",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in ISO format (YYYY-MM-DD or full ISO datetime)"
                }
            },
            "required": ["date"]
        }
    },
    {
        "name": "create_schedule",
        "description": "Create a new movie schedule for a specific cinema and time",
        "parameters": {
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "string",
                    "description": "Movie UUID to schedule"
                },
                "cinema_id": {
                    "type": "string",
                    "description": "Cinema UUID where movie will be shown"
                },
                "time_slot": {
                    "type": "string",
                    "description": "Showtime in ISO datetime format"
                },
                "unit_price": {
                    "type": "number",
                    "description": "Base ticket price"
                },
                "service_fee": {
                    "type": "number",
                    "description": "Additional service fee (optional, defaults to 0)"
                },
                "max_sales": {
                    "type": "integer",
                    "description": "Maximum tickets to sell (optional, defaults to cinema capacity)"
                }
            },
            "required": ["movie_id", "cinema_id", "time_slot", "unit_price"]
        }
    },
    {
        "name": "update_schedule",
        "description": "Update existing schedule details",
        "parameters": {
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "string",
                    "description": "Schedule UUID"
                },
                "time_slot": {
                    "type": "string",
                    "description": "New showtime in ISO datetime format (optional)"
                },
                "unit_price": {
                    "type": "number",
                    "description": "Updated ticket price (optional)"
                },
                "service_fee": {
                    "type": "number",
                    "description": "Updated service fee (optional)"
                },
                "max_sales": {
                    "type": "integer",
                    "description": "Updated maximum sales (optional)"
                },
                "status": {
                    "type": "string",
                    "description": "Schedule status: active, cancelled, completed (optional)"
                }
            },
            "required": ["schedule_id"]
        }
    },
    {
        "name": "cancel_schedule",
        "description": "Cancel a scheduled movie showing",
        "parameters": {
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "string",
                    "description": "Schedule UUID to cancel"
                }
            },
            "required": ["schedule_id"]
        }
    },
    {
        "name": "get_available_time_slots",
        "description": "Get available time slots for scheduling a movie in a specific cinema on a date",
        "parameters": {
            "type": "object",
            "properties": {
                "cinema_id": {
                    "type": "string",
                    "description": "Cinema UUID"
                },
                "date": {
                    "type": "string",
                    "description": "Date in ISO format"
                },
                "movie_duration": {
                    "type": "integer",
                    "description": "Movie duration in minutes"
                }
            },
            "required": ["cinema_id", "date", "movie_duration"]
        }
    }
]

# Forecast Management Functions
FORECAST_FUNCTIONS = [
    {
        "name": "create_forecast",
        "description": "Create a new forecast with AI-generated optimized schedules for a date range",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range_start": {
                    "type": "string",
                    "description": "Start date for forecast in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss)"
                },
                "date_range_end": {
                    "type": "string",
                    "description": "End date for forecast in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss)"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description for the forecast"
                },
                "optimization_parameters": {
                    "type": "object",
                    "description": "Optional optimization parameters",
                    "properties": {
                        "revenue_goal": {
                            "type": "number",
                            "description": "Revenue multiplier (0.5-2.0, default 1.0)"
                        },
                        "occupancy_goal": {
                            "type": "number",
                            "description": "Target occupancy rate (0.3-0.9, default 0.7)"
                        },
                        "movie_preferences": {
                            "type": "object",
                            "description": "Movie preferences as movie_id -> weight (0.1-2.0)"
                        }
                    }
                },
                "created_by": {
                    "type": "string",
                    "description": "User who created the forecast (optional, defaults to 'ai-assistant')"
                }
            },
            "required": ["date_range_start", "date_range_end"]
        }
    },
    {
        "name": "get_all_forecasts",
        "description": "Get list of all forecasts with their basic information and status",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_forecast_details",
        "description": "Get detailed information about a specific forecast including parameters and metrics",
        "parameters": {
            "type": "object",
            "properties": {
                "forecast_id": {
                    "type": "string",
                    "description": "Forecast UUID"
                }
            },
            "required": ["forecast_id"]
        }
    },
    {
        "name": "get_forecast_schedules",
        "description": "Get all generated schedules for a specific forecast",
        "parameters": {
            "type": "object",
            "properties": {
                "forecast_id": {
                    "type": "string",
                    "description": "Forecast UUID"
                }
            },
            "required": ["forecast_id"]
        }
    },
    {
        "name": "get_forecast_predictions",
        "description": "Get prediction metrics and analysis data for a specific forecast",
        "parameters": {
            "type": "object",
            "properties": {
                "forecast_id": {
                    "type": "string",
                    "description": "Forecast UUID"
                }
            },
            "required": ["forecast_id"]
        }
    },
    {
        "name": "regenerate_forecast",
        "description": "Re-run optimization to generate new schedules for an existing forecast",
        "parameters": {
            "type": "object",
            "properties": {
                "forecast_id": {
                    "type": "string",
                    "description": "Forecast UUID to regenerate"
                }
            },
            "required": ["forecast_id"]
        }
    }
]

# Combined list of all available functions
ALL_FUNCTIONS = CINEMA_FUNCTIONS + MOVIE_FUNCTIONS + SCHEDULE_FUNCTIONS + FORECAST_FUNCTIONS

# Function categories for easier access
FUNCTION_CATEGORIES = {
    "cinema": CINEMA_FUNCTIONS,
    "movie": MOVIE_FUNCTIONS,
    "schedule": SCHEDULE_FUNCTIONS,
    "forecast": FORECAST_FUNCTIONS
}

# Helper function to get functions by category
def get_functions_by_category(category: str = None):
    """Get function schemas by category or all if no category specified"""
    if category and category in FUNCTION_CATEGORIES:
        return FUNCTION_CATEGORIES[category]
    return ALL_FUNCTIONS

# Helper function to get function schema by name
def get_function_schema(function_name: str):
    """Get specific function schema by name"""
    for function in ALL_FUNCTIONS:
        if function["name"] == function_name:
            return function
    return None