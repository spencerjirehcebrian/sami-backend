"""
Basic Flow Tests for SAMi Backend

Tests common user workflows and end-to-end scenarios.
Validates that typical user interactions work properly.
"""

import pytest


class TestMovieDiscoveryFlow:
    """Test movie discovery user workflow."""

    @pytest.mark.asyncio
    async def test_search_get_details_check_schedule_flow(self, prompt_tester):
        """Test: Search movies → Get details → Check schedule."""
        # Step 1: Search for movies
        search_response = await prompt_tester.send_prompt("Find action movies")
        prompt_tester.assert_ai_response_valid(search_response)
        assert any(word in search_response["content"].lower() for word in ["action", "movie", "film"])

        # Step 2: Get details about movies (generic request)
        details_response = await prompt_tester.send_prompt("Tell me more about the first movie")
        prompt_tester.assert_ai_response_valid(details_response)
        assert any(word in details_response["content"].lower() for word in ["movie", "film", "details"])

        # Step 3: Check schedule
        schedule_response = await prompt_tester.send_prompt("When are the movies playing?")
        prompt_tester.assert_ai_response_valid(schedule_response)
        assert any(word in schedule_response["content"].lower() for word in ["schedule", "playing", "showing", "time"])

    @pytest.mark.asyncio
    async def test_genre_specific_discovery_flow(self, prompt_tester):
        """Test genre-specific movie discovery workflow."""
        # Search for specific genre
        response = await prompt_tester.send_prompt("What comedy movies do we have?")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert "comedy" in content or "movie" in content

        # Ask for recommendations
        rec_response = await prompt_tester.send_prompt("Which one do you recommend?")
        prompt_tester.assert_ai_response_valid(rec_response)
        assert any(word in rec_response["content"].lower() for word in ["recommend", "suggest", "movie"])


class TestBookingFlow:
    """Test booking and scheduling user workflow."""

    @pytest.mark.asyncio
    async def test_availability_schedule_confirm_flow(self, prompt_tester):
        """Test: Check availability → Schedule → Confirm."""
        # Step 1: Check availability
        avail_response = await prompt_tester.send_prompt("What cinemas are available tomorrow evening?")
        prompt_tester.assert_ai_response_valid(avail_response)
        assert any(word in avail_response["content"].lower() for word in ["cinema", "available", "tomorrow"])

        # Step 2: Schedule a movie
        schedule_response = await prompt_tester.send_prompt("Schedule a movie for Cinema 1 at 8 PM tomorrow")
        prompt_tester.assert_ai_response_valid(schedule_response)
        assert any(word in schedule_response["content"].lower() for word in ["schedule", "cinema", "movie"])

        # Step 3: Confirm/check the schedule
        confirm_response = await prompt_tester.send_prompt("Show me what's scheduled for tomorrow")
        prompt_tester.assert_ai_response_valid(confirm_response)
        assert any(word in confirm_response["content"].lower() for word in ["schedule", "tomorrow", "showing"])

    @pytest.mark.asyncio
    async def test_time_slot_booking_flow(self, prompt_tester):
        """Test time slot availability and booking."""
        # Check time slots
        slots_response = await prompt_tester.send_prompt("What time slots are available for Cinema 2?")
        prompt_tester.assert_ai_response_valid(slots_response)
        assert any(word in slots_response["content"].lower() for word in ["time", "slot", "available", "cinema"])

        # Book a specific time slot
        book_response = await prompt_tester.send_prompt("Book the 7 PM slot for an action movie")
        prompt_tester.assert_ai_response_valid(book_response)
        assert any(word in book_response["content"].lower() for word in ["book", "schedule", "action", "movie"])


class TestAnalyticsFlow:
    """Test analytics and reporting user workflow."""

    @pytest.mark.asyncio
    async def test_revenue_data_format_flow(self, prompt_tester):
        """Test: Request revenue → Get data → Format response."""
        # Request revenue information
        revenue_response = await prompt_tester.send_prompt("Show me today's revenue")
        prompt_tester.assert_ai_response_valid(revenue_response)
        content = revenue_response["content"].lower()
        assert any(word in content for word in ["revenue", "earning", "money", "income", "today"])

    @pytest.mark.asyncio
    async def test_occupancy_analytics_flow(self, prompt_tester):
        """Test occupancy and capacity analytics."""
        # Request occupancy data
        occupancy_response = await prompt_tester.send_prompt("What's our occupancy rate?")
        prompt_tester.assert_ai_response_valid(occupancy_response)
        content = occupancy_response["content"].lower()
        assert any(word in content for word in ["occupancy", "capacity", "full", "empty", "rate"])

    @pytest.mark.asyncio
    async def test_performance_metrics_flow(self, prompt_tester):
        """Test performance metrics reporting."""
        # Request performance metrics
        perf_response = await prompt_tester.send_prompt("How are our movies performing?")
        prompt_tester.assert_ai_response_valid(perf_response)
        content = perf_response["content"].lower()
        assert any(word in content for word in ["perform", "movie", "popular", "success"])


