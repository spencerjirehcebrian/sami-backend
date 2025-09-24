# SAMi Backend Test Improvement Plan

## Current Issues with Test Suite

Your test suite has become over-engineered for what you actually need. Here are the main problems:

### 1. **Over-Complex Infrastructure**

- Complex retry logic with exponential backoff and jitter
- Performance monitoring and metrics collection
- Load testing and stress testing capabilities
- Complex reporting with multiple output formats
- Extensive rate limit handling beyond what's needed

### 2. **Bloated Test Coverage**

- Multiple prompt variations testing the same functionality
- Extensive error handling scenarios
- Edge case testing (invalid dates, non-existent entities, etc.)
- Complex context switching and conversational flows
- Performance benchmarking mixed with functional tests

### 3. **Mixed Concerns**

- Functional tests mixed with performance tests
- Unit-like testing mixed with integration testing
- WebSocket testing mixed with REST API testing

## Proposed Simplified Approach

### Core Philosophy

**Test the happy path effectively, keep it simple, focus on "does it work" rather than "does it handle every edge case perfectly"**

### 1. **Streamlined Test Structure**

```
tests/
├── test_rest_apis.py          # Test REST endpoints directly (~100 lines)
├── test_ai_integration.py     # Test AI prompts end-to-end (~200 lines)
├── test_basic_flows.py        # Test common user workflows (~100 lines)
├── conftest.py                # Minimal fixtures only (~50 lines)
├── utils.py                   # Basic utilities (~100 lines)
└── run_tests.py               # Simple test runner (~50 lines)
```

**Total: ~600 lines vs current ~2000+ lines**

### 2. **Two-Layer Testing Approach**

#### Layer 1: REST API Testing (Fast & Reliable)

Test all REST endpoints directly to ensure the backend works:

```python
def test_get_all_movies():
    response = client.get("/api/movies")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_create_schedule():
    data = {
        "movie_id": "uuid-here",
        "cinema_id": "uuid-here",
        "time_slot": "2024-01-15T20:00:00Z",
        "unit_price": 15.00
    }
    response = client.post("/api/schedules", json=data)
    assert response.status_code == 200
    assert "scheduled" in response.json()["message"].lower()
```

#### Layer 2: AI Integration Testing (Core Functionality)

Test key AI prompts to ensure the integration works:

```python
async def test_ai_movie_query():
    response = await send_prompt("Show me all action movies")
    assert "action" in response["content"].lower()
    assert response["metadata"]["ai_powered"] == True

async def test_ai_schedule_creation():
    response = await send_prompt("Schedule Avatar for Cinema 1 tomorrow at 8 PM")
    assert any(word in response["content"].lower()
              for word in ["scheduled", "created", "booked"])
```

### 3. **Essential AI Integration Tests**

Here's specifically what we're testing in the AI integration layer:

#### Core Function Call Integration

- **Cinema Management Functions**

  - `get_all_cinemas` - "Show me all cinemas"
  - `get_cinema_by_number` - "Tell me about Cinema 1"
  - `get_available_cinemas` - "Which cinemas are available tonight?"

- **Movie Management Functions**

  - `get_all_movies` - "List all movies"
  - `search_movies` - "Find action movies"
  - `create_movie` - "Add a new movie called 'Test Film'"

- **Schedule Management Functions**

  - `get_all_schedules` - "What's scheduled today?"
  - `create_schedule` - "Schedule Avatar for Cinema 1 tomorrow at 8 PM"
  - `get_schedules_by_date` - "Show me tomorrow's schedule"

- **Forecast Management Functions**
  - `create_forecast` - "Create a forecast for next week"
  - `get_all_forecasts` - "Show me all forecasts"

#### AI Processing Validation

- **Function Call Execution** - AI correctly calls backend functions
- **Response Formatting** - AI properly formats function results for users
- **Context Understanding** - AI understands natural language intents
- **Error Handling** - AI gracefully handles function execution errors

#### One Test Per Domain

```python
# Cinema domain
async def test_cinema_ai_integration():
    response = await send_prompt("Show me all cinemas")
    assert_ai_response_valid(response)
    assert "cinema" in response["content"].lower()

# Movie domain
async def test_movie_ai_integration():
    response = await send_prompt("Find action movies")
    assert_ai_response_valid(response)
    assert "action" in response["content"].lower()

# Schedule domain
async def test_schedule_ai_integration():
    response = await send_prompt("What's scheduled today?")
    assert_ai_response_valid(response)
    assert "schedule" in response["content"].lower()

# Forecast domain
async def test_forecast_ai_integration():
    response = await send_prompt("Create a forecast for next week")
    assert_ai_response_valid(response)
    assert "forecast" in response["content"].lower()
```

### 4. **Simplified Test Infrastructure**

#### Basic Retry Mechanism (Essential for LLM APIs)

```python
class SimpleRetry:
    def __init__(self, max_retries=3, base_delay=2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute(self, operation, *args, **kwargs):
        for attempt in range(self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                if self._is_rate_limit(e) and attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)  # Simple exponential
                    await asyncio.sleep(delay)
                    continue
                raise e

    def _is_rate_limit(self, exception):
        error_str = str(exception).lower()
        return any(term in error_str for term in ["rate limit", "429", "quota"])
```

