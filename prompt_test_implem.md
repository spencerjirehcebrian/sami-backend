# Prompt Testing Implementation Guide for SAMi Backend

## Overview

This document provides a comprehensive testing framework for validating the end-to-end natural language processing pipeline in the SAMi cinema management system. The tests ensure that user prompts are correctly understood, processed, and executed through the AI pipeline.

## Pipeline Architecture

```
User Prompt → WebSocket Handler → Message Processor → Gemini AI → Function Executor → Services → Database → Response
```

## Test Categories

### 1. Intent Recognition Tests

Verify that the AI correctly identifies user intentions and maps them to appropriate functions.

### 2. Parameter Extraction Tests

Ensure that relevant parameters are correctly extracted from natural language input.

### 3. Function Execution Tests

Validate that the correct functions are called with proper parameters.

### 4. Response Quality Tests

Assess the quality and accuracy of AI-generated responses.

### 5. Error Handling Tests

Test robustness when dealing with invalid inputs or system errors.

## Test Implementation Framework

### Setup Requirements

```python
import asyncio
import json
import websockets
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
```

### Test Configuration

```python
# Test configuration
WEBSOCKET_URL = "ws://localhost:8000/ws"
TEST_SESSION_ID = "test-session-e2e"
TIMEOUT = 30  # seconds

class PromptTester:
    def __init__(self):
        self.websocket = None
        self.session_id = TEST_SESSION_ID

    async def connect(self):
        """Establish WebSocket connection"""
        self.websocket = await websockets.connect(f"{WEBSOCKET_URL}/{self.session_id}")

    async def disconnect(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()

    async def send_prompt(self, prompt: str) -> Dict[str, Any]:
        """Send a prompt and return the response"""
        message = {
            "type": "chat",
            "content": prompt,
            "metadata": {}
        }

        await self.websocket.send(json.dumps(message))
        response = await asyncio.wait_for(
            self.websocket.recv(),
            timeout=TIMEOUT
        )

        return json.loads(response)
```

## Test Cases by Category

### 1. Cinema Management Tests

#### Test: Get All Cinemas

```python
async def test_get_all_cinemas():
    """Test: 'Show me all cinemas' should return cinema list"""
    tester = PromptTester()

    test_cases = [
        "Show me all cinemas",
        "List all movie theaters",
        "What cinemas do we have?",
        "Give me the cinema information",
        "I need to see all our theaters"
    ]

    for prompt in test_cases:
        await tester.connect()
        response = await tester.send_prompt(prompt)

        # Assertions
        assert response["type"] == "response"
        assert "cinema" in response["content"].lower()
        assert response["metadata"]["function_calls_made"] >= 1
        assert response["metadata"]["ai_powered"] == True

        await tester.disconnect()
```

#### Test: Get Specific Cinema

```python
async def test_get_specific_cinema():
    """Test: 'Tell me about Cinema 5' should return specific cinema info"""
    tester = PromptTester()

    test_cases = [
        ("Tell me about Cinema 5", 5),
        ("What's the capacity of Cinema 1?", 1),
        ("Show me details for theater number 3", 3),
        ("I need info on Cinema 10", 10)
    ]

    for prompt, expected_cinema_number in test_cases:
        await tester.connect()
        response = await tester.send_prompt(prompt)

        # Assertions
        assert response["type"] == "response"
        assert str(expected_cinema_number) in response["content"]
        assert "cinema" in response["content"].lower()

        await tester.disconnect()
```

### 2. Movie Management Tests

#### Test: Search Movies

```python
async def test_search_movies():
    """Test movie search functionality"""
    tester = PromptTester()

    test_cases = [
        ("Find all action movies", "action"),
        ("Show me horror films", "horror"),
        ("What comedies do we have?", "comedy"),
        ("List PG-13 movies", "PG-13")
    ]

    for prompt, expected_filter in test_cases:
        await tester.connect()
        response = await tester.send_prompt(prompt)

        # Assertions
        assert response["type"] == "response"
        assert expected_filter.lower() in response["content"].lower()
        assert "movie" in response["content"].lower()

        await tester.disconnect()
```

#### Test: Add New Movie