class TestPlanningFlow:
    """Test planning and forecasting workflow."""

    @pytest.mark.asyncio
    async def test_forecast_creation_flow(self, prompt_tester):
        """Test forecast creation and planning."""
        # Create a forecast
        forecast_response = await prompt_tester.send_prompt("Create a forecast for next week")
        prompt_tester.assert_ai_response_valid(forecast_response)
        content = forecast_response["content"].lower()
        assert any(word in content for word in ["forecast", "prediction", "week", "created"])

        # Check forecast details
        details_response = await prompt_tester.send_prompt("What does the forecast predict?")
        prompt_tester.assert_ai_response_valid(details_response)
        assert any(word in details_response["content"].lower() for word in ["forecast", "predict", "expect"])

    @pytest.mark.asyncio
    async def test_weekly_planning_flow(self, prompt_tester):
        """Test weekly planning workflow."""
        # Plan for the week
        plan_response = await prompt_tester.send_prompt("Help me plan next week's movie schedule")
        prompt_tester.assert_ai_response_valid(plan_response)
        content = plan_response["content"].lower()
        assert any(word in content for word in ["plan", "schedule", "week", "movie"])


class TestCustomerServiceFlow:
    """Test customer service interaction workflows."""

    @pytest.mark.asyncio
    async def test_movie_recommendation_flow(self, prompt_tester):
        """Test movie recommendation workflow."""
        # Ask for recommendations
        rec_response = await prompt_tester.send_prompt("What movies would you recommend for tonight?")
        prompt_tester.assert_ai_response_valid(rec_response)
        content = rec_response["content"].lower()
        assert any(word in content for word in ["recommend", "movie", "tonight", "suggest"])

        # Ask about specific preferences
        pref_response = await prompt_tester.send_prompt("I like comedy movies, what do you suggest?")
        prompt_tester.assert_ai_response_valid(pref_response)
        assert any(word in pref_response["content"].lower() for word in ["comedy", "suggest", "movie"])

    @pytest.mark.asyncio
    async def test_information_request_flow(self, prompt_tester):
        """Test general information request workflow."""
        # General information request
        info_response = await prompt_tester.send_prompt("Tell me about your cinema facilities")
        prompt_tester.assert_ai_response_valid(info_response)
        content = info_response["content"].lower()
        assert any(word in content for word in ["cinema", "facility", "theater", "about"])

        # Follow-up questions
        followup_response = await prompt_tester.send_prompt("What are your operating hours?")
        prompt_tester.assert_ai_response_valid(followup_response)
        assert any(word in followup_response["content"].lower() for word in ["hour", "time", "open", "operating"])


class TestErrorHandlingFlow:
    """Test error handling in user workflows."""

    @pytest.mark.asyncio
    async def test_invalid_request_handling(self, prompt_tester):
        """Test handling of invalid or impossible requests."""
        # Invalid movie request
        response = await prompt_tester.send_prompt("Schedule a movie that doesn't exist")
        assert response.get("type") in ["response", "error"]
        assert response.get("content"), "Should provide helpful error message"

    @pytest.mark.asyncio
    async def test_unclear_request_handling(self, prompt_tester):
        """Test handling of unclear user requests."""
        # Vague request
        response = await prompt_tester.send_prompt("I want something")
        prompt_tester.assert_ai_response_valid(response)
        # Should ask for clarification or provide helpful suggestions
        content = response["content"].lower()
        assert any(word in content for word in ["help", "what", "specific", "clarify", "need"])

    @pytest.mark.asyncio
    async def test_system_limitation_handling(self, prompt_tester):
        """Test handling when system has limitations."""
        # Request for unavailable functionality
        response = await prompt_tester.send_prompt("Book tickets for me online")
        assert response.get("type") in ["response", "error"]
        assert response.get("content"), "Should explain limitations or alternatives"


class TestConcurrentUserFlow:
    """Test workflows that might involve multiple concurrent operations."""

    @pytest.mark.asyncio
    async def test_multi_cinema_query_flow(self, prompt_tester):
        """Test queries involving multiple cinemas."""
        response = await prompt_tester.send_prompt("Compare schedules between Cinema 1 and Cinema 2")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert "cinema" in content and any(word in content for word in ["compare", "schedule", "between"])

    @pytest.mark.asyncio
    async def test_multi_movie_comparison_flow(self, prompt_tester):
        """Test comparing multiple movies."""
        response = await prompt_tester.send_prompt("Which action movies are most popular?")
        prompt_tester.assert_ai_response_valid(response)
        content = response["content"].lower()
        assert "action" in content and any(word in content for word in ["popular", "movie", "most"])