#### Simplified PromptTester

```python
class PromptTester:
    def __init__(self, session_id=None):
        self.session_id = session_id or f"test-{int(time.time())}"
        self.websocket = None
        self.retry = SimpleRetry()

    async def connect(self):
        self.websocket = await websockets.connect(f"ws://localhost:8000/ws/{self.session_id}")

    async def send_prompt(self, prompt: str) -> dict:
        return await self.retry.execute(self._send_prompt_internal, prompt)

    async def _send_prompt_internal(self, prompt: str) -> dict:
        await self.websocket.send(json.dumps({"type": "chat", "content": prompt}))
        response_text = await self.websocket.recv()
        return json.loads(response_text)

    def assert_ai_response_valid(self, response: dict):
        assert response.get("type") == "response"
        assert response.get("content")
        assert response.get("metadata", {}).get("ai_powered") == True
```

### 5. **What We're Removing**

#### Infrastructure We Don't Need

- Complex retry mechanisms with jitter
- Performance monitoring and metrics collection
- Load testing capabilities
- Complex reporting systems
- Rate limit analytics
- Connection pooling
- Circuit breakers

#### Test Cases We Don't Need

- Multiple prompt variations per function
- Comprehensive error handling scenarios
- Edge case testing (invalid UUIDs, malformed dates)
- Context switching and multi-turn conversations
- Performance benchmarking
- Stress testing
- Detailed validation of error messages

#### What We Keep

- Basic retry for LLM rate limits (essential)
- Core functionality validation
- Simple response structure validation
- Basic error handling (404, 500 responses)

### 6. **Essential Test Categories**

#### REST API Tests (`test_rest_apis.py`)

- **Movies CRUD**: GET, POST, PUT, DELETE `/api/movies`
- **Cinemas CRUD**: GET, POST, PUT, DELETE `/api/cinemas`
- **Schedules CRUD**: GET, POST, PUT, DELETE `/api/schedules`
- **Forecasts CRUD**: GET, POST, PUT, DELETE `/api/forecasts`

#### AI Integration Tests (`test_ai_integration.py`)

**Core Function Testing (one per domain):**

- Cinema queries and management
- Movie search and management
- Schedule creation and querying
- Forecast generation

**AI Processing Validation:**

- Function calls are executed
- Results are properly formatted
- Natural language understanding works
- Error responses are handled

#### Basic Flow Tests (`test_basic_flows.py`)

- **Movie Discovery Flow**: Search → Get Details → Check Schedule
- **Booking Flow**: Find Available → Schedule → Confirm
- **Analytics Flow**: Request Revenue → Get Data → Format Response

### 7. **Simplified Reporting**

Replace complex reporting with:

```python
def run_tests():
    results = {
        "rest_api": run_rest_tests(),
        "ai_integration": run_ai_tests(),
        "basic_flows": run_flow_tests()
    }

    total_tests = sum(r["total"] for r in results.values())
    passed_tests = sum(r["passed"] for r in results.values())

    print(f"Tests: {passed_tests}/{total_tests} passed")

    for category, result in results.items():
        if result["failed"] > 0:
            print(f"\n{category} failures:")
            for failure in result["failures"]:
                print(f"  - {failure}")
```

### 8. **Implementation Priority**

#### Phase 1: Core Functionality (Week 1)

1. Set up simplified test infrastructure
2. Test all REST endpoints work (GET, POST, PUT, DELETE)
3. Test basic AI prompts for each domain (movies, cinemas, schedules, forecasts)

#### Phase 2: Integration Validation (Week 2)

1. Test key user workflows (search → schedule → confirm)
2. Test AI function calling works for each service
3. Validate error handling basics

#### Phase 3: Quality Assurance (Week 3)

1. Basic error responses (404, 500)
2. One performance smoke test (response < 10 seconds)
3. Documentation and cleanup

### 9. **Implementation Checklists**

#### Phase 1: Core Functionality Checklist

**Infrastructure Setup:**

- [ ] Create new `tests/` directory structure
- [ ] Implement `SimpleRetry` class with basic exponential backoff
- [ ] Create simplified `PromptTester` class
- [ ] Set up `conftest.py` with minimal fixtures
- [ ] Create basic test data seeds (movies, cinemas, schedules)

**REST API Tests (`test_rest_apis.py`):**

- [ ] Movies API tests:
  - [ ] `GET /api/movies` - returns movie list
  - [ ] `POST /api/movies` - creates new movie
  - [ ] `GET /api/movies/{id}` - returns specific movie
  - [ ] `PUT /api/movies/{id}` - updates movie
  - [ ] `DELETE /api/movies/{id}` - deletes movie
- [ ] Cinemas API tests:
  - [ ] `GET /api/cinemas` - returns cinema list
  - [ ] `POST /api/cinemas` - creates new cinema
  - [ ] `GET /api/cinemas/{number}` - returns specific cinema
  - [ ] `PUT /api/cinemas/{number}` - updates cinema
  - [ ] `DELETE /api/cinemas/{number}` - deletes cinema