```python
async def test_add_new_movie():
    """Test adding a new movie"""
    tester = PromptTester()

    test_cases = [
        {
            "prompt": "Add a new movie called 'Test Adventure' that's 120 minutes long, rated PG-13, action genre, about a hero's journey",
            "expected_title": "Test Adventure",
            "expected_duration": 120,
            "expected_rating": "PG-13",
            "expected_genre": "action"
        }
    ]

    for test in test_cases:
        await tester.connect()
        response = await tester.send_prompt(test["prompt"])

        # Assertions
        assert response["type"] == "response"
        assert test["expected_title"] in response["content"]
        assert "created" in response["content"].lower() or "added" in response["content"].lower()

        await tester.disconnect()
```

### 3. Schedule Management Tests

#### Test: Create Schedule

```python
async def test_create_schedule():
    """Test schedule creation with natural language"""
    tester = PromptTester()

    # Get current date for testing
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    test_cases = [
        f"Schedule Avatar for Cinema 1 tomorrow at 8:00 PM with ticket price $15",
        f"Add a showing of Inception in Theater 2 at 7:30 PM tomorrow for $12",
        f"Book Cinema 3 for Spider-Man at 9:00 PM tomorrow, price $18"
    ]

    for prompt in test_cases:
        await tester.connect()
        response = await tester.send_prompt(prompt)

        # Assertions
        assert response["type"] == "response"
        assert "schedule" in response["content"].lower()
        assert ("created" in response["content"].lower() or
                "added" in response["content"].lower() or
                "booked" in response["content"].lower())

        await tester.disconnect()
```

#### Test: Check Availability

```python
async def test_check_availability():
    """Test availability checking"""
    tester = PromptTester()

    test_cases = [
        "What time slots are available for Cinema 1 tomorrow?",
        "When is Cinema 5 free next week?",
        "Show me available times for all theaters on Friday"
    ]

    for prompt in test_cases:
        await tester.connect()
        response = await tester.send_prompt(prompt)

        # Assertions
        assert response["type"] == "response"
        assert ("available" in response["content"].lower() or
                "free" in response["content"].lower() or
                "open" in response["content"].lower())

        await tester.disconnect()
```

### 4. Analytics Tests

#### Test: Revenue Reports

```python
async def test_revenue_reports():
    """Test revenue reporting functionality"""
    tester = PromptTester()

    test_cases = [
        "Show me today's revenue",
        "What was our revenue this week?",
        "Generate a revenue report for Cinema 1",
        "How much money did we make yesterday?"
    ]

    for prompt in test_cases:
        await tester.connect()
        response = await tester.send_prompt(prompt)

        # Assertions
        assert response["type"] == "response"
        assert ("revenue" in response["content"].lower() or
                "money" in response["content"].lower() or
                "earnings" in response["content"].lower())

        await tester.disconnect()
```

#### Test: Occupancy Reports

```python
async def test_occupancy_reports():
    """Test occupancy analysis"""
    tester = PromptTester()

    test_cases = [
        "What's our occupancy rate today?",
        "Show me how full our theaters are",
        "Which cinemas have the best attendance?",
        "Generate an occupancy report for this week"
    ]

    for prompt in test_cases:
        await tester.connect()
        response = await tester.send_prompt(prompt)

        # Assertions
        assert response["type"] == "response"
        assert ("occupancy" in response["content"].lower() or
                "attendance" in response["content"].lower() or
                "full" in response["content"].lower())

        await tester.disconnect()
```

### 5. Error Handling Tests

#### Test: Invalid Requests

```python
async def test_invalid_requests():
    """Test handling of invalid or impossible requests"""
    tester = PromptTester()

    test_cases = [
        "Schedule a movie for Cinema 999 tomorrow",  # Non-existent cinema
        "Show me revenue for the year 3000",         # Invalid date
        "Add a movie with -50 minutes duration",     # Invalid duration
        "Book Cinema 1 at 25:00",                   # Invalid time
    ]

    for prompt in test_cases:
        await tester.connect()
        response = await tester.send_prompt(prompt)

        # Assertions
        assert response["type"] in ["response", "error"]
        if response["type"] == "error":
            assert "error" in response["content"].lower()
        else:
            # AI should explain why the request can't be fulfilled
            assert ("cannot" in response["content"].lower() or
                    "unable" in response["content"].lower() or
                    "invalid" in response["content"].lower())

        await tester.disconnect()
```

#### Test: Ambiguous Requests

