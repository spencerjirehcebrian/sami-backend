# SAMi Backend Prompt Testing Framework

A comprehensive end-to-end testing framework for validating the natural language processing pipeline in the SAMi cinema management system.

## Overview

This testing framework validates that user prompts are correctly understood, processed, and executed through the AI pipeline from WebSocket input to database operations and responses.

## Pipeline Architecture Tested

```
User Prompt → WebSocket Handler → Message Processor → Gemini AI → Function Executor → Services → Database → Response
```

## Installation

1. Ensure you have the required dependencies:
```bash
cd sami-backend
poetry install
```

2. Make sure the backend server is running:
```bash
poetry run python app/main.py
```

3. Ensure the database is seeded with test data:
```bash
poetry run python alembic/seed.py
```

## Test Categories

### 1. **Cinema Management Tests** (`test_cinema_management.py`)
- Cinema information queries
- Capacity and availability checks
- Cinema comparisons and recommendations
- Status and maintenance queries

### 2. **Movie Management Tests** (`test_movie_management.py`)
- Movie search and filtering (genre, rating, duration)
- Movie information queries
- CRUD operations (create, update, delete movies)
- Movie recommendations

### 3. **Schedule Management Tests** (`test_schedule_management.py`)
- Schedule creation and modification
- Availability checking
- Conflict detection and resolution
- Schedule queries by movie/cinema/time

### 4. **Analytics Tests** (`test_analytics.py`)
- Revenue reporting (daily, weekly, by cinema/movie)
- Occupancy analysis
- Performance metrics and KPIs
- Comparative analysis and forecasting

### 5. **Error Handling Tests** (`test_error_handling.py`)
- Invalid requests (non-existent cinemas, invalid dates)
- Ambiguous requests (missing information)
- Edge cases and system limits
- Recovery from errors

### 6. **Context and Follow-up Tests** (`test_context.py`)
- Conversational context maintenance
- Pronoun and reference resolution
- Multi-turn conversations
- Context switching

## Usage

### Quick Start - Run All Tests
```bash
# Run all test categories
python tests/run_prompt_tests.py --all

# Run smoke tests only (fastest)
python tests/run_prompt_tests.py --smoke
```

### Run Specific Test Categories
```bash
# Cinema management tests
python tests/run_prompt_tests.py --category cinema

# Movie management tests
python tests/run_prompt_tests.py --category movie

# Schedule management tests
python tests/run_prompt_tests.py --category schedule

# Analytics tests
python tests/run_prompt_tests.py --category analytics

# Error handling tests
python tests/run_prompt_tests.py --category error

# Context and follow-up tests
python tests/run_prompt_tests.py --category context
```

### Performance and Load Testing
```bash
# Run performance benchmarks
python tests/run_prompt_tests.py --performance

# Run load tests with custom parameters
python tests/run_prompt_tests.py --load-test --concurrent-users 10 --requests-per-user 5
```

### Using Pytest Directly
```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_cinema_management.py
pytest tests/test_movie_management.py

# Run tests with specific markers
pytest -m "smoke"
pytest -m "cinema and not performance"
pytest -m "error"

# Run with verbose output
pytest -v tests/

# Run with coverage
pytest --cov=app tests/
```

## Test Structure

### Core Components

- **`prompt_tester.py`** - Core PromptTester class for WebSocket communication
- **`conftest.py`** - Pytest configuration, fixtures, and shared test data
- **`utils.py`** - Test utilities, data generators, and reporting tools
- **`run_prompt_tests.py`** - Main test runner with comprehensive reporting

### Test Data

Tests use a combination of:
- **Fixture data** - Predefined test prompts and expected responses
- **Generated data** - Dynamically created test data for various scenarios
- **Seeded database** - Consistent test data from `alembic/seed.py`

## Example Test Cases

### Cinema Management
```python
# Basic cinema query
"Show me all cinemas"
"What's the capacity of Cinema 1?"
"Which theaters are available tonight?"

# Advanced cinema queries
"Which cinema is best for a date?"
"Compare Cinema 1 and Cinema 2"
"Are all cinemas operational?"
```