- [ ] Schedules API tests:
  - [ ] `GET /api/schedules` - returns schedule list
  - [ ] `POST /api/schedules` - creates new schedule
  - [ ] `GET /api/schedules/{id}` - returns specific schedule
  - [ ] `PUT /api/schedules/{id}` - updates schedule
  - [ ] `DELETE /api/schedules/{id}` - cancels schedule
- [ ] Forecasts API tests:
  - [ ] `GET /api/forecasts` - returns forecast list
  - [ ] `POST /api/forecasts` - creates new forecast
  - [ ] `GET /api/forecasts/{id}` - returns specific forecast
  - [ ] `DELETE /api/forecasts/{id}` - deletes forecast

**Basic AI Integration Tests (`test_ai_integration.py`):**

- [ ] Cinema AI tests:
  - [ ] "Show me all cinemas" - calls `get_all_cinemas`
  - [ ] "Tell me about Cinema 1" - calls `get_cinema_by_number`
- [ ] Movie AI tests:
  - [ ] "List all movies" - calls `get_all_movies`
  - [ ] "Find action movies" - calls `search_movies`
- [ ] Schedule AI tests:
  - [ ] "What's scheduled today?" - calls `get_schedules_by_date`
  - [ ] "Schedule Avatar for Cinema 1 tomorrow at 8 PM" - calls `create_schedule`
- [ ] Forecast AI tests:
  - [ ] "Create a forecast for next week" - calls `create_forecast`
  - [ ] "Show me all forecasts" - calls `get_all_forecasts`

**Validation Functions:**

- [ ] `assert_ai_response_valid()` - validates AI response structure
- [ ] `assert_function_called()` - validates function was executed
- [ ] Basic response time validation (< 10 seconds)

#### Phase 2: Integration Validation Checklist

**Workflow Tests (`test_basic_flows.py`):**

- [ ] Movie Discovery Flow:
  - [ ] "Find action movies" → Get results
  - [ ] "Tell me about [first movie]" → Get details
  - [ ] "When is [movie] playing?" → Check schedule
- [ ] Booking Flow:
  - [ ] "What cinemas are available tomorrow evening?" → Get availability
  - [ ] "Schedule [movie] for Cinema 1 at 8 PM tomorrow" → Create booking
  - [ ] Verify schedule was created in database
- [ ] Analytics Flow:
  - [ ] "Show me today's revenue" → Get revenue data
  - [ ] "What's our occupancy rate?" → Get occupancy data
  - [ ] Verify data format and content

**AI Function Call Integration:**

- [ ] Test AI correctly calls cinema service functions
- [ ] Test AI correctly calls movie service functions
- [ ] Test AI correctly calls schedule service functions
- [ ] Test AI correctly calls forecast service functions
- [ ] Test AI handles function execution errors gracefully
- [ ] Test AI formats function results for user consumption

**Error Handling:**

- [ ] Test WebSocket connection failures
- [ ] Test AI service unavailable scenarios
- [ ] Test database connection errors
- [ ] Test malformed AI responses

#### Phase 3: Quality Assurance Checklist

**Error Response Testing:**

- [ ] Test 404 responses for non-existent resources
- [ ] Test 500 responses for server errors
- [ ] Test AI error responses are user-friendly
- [ ] Test WebSocket disconnection handling

**Performance Validation:**

- [ ] Smoke test: All AI responses < 10 seconds
- [ ] Smoke test: All REST API calls < 2 seconds
- [ ] Test retry mechanism works for rate limits
- [ ] Test system recovers from temporary failures

**Documentation & Cleanup:**

- [ ] Create `README.md` for test suite
- [ ] Document test running procedures
- [ ] Document environment setup requirements
- [ ] Clean up old test files and infrastructure
- [ ] Delete deprecated code

**Final Validation:**

- [ ] All tests pass consistently (3 consecutive runs)
- [ ] Test execution time < 5 minutes total
- [ ] No false positives in test results
- [ ] Test output is clear and actionable
- [ ] Test coverage covers all major user scenarios

### 9. **Benefits of This Approach**

1. **Faster test execution** - Simple retry logic, fewer test cases
2. **Easier maintenance** - Less complex infrastructure to maintain
3. **Clearer purpose** - Each test has obvious, focused value
4. **Faster feedback** - Quick to identify when something breaks
5. **Less brittle** - Fewer edge cases means fewer false failures
6. **Focused debugging** - When a test fails, it's easier to identify the issue

### 10. **What You Lose (and why it's OK)**

- **Comprehensive error handling validation** - You'll catch major errors in production anyway
- **Performance monitoring in tests** - Use APM tools for this instead
- **Load testing in unit tests** - Use dedicated load testing tools
- **Edge case coverage** - Focus on fixing real issues users encounter
- **Complex conversational flows** - Most users have simple, direct interactions

This approach gives you 80% of the testing value with 20% of the complexity while maintaining the essential retry mechanism for LLM API stability.