```python
async def test_ambiguous_requests():
    """Test handling of ambiguous requests"""
    tester = PromptTester()

    test_cases = [
        "Schedule a movie tomorrow",           # Missing movie, cinema, time
        "What's the revenue?",                # Missing time period
        "Cancel the showing",                 # Missing which showing
        "Update the movie",                   # Missing which movie and what to update
    ]

    for prompt in test_cases:
        await tester.connect()
        response = await tester.send_prompt(prompt)

        # Assertions
        assert response["type"] == "response"
        assert ("clarify" in response["content"].lower() or
                "specify" in response["content"].lower() or
                "which" in response["content"].lower() or
                "need" in response["content"].lower())

        await tester.disconnect()
```

### 6. Context and Follow-up Tests

#### Test: Conversational Context

```python
async def test_conversational_context():
    """Test that AI maintains context across multiple messages"""
    tester = PromptTester()
    await tester.connect()

    # First message: Get movie info
    response1 = await tester.send_prompt("Tell me about Avatar")
    assert "Avatar" in response1["content"]

    # Follow-up: Schedule without mentioning movie name again
    response2 = await tester.send_prompt("Schedule it for Cinema 1 tomorrow at 8 PM for $15")
    assert ("schedule" in response2["content"].lower() and
            ("Avatar" in response2["content"] or "it" in response2["content"]))

    await tester.disconnect()
```

## Advanced Testing Scenarios

### Performance Tests

```python
async def test_response_time():
    """Test that responses come within acceptable time limits"""
    tester = PromptTester()

    prompts = [
        "Show me all movies",
        "What's our revenue today?",
        "List available time slots for Cinema 1"
    ]

    for prompt in prompts:
        await tester.connect()
        start_time = datetime.now()

        response = await tester.send_prompt(prompt)

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()

        # Response should be under 5 seconds
        assert response_time < 5.0
        assert response["type"] == "response"

        await tester.disconnect()
```

### Concurrent User Tests

```python
async def test_concurrent_users():
    """Test multiple users interacting simultaneously"""
    async def user_session(user_id: int):
        tester = PromptTester()
        tester.session_id = f"test-user-{user_id}"

        await tester.connect()
        response = await tester.send_prompt(f"Show me all cinemas - User {user_id}")

        assert response["type"] == "response"
        assert "cinema" in response["content"].lower()

        await tester.disconnect()

    # Run 5 concurrent sessions
    tasks = [user_session(i) for i in range(5)]
    await asyncio.gather(*tasks)
```

## Test Execution Framework

### Running All Tests

```python
async def run_all_tests():
    """Execute all prompt tests for local MVP"""
    test_functions = [
        test_get_all_cinemas,
        test_get_specific_cinema,
        test_search_movies,
        test_add_new_movie,
        test_create_schedule,
        test_check_availability,
        test_revenue_reports,
        test_occupancy_reports,
        test_invalid_requests,
        test_ambiguous_requests,
        test_conversational_context,
        test_response_time
    ]

    results = {}

    for test_func in test_functions:
        try:
            await test_func()
            results[test_func.__name__] = "PASSED"
            print(f"✅ {test_func.__name__} PASSED")
        except Exception as e:
            results[test_func.__name__] = f"FAILED: {str(e)}"
            print(f"❌ {test_func.__name__} FAILED: {str(e)}")

    return results

# Execute tests
if __name__ == "__main__":
    results = asyncio.run(run_all_tests())

    # Summary
    passed = sum(1 for r in results.values() if r == "PASSED")
    total = len(results)

    print(f"\n📊 Test Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
```

## Test Data Setup

Before running tests, ensure the database is seeded with test data by running:

```bash
# Start the backend server
cd sami-backend
poetry run python alembic/seed.py

# The seed script creates movies, cinemas, and cinema types needed for testing
```

## Troubleshooting Common Issues

### Connection Issues

- Ensure the backend server is running on localhost:8000
- Check that WebSocket connections are properly established
- Verify the session ID format is correct

### Test Failures

- Check database connectivity and test data availability
- Verify Gemini API key is valid and has sufficient quota
- Ensure all required services (PostgreSQL, FastAPI) are running

### Response Validation

- Update assertions when response formats change
- Account for variations in AI responses (natural language can vary)
- Use flexible matching for content validation

This testing framework ensures that the SAMi AI pipeline correctly processes natural language inputs and produces accurate responses for cinema management operations in your local MVP environment.
