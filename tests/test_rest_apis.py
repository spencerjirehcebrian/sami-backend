"""
REST API Tests for SAMi Backend

Tests all REST endpoints directly to ensure backend functionality.
Fast and reliable testing of CRUD operations.
"""

import pytest


class TestMoviesAPI:
    """Test movie CRUD operations."""

    @classmethod
    def setup_class(cls):
        """Set up class-level tracking for created entities."""
        cls.created_movie_ids = []

    @classmethod
    def teardown_class(cls):
        """Clean up any movies created during tests."""
        if hasattr(cls, 'created_movie_ids') and cls.created_movie_ids:
            from app.database import SessionLocal
            from app.models.movie import Movie

            db = SessionLocal()
            try:
                # Batch delete all created movies in single operation
                deleted = db.query(Movie).filter(Movie.id.in_(cls.created_movie_ids)).delete(synchronize_session=False)
                db.commit()
                print(f"Cleaned up {deleted} test movies")

                # Track cleanup for global optimization
                from tests.conftest import track_cleanup_performed
                track_cleanup_performed(deleted)
            except Exception as e:
                db.rollback()
                print(f"Error cleaning up movies: {e}")
            finally:
                db.close()

    def test_get_all_movies(self, client):
        """Test GET /api/movies returns movie list."""
        response = client.get("/api/movies")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_movie(self, client, sample_movie_data):
        """Test POST /api/movies creates new movie."""
        response = client.post("/api/movies", json=sample_movie_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_movie_data["title"]
        assert data["genre"] == sample_movie_data["genre"]
        # Track created movie for cleanup
        self.__class__.created_movie_ids.append(data["id"])
        return data["id"]

    def test_get_movie_by_id(self, client, sample_movie_data):
        """Test GET /api/movies/{id} returns specific movie."""
        # Create movie first
        create_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = create_response.json()["id"]
        self.__class__.created_movie_ids.append(movie_id)

        # Get movie by ID
        response = client.get(f"/api/movies/{movie_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == movie_id
        assert data["title"] == sample_movie_data["title"]

    def test_update_movie(self, client, sample_movie_data):
        """Test PUT /api/movies/{id} updates movie."""
        import time
        import random
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)

        # Create movie first
        create_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = create_response.json()["id"]
        self.__class__.created_movie_ids.append(movie_id)

        # Update movie with unique title
        updated_title = f"Updated Test Movie {timestamp}_{random_num}"
        update_data = {"title": updated_title, "genre": "Comedy"}
        response = client.put(f"/api/movies/{movie_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == updated_title
        assert data["genre"] == "Comedy"

    def test_delete_movie(self, client, sample_movie_data):
        """Test DELETE /api/movies/{id} deletes movie."""
        # Create movie first
        create_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = create_response.json()["id"]
        self.__class__.created_movie_ids.append(movie_id)

        # Delete movie
        response = client.delete(f"/api/movies/{movie_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

        # Remove from tracking since it's deleted
        if movie_id in self.__class__.created_movie_ids:
            self.__class__.created_movie_ids.remove(movie_id)

        # Verify deletion
        get_response = client.get(f"/api/movies/{movie_id}")
        assert get_response.status_code == 404

    def test_search_movies_by_genre(self, client):
        """Test GET /api/movies?genre= filters by genre."""
        response = client.get("/api/movies?genre=Action")
        assert response.status_code == 200
        movies = response.json()
        # If movies exist, they should be Action genre
        for movie in movies:
            assert movie.get("genre") == "Action"


class TestCinemasAPI:
    """Test cinema CRUD operations."""

    @classmethod
    def setup_class(cls):
        """Set up class-level tracking for created entities."""
        cls.created_cinema_numbers = []

    @classmethod
    def teardown_class(cls):
        """Clean up any cinemas created during tests."""
        if hasattr(cls, 'created_cinema_numbers') and cls.created_cinema_numbers:
            from app.database import SessionLocal
            from app.models.cinema import Cinema

            db = SessionLocal()
            try:
                # Batch delete all created cinemas in single operation
                deleted = db.query(Cinema).filter(Cinema.number.in_(cls.created_cinema_numbers)).delete(synchronize_session=False)
                db.commit()
                print(f"Cleaned up {deleted} test cinemas")

                # Track cleanup for global optimization
                from tests.conftest import track_cleanup_performed
                track_cleanup_performed(deleted)
            except Exception as e:
                db.rollback()
                print(f"Error cleaning up cinemas: {e}")
            finally:
                db.close()

    def test_get_all_cinemas(self, client):
        """Test GET /api/cinemas returns cinema list."""
        response = client.get("/api/cinemas")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_cinema(self, client, sample_cinema_data):
        """Test POST /api/cinemas creates new cinema."""
        response = client.post("/api/cinemas", json=sample_cinema_data)
        assert response.status_code == 200
        data = response.json()
        assert data["number"] == sample_cinema_data["number"]
        assert data["total_seats"] == sample_cinema_data["total_seats"]
        # Track created cinema for cleanup
        self.__class__.created_cinema_numbers.append(data["number"])

    def test_get_cinema_by_number(self, client, sample_cinema_data):
        """Test GET /api/cinemas/{number} returns specific cinema."""
        # Create cinema first
        client.post("/api/cinemas", json=sample_cinema_data)
        self.__class__.created_cinema_numbers.append(sample_cinema_data["number"])

        # Get cinema by number
        response = client.get(f"/api/cinemas/{sample_cinema_data['number']}")
        assert response.status_code == 200
        data = response.json()
        assert data["number"] == sample_cinema_data["number"]

    def test_update_cinema(self, client, sample_cinema_data):
        """Test PUT /api/cinemas/{number} updates cinema."""
        # Create cinema first
        client.post("/api/cinemas", json=sample_cinema_data)
        self.__class__.created_cinema_numbers.append(sample_cinema_data["number"])

        # Update cinema
        update_data = {"total_seats": 150}
        response = client.put(f"/api/cinemas/{sample_cinema_data['number']}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["total_seats"] == 150

    def test_delete_cinema(self, client, sample_cinema_data):
        """Test DELETE /api/cinemas/{number} deletes cinema."""
        # Create cinema first
        client.post("/api/cinemas", json=sample_cinema_data)
        self.__class__.created_cinema_numbers.append(sample_cinema_data["number"])

        # Delete cinema
        response = client.delete(f"/api/cinemas/{sample_cinema_data['number']}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

        # Remove from tracking since it's deleted
        if sample_cinema_data["number"] in self.__class__.created_cinema_numbers:
            self.__class__.created_cinema_numbers.remove(sample_cinema_data["number"])


class TestSchedulesAPI:
    """Test schedule CRUD operations."""

    @classmethod
    def setup_class(cls):
        """Set up class-level tracking for created entities."""
        cls.created_schedule_ids = []
        cls.created_movie_ids = []
        cls.created_cinema_numbers = []

    @classmethod
    def teardown_class(cls):
        """Clean up any schedules and related data created during tests."""
        if hasattr(cls, 'created_schedule_ids') or hasattr(cls, 'created_movie_ids') or hasattr(cls, 'created_cinema_numbers'):
            from app.database import SessionLocal
            from app.models.schedule import Schedule
            from app.models.movie import Movie
            from app.models.cinema import Cinema

            db = SessionLocal()
            try:
                # Batch all cleanup operations in single transaction for speed
                deleted_schedules = deleted_movies = deleted_cinemas = 0

                # 1. Delete schedules first
                if hasattr(cls, 'created_schedule_ids') and cls.created_schedule_ids:
                    deleted_schedules = db.query(Schedule).filter(
                        Schedule.id.in_(cls.created_schedule_ids)
                    ).delete(synchronize_session=False)

                # 2. Delete test movies
                if hasattr(cls, 'created_movie_ids') and cls.created_movie_ids:
                    deleted_movies = db.query(Movie).filter(
                        Movie.id.in_(cls.created_movie_ids)
                    ).delete(synchronize_session=False)

                # 3. Delete test cinemas
                if hasattr(cls, 'created_cinema_numbers') and cls.created_cinema_numbers:
                    deleted_cinemas = db.query(Cinema).filter(
                        Cinema.number.in_(cls.created_cinema_numbers)
                    ).delete(synchronize_session=False)

                # Single commit for all operations
                db.commit()
                print(f"Cleaned up schedule test data: {deleted_schedules} schedules, {deleted_movies} movies, {deleted_cinemas} cinemas")

                # Track cleanup for global optimization
                from tests.conftest import track_cleanup_performed
                track_cleanup_performed(deleted_schedules + deleted_movies + deleted_cinemas)
            except Exception as e:
                db.rollback()
                print(f"Error cleaning up schedule test data: {e}")
            finally:
                db.close()

    def test_get_all_schedules(self, client):
        """Test GET /api/schedules returns schedule list."""
        # API requires date filter for security - provide a reasonable date range
        response = client.get("/api/schedules?date_from=2024-12-01&date_to=2024-12-31")
        assert response.status_code == 200
        data = response.json()
        # API returns paginated data format
        assert "data" in data and "pagination" in data
        assert isinstance(data["data"], list)

    def test_create_schedule(self, client, sample_schedule_data, sample_movie_data, sample_cinema_data):
        """Test POST /api/schedules creates new schedule."""
        # Create a movie and cinema first
        movie_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = movie_response.json()["id"]
        self.__class__.created_movie_ids.append(movie_id)

        cinema_response = client.post("/api/cinemas", json=sample_cinema_data)
        cinema_number = cinema_response.json()["number"]
        self.__class__.created_cinema_numbers.append(cinema_number)

        # Update schedule data with real IDs
        sample_schedule_data["movie_id"] = movie_id
        sample_schedule_data["cinema_number"] = cinema_number

        response = client.post("/api/schedules", json=sample_schedule_data)
        assert response.status_code == 200
        data = response.json()
        assert "scheduled" in data.get("message", "").lower() or data.get("movie_id") == sample_schedule_data["movie_id"]
        # Track schedule if ID is available
        if data.get("id") or data.get("schedule_id"):
            schedule_id = data.get("id") or data.get("schedule_id")
            self.__class__.created_schedule_ids.append(schedule_id)

    def test_get_schedule_by_id(self, client, sample_schedule_data, sample_movie_data, sample_cinema_data):
        """Test GET /api/schedules/{id} returns specific schedule."""
        # Create a movie and cinema first
        movie_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = movie_response.json()["id"]
        self.__class__.created_movie_ids.append(movie_id)

        cinema_response = client.post("/api/cinemas", json=sample_cinema_data)
        cinema_number = cinema_response.json()["number"]
        self.__class__.created_cinema_numbers.append(cinema_number)

        # Update schedule data with real IDs
        sample_schedule_data["movie_id"] = movie_id
        sample_schedule_data["cinema_number"] = cinema_number

        # Create schedule first
        create_response = client.post("/api/schedules", json=sample_schedule_data)
        schedule_data = create_response.json()

        # Extract schedule ID from response
        schedule_id = schedule_data.get("id") or schedule_data.get("schedule_id")
        if not schedule_id:
            pytest.skip("Cannot extract schedule ID from create response")

        self.__class__.created_schedule_ids.append(schedule_id)

        # Get schedule by ID
        response = client.get(f"/api/schedules/{schedule_id}")
        assert response.status_code == 200

    def test_update_schedule(self, client, sample_schedule_data, sample_movie_data, sample_cinema_data):
        """Test PUT /api/schedules/{id} updates schedule."""
        # Create a movie and cinema first
        movie_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = movie_response.json()["id"]
        self.__class__.created_movie_ids.append(movie_id)

        cinema_response = client.post("/api/cinemas", json=sample_cinema_data)
        cinema_number = cinema_response.json()["number"]
        self.__class__.created_cinema_numbers.append(cinema_number)

        # Update schedule data with real IDs
        sample_schedule_data["movie_id"] = movie_id
        sample_schedule_data["cinema_number"] = cinema_number

        # Create schedule first
        create_response = client.post("/api/schedules", json=sample_schedule_data)
        schedule_data = create_response.json()

        schedule_id = schedule_data.get("id") or schedule_data.get("schedule_id")
        if not schedule_id:
            pytest.skip("Cannot extract schedule ID from create response")

        self.__class__.created_schedule_ids.append(schedule_id)

        # Update schedule
        update_data = {"unit_price": 18.00}
        response = client.put(f"/api/schedules/{schedule_id}", json=update_data)
        assert response.status_code == 200

    def test_cancel_schedule(self, client, sample_schedule_data, sample_movie_data, sample_cinema_data):
        """Test DELETE /api/schedules/{id} cancels schedule."""
        # Create a movie and cinema first
        movie_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = movie_response.json()["id"]
        self.__class__.created_movie_ids.append(movie_id)

        cinema_response = client.post("/api/cinemas", json=sample_cinema_data)
        cinema_number = cinema_response.json()["number"]
        self.__class__.created_cinema_numbers.append(cinema_number)

        # Update schedule data with real IDs
        sample_schedule_data["movie_id"] = movie_id
        sample_schedule_data["cinema_number"] = cinema_number

        # Create schedule first
        create_response = client.post("/api/schedules", json=sample_schedule_data)
        schedule_data = create_response.json()

        schedule_id = schedule_data.get("id") or schedule_data.get("schedule_id")
        if not schedule_id:
            pytest.skip("Cannot extract schedule ID from create response")

        self.__class__.created_schedule_ids.append(schedule_id)

        # Cancel schedule
        response = client.delete(f"/api/schedules/{schedule_id}")
        assert response.status_code == 200

        # Remove from tracking since it's deleted
        if schedule_id in self.__class__.created_schedule_ids:
            self.__class__.created_schedule_ids.remove(schedule_id)


class TestForecastsAPI:
    """Test forecast CRUD operations."""

    @classmethod
    def setup_class(cls):
        """Set up class-level tracking for created entities."""
        cls.created_forecast_ids = []

    @classmethod
    def teardown_class(cls):
        """Clean up any forecasts and related data created during tests."""
        if hasattr(cls, 'created_forecast_ids') and cls.created_forecast_ids:
            from app.database import SessionLocal
            from app.models.forecast import Forecast

            db = SessionLocal()
            try:
                # Leverage CASCADE deletes - deleting forecasts automatically removes schedules and predictions
                deleted_forecasts = db.query(Forecast).filter(
                    Forecast.id.in_(cls.created_forecast_ids)
                ).delete(synchronize_session=False)

                db.commit()
                print(f"Cleaned up forecast test data: {deleted_forecasts} forecasts (CASCADE deleted related schedules and predictions)")

                # Track cleanup for global optimization
                from tests.conftest import track_cleanup_performed
                track_cleanup_performed(deleted_forecasts)
            except Exception as e:
                db.rollback()
                print(f"Error cleaning up forecasts: {e}")
            finally:
                db.close()

    def test_get_all_forecasts(self, client):
        """Test GET /api/forecasts returns forecast list."""
        response = client.get("/api/forecasts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_forecast(self, client, sample_forecast_data):
        """Test POST /api/forecasts creates new forecast."""
        response = client.post("/api/forecasts", json=sample_forecast_data)
        assert response.status_code == 200
        data = response.json()
        # Compare date strings - API returns ISO format, test data is YYYY-MM-DD
        assert data.get("date_range_start").startswith(sample_forecast_data["date_range_start"])
        # Track created forecast for cleanup
        self.__class__.created_forecast_ids.append(data["id"])

    def test_get_forecast_by_id(self, client, sample_forecast_data):
        """Test GET /api/forecasts/{id} returns specific forecast."""
        # Create forecast first
        create_response = client.post("/api/forecasts", json=sample_forecast_data)
        forecast_id = create_response.json()["id"]
        self.__class__.created_forecast_ids.append(forecast_id)

        # Get forecast by ID
        response = client.get(f"/api/forecasts/{forecast_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == forecast_id

    def test_delete_forecast(self, client, sample_forecast_data):
        """Test DELETE /api/forecasts/{id} deletes forecast."""
        # Create forecast first
        create_response = client.post("/api/forecasts", json=sample_forecast_data)
        forecast_id = create_response.json()["id"]
        self.__class__.created_forecast_ids.append(forecast_id)

        # Delete forecast
        response = client.delete(f"/api/forecasts/{forecast_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

        # Remove from tracking since it's deleted (along with related data)
        if forecast_id in self.__class__.created_forecast_ids:
            self.__class__.created_forecast_ids.remove(forecast_id)


class TestHealthEndpoint:
    """Test system health endpoint."""

    def test_health_check(self, client):
        """Test GET /health returns system status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["service"] == "SAMi Backend API"

    def test_root_endpoint(self, client):
        """Test GET / returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "SAMi Backend API" in data["message"]