### Movie Management
```python
# Movie search
"Find all action movies"
"Show me PG-13 movies"
"List movies under 2 hours"

# Movie operations
"Add a new movie called 'Test Film' that's 120 minutes long"
"Tell me about Avatar"
"Which movies are most popular?"
```

### Schedule Management
```python
# Schedule creation
"Schedule Avatar for Cinema 1 tomorrow at 8 PM with ticket price $15"
"What time slots are available for Cinema 1 tomorrow?"

# Schedule queries
"When is Inception playing?"
"What's scheduled for today?"
"Change the 8 PM Avatar showing to 9 PM"
```

### Analytics
```python
# Revenue queries
"Show me today's revenue"
"What was our revenue this week?"
"How much did Avatar generate?"

# Occupancy queries
"What's our occupancy rate today?"
"Which cinemas have the best attendance?"
"Show me occupancy trends this month"
```

## Response Validation

Each test validates multiple aspects:

### Response Structure
- Valid JSON format
- Required fields (type, content, timestamp)
- Proper timestamp format
- Session ID tracking

### AI Processing Indicators
- `ai_powered: true` in metadata
- Function calls made tracking
- Handler information
- Processing time metrics

### Content Quality
- Relevant keywords present
- Appropriate response length
- Context-aware responses
- Error handling quality

## Performance Benchmarks

### Response Time Thresholds
- **Fast Response**: < 2 seconds (simple queries)
- **Normal Response**: < 5 seconds (complex operations)
- **Slow Response**: < 10 seconds (heavy analytics)

### Load Testing
- **Concurrent Users**: 5-10 simultaneous sessions
- **Success Rate**: > 95% for normal operations
- **Error Recovery**: System should recover gracefully

## Reporting

### Automatic Reports
- **Summary Report**: Overall test results and success rates
- **Detailed Report**: Individual test results with timing
- **Performance Report**: Response time analysis
- **Load Test Report**: Concurrent user performance

### Report Formats
- Console output with colored indicators
- Log files with detailed timing
- Text files for archival
- JSON format for integration

## Troubleshooting

### Common Issues

**Backend Not Available**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend
poetry run python app/main.py
```

**Database Issues**
```bash
# Re-seed database
poetry run python alembic/seed.py

# Check database connection
# Verify DATABASE_URL in .env
```

**WebSocket Connection Failed**
```bash
# Check WebSocket endpoint
# Verify port 8000 is not blocked
# Check firewall settings
```

**Test Timeouts**
```bash
# Increase timeout in test configuration
# Check backend performance
# Verify Gemini API connectivity
```

### Debug Mode
```bash
# Run with debug logging
PYTHONPATH=. python tests/run_prompt_tests.py --smoke --verbose

# Individual test debugging
pytest tests/test_cinema_management.py::TestCinemaQueries::test_get_all_cinemas_variations -v -s
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: SAMi Prompt Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Start backend
        run: |
          poetry run python app/main.py &
          sleep 10
      - name: Run prompt tests
        run: |
          poetry run python tests/run_prompt_tests.py --smoke
```

## Contributing

When adding new tests:

1. **Follow naming conventions**: `test_<category>_<functionality>.py`
2. **Use appropriate markers**: `@pytest.mark.category`
3. **Add test data to fixtures**: Update `conftest.py`
4. **Document test purpose**: Clear docstrings
5. **Validate all response aspects**: Structure, content, performance
6. **Handle errors gracefully**: Use appropriate expect methods

## Performance Optimization

For faster test execution:

1. **Use smoke tests** for quick validation
2. **Run specific categories** instead of all tests
3. **Parallel execution** with pytest-xdist
4. **Mock external services** when appropriate
5. **Cache test data** between runs

## Monitoring and Alerting

Set up monitoring for:
- Test execution duration
- Success/failure rates
- Performance degradation
- Error patterns
- Resource usage during tests

This framework ensures the SAMi AI pipeline correctly processes natural language inputs and produces accurate responses for cinema management operations.