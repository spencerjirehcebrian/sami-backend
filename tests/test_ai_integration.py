"""
AI Integration Tests for SAMi Backend

Tests core AI function calling and natural language processing.
Validates that AI correctly calls backend functions and formats responses.
"""

import pytest


class TestCinemaAIIntegration:
    """Test AI integration for cinema management functions."""

    @pytest.mark.asyncio
    async def test_get_all_cinemas_ai(self, prompt_tester):
        """Test AI calls get_all_cinemas function."""
        response = await prompt_tester.send_prompt("Show me all cinemas")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert "cinema" in content or "theater" in content

    @pytest.mark.asyncio
    async def test_get_cinema_by_number_ai(self, prompt_tester):
        """Test AI calls get_cinema_by_number function."""
        response = await prompt_tester.send_prompt("Tell me about Cinema 1")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert "cinema" in content and ("1" in content or "one" in content)

    @pytest.mark.asyncio
    async def test_get_available_cinemas_ai(self, prompt_tester):
        """Test AI calls get_available_cinemas function."""
        response = await prompt_tester.send_prompt("Which cinemas are available tonight?")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert any(word in content for word in ["cinema", "available", "tonight", "theater"])


class TestMovieAIIntegration:
    """Test AI integration for movie management functions."""

    @pytest.mark.asyncio
    async def test_get_all_movies_ai(self, prompt_tester):
        """Test AI calls get_all_movies function."""
        response = await prompt_tester.send_prompt("List all movies")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert "movie" in content or "film" in content

    @pytest.mark.asyncio
    async def test_search_movies_ai(self, prompt_tester):
        """Test AI calls search_movies function."""
        response = await prompt_tester.send_prompt("Find action movies")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert "action" in content or "movie" in content

    @pytest.mark.asyncio
    async def test_search_movies_by_genre_ai(self, prompt_tester):
        """Test AI searches movies by specific genre."""
        response = await prompt_tester.send_prompt("Show me comedy movies")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert "comedy" in content or "movie" in content

    @pytest.mark.asyncio
    async def test_create_movie_ai(self, prompt_tester):
        """Test AI calls create_movie function."""
        response = await prompt_tester.send_prompt("Add a new movie called 'Test AI Film'")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert any(word in content for word in ["created", "added", "movie", "film"])


class TestScheduleAIIntegration:
    """Test AI integration for schedule management functions."""

    @pytest.mark.asyncio
    async def test_get_all_schedules_ai(self, prompt_tester):
        """Test AI calls get_all_schedules function."""
        response = await prompt_tester.send_prompt("What's scheduled today?")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert any(word in content for word in ["schedule", "showing", "today", "movie"])

    @pytest.mark.asyncio
    async def test_get_schedules_by_date_ai(self, prompt_tester):
        """Test AI calls get_schedules_by_date function."""
        response = await prompt_tester.send_prompt("Show me tomorrow's schedule")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert any(word in content for word in ["tomorrow", "schedule", "showing"])

    @pytest.mark.asyncio
    async def test_create_schedule_ai(self, prompt_tester):
        """Test AI calls create_schedule function."""
        response = await prompt_tester.send_prompt("Schedule Avatar for Cinema 1 tomorrow at 8 PM")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert any(word in content for word in ["scheduled", "created", "booked", "avatar"])

    @pytest.mark.asyncio
    async def test_get_available_time_slots_ai(self, prompt_tester):
        """Test AI calls get_available_time_slots function."""
        response = await prompt_tester.send_prompt("What time slots are available for Cinema 2?")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert any(word in content for word in ["time", "available", "cinema", "slot"])


class TestForecastAIIntegration:
    """Test AI integration for forecast management functions."""

    @pytest.mark.asyncio
    async def test_create_forecast_ai(self, prompt_tester):
        """Test AI calls create_forecast function."""
        response = await prompt_tester.send_prompt("Create a forecast for next week")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert any(word in content for word in ["forecast", "created", "week", "prediction"])

    @pytest.mark.asyncio
    async def test_get_all_forecasts_ai(self, prompt_tester):
        """Test AI calls get_all_forecasts function."""
        response = await prompt_tester.send_prompt("Show me all forecasts")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert "forecast" in content

    @pytest.mark.asyncio
    async def test_get_forecast_details_ai(self, prompt_tester):
        """Test AI calls get_forecast_details function."""
        response = await prompt_tester.send_prompt("Give me details on the latest forecast")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert any(word in content for word in ["forecast", "details", "prediction"])


class TestAIProcessingValidation:
    """Test AI processing and response formatting."""

    @pytest.mark.asyncio
    async def test_function_call_execution(self, prompt_tester):
        """Test AI correctly executes backend functions."""
        response = await prompt_tester.send_prompt("How many movies do we have?")
        prompt_tester.assert_ai_response_valid(response)

        # Check that function was called
        metadata = response.get("metadata", {})
        function_calls = metadata.get("function_calls_made", 0)
        assert function_calls > 0, "AI should have made function calls"

    @pytest.mark.asyncio
    async def test_response_formatting(self, prompt_tester):
        """Test AI properly formats function results."""
        response = await prompt_tester.send_prompt("List the first 3 movies")
        prompt_tester.assert_ai_response_valid(response)

        # Response should be user-friendly, not raw function output
        content = response["content"]
        assert len(content) > 20, "Response should be formatted for users"
        assert not content.startswith("{"), "Should not return raw JSON"

    @pytest.mark.asyncio
    async def test_context_understanding(self, prompt_tester):
        """Test AI understands natural language intents."""
        response = await prompt_tester.send_prompt("What can I watch tonight?")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert any(word in content for word in ["movie", "film", "watch", "schedule", "show"])

    @pytest.mark.asyncio
    async def test_error_handling(self, prompt_tester):
        """Test AI gracefully handles function execution errors."""
        response = await prompt_tester.send_prompt("Get details for movie with ID 'nonexistent-movie-id'")
        # Response should be valid even if function fails
        assert response.get("type") in ["response", "error"]
        assert response.get("content"), "Should provide error message to user"


class TestDomainIntegration:
    """Test AI integration across different domains."""

    @pytest.mark.asyncio
    async def test_cinema_domain_integration(self, prompt_tester):
        """Test comprehensive cinema domain AI integration."""
        response = await prompt_tester.send_prompt("Tell me about our cinema facilities")
        prompt_tester.assert_ai_response_valid(response)
        assert "cinema" in response["content"].lower()

    @pytest.mark.asyncio
    async def test_movie_domain_integration(self, prompt_tester):
        """Test comprehensive movie domain AI integration."""
        response = await prompt_tester.send_prompt("What movies are popular right now?")
        prompt_tester.assert_ai_response_valid(response)
        assert any(word in response["content"].lower() for word in ["movie", "film", "popular"])

    @pytest.mark.asyncio
    async def test_schedule_domain_integration(self, prompt_tester):
        """Test comprehensive schedule domain AI integration."""
        response = await prompt_tester.send_prompt("What's our busiest time slot?")
        prompt_tester.assert_ai_response_valid(response)
        assert any(word in response["content"].lower() for word in ["time", "schedule", "busy"])

    @pytest.mark.asyncio
    async def test_forecast_domain_integration(self, prompt_tester):
        """Test comprehensive forecast domain AI integration."""
        response = await prompt_tester.send_prompt("What do our predictions look like?")
        prompt_tester.assert_ai_response_valid(response)
        assert any(word in response["content"].lower() for word in ["forecast", "prediction", "look"])