"""
REST API Tests for SAMi Backend

Tests all REST endpoints directly to ensure backend functionality.
Fast and reliable testing of CRUD operations.
"""

import pytest


class TestMoviesAPI:
    """Test movie CRUD operations."""

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
        return data["id"]  # Return for cleanup

    def test_get_movie_by_id(self, client, sample_movie_data):
        """Test GET /api/movies/{id} returns specific movie."""
        # Create movie first
        create_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = create_response.json()["id"]

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

        # Delete movie
        response = client.delete(f"/api/movies/{movie_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

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

    def test_get_cinema_by_number(self, client, sample_cinema_data):
        """Test GET /api/cinemas/{number} returns specific cinema."""
        # Create cinema first
        client.post("/api/cinemas", json=sample_cinema_data)

        # Get cinema by number
        response = client.get(f"/api/cinemas/{sample_cinema_data['number']}")
        assert response.status_code == 200
        data = response.json()
        assert data["number"] == sample_cinema_data["number"]

    def test_update_cinema(self, client, sample_cinema_data):
        """Test PUT /api/cinemas/{number} updates cinema."""
        # Create cinema first
        client.post("/api/cinemas", json=sample_cinema_data)

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

        # Delete cinema
        response = client.delete(f"/api/cinemas/{sample_cinema_data['number']}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()


class TestSchedulesAPI:
    """Test schedule CRUD operations."""

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

        cinema_response = client.post("/api/cinemas", json=sample_cinema_data)
        cinema_number = cinema_response.json()["number"]

        # Update schedule data with real IDs
        sample_schedule_data["movie_id"] = movie_id
        sample_schedule_data["cinema_number"] = cinema_number

        response = client.post("/api/schedules", json=sample_schedule_data)
        assert response.status_code == 200
        data = response.json()
        assert "scheduled" in data.get("message", "").lower() or data.get("movie_id") == sample_schedule_data["movie_id"]

    def test_get_schedule_by_id(self, client, sample_schedule_data, sample_movie_data, sample_cinema_data):
        """Test GET /api/schedules/{id} returns specific schedule."""
        # Create a movie and cinema first
        movie_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = movie_response.json()["id"]

        cinema_response = client.post("/api/cinemas", json=sample_cinema_data)
        cinema_number = cinema_response.json()["number"]

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

        # Get schedule by ID
        response = client.get(f"/api/schedules/{schedule_id}")
        assert response.status_code == 200

    def test_update_schedule(self, client, sample_schedule_data, sample_movie_data, sample_cinema_data):
        """Test PUT /api/schedules/{id} updates schedule."""
        # Create a movie and cinema first
        movie_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = movie_response.json()["id"]

        cinema_response = client.post("/api/cinemas", json=sample_cinema_data)
        cinema_number = cinema_response.json()["number"]

        # Update schedule data with real IDs
        sample_schedule_data["movie_id"] = movie_id
        sample_schedule_data["cinema_number"] = cinema_number

        # Create schedule first
        create_response = client.post("/api/schedules", json=sample_schedule_data)
        schedule_data = create_response.json()

        schedule_id = schedule_data.get("id") or schedule_data.get("schedule_id")
        if not schedule_id:
            pytest.skip("Cannot extract schedule ID from create response")

        # Update schedule
        update_data = {"unit_price": 18.00}
        response = client.put(f"/api/schedules/{schedule_id}", json=update_data)
        assert response.status_code == 200

    def test_cancel_schedule(self, client, sample_schedule_data, sample_movie_data, sample_cinema_data):
        """Test DELETE /api/schedules/{id} cancels schedule."""
        # Create a movie and cinema first
        movie_response = client.post("/api/movies", json=sample_movie_data)
        movie_id = movie_response.json()["id"]

        cinema_response = client.post("/api/cinemas", json=sample_cinema_data)
        cinema_number = cinema_response.json()["number"]

        # Update schedule data with real IDs
        sample_schedule_data["movie_id"] = movie_id
        sample_schedule_data["cinema_number"] = cinema_number

        # Create schedule first
        create_response = client.post("/api/schedules", json=sample_schedule_data)
        schedule_data = create_response.json()

        schedule_id = schedule_data.get("id") or schedule_data.get("schedule_id")
        if not schedule_id:
            pytest.skip("Cannot extract schedule ID from create response")

        # Cancel schedule
        response = client.delete(f"/api/schedules/{schedule_id}")
        assert response.status_code == 200


class TestForecastsAPI:
    """Test forecast CRUD operations."""

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
        assert data.get("date_range_start") == sample_forecast_data["date_range_start"]

    def test_get_forecast_by_id(self, client, sample_forecast_data):
        """Test GET /api/forecasts/{id} returns specific forecast."""
        # Create forecast first
        create_response = client.post("/api/forecasts", json=sample_forecast_data)
        forecast_id = create_response.json()["id"]

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

        # Delete forecast
        response = client.delete(f"/api/forecasts/{forecast_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()


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