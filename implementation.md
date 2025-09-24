# Implementation Guide: Analytics to Forecast Optimization System

## Overview

This implementation converts the existing analytics-focused system into a schedule optimization platform. The current system analyzes historical data and generates reports, but the actual business requirement is to optimize future cinema schedules using AI-powered forecasting.

### Business Problem
Cinema operators need to maximize revenue and occupancy by intelligently scheduling movies across their theater network. Rather than manually creating schedules or analyzing past performance, they need a system that:
- Generates optimized schedules for future time periods
- Predicts occupancy and revenue outcomes 
- Allows "what-if" scenario planning through multiple forecasts
- Provides confidence metrics for business decision making

### Solution Approach
Transform the system from retrospective analytics to predictive optimization:

**Before (Analytics Focus):**
- Analyzed historical schedule performance
- Generated revenue and occupancy reports
- Provided insights on past trends

**After (Optimization Focus):**
- AI generates optimized schedules for specified date ranges
- Creates predictions about occupancy, revenue, and operational metrics
- Maintains multiple forecast scenarios for comparison
- Prepares foundation for future ML model integration

### Key Changes
1. **New Data Model**: Forecasts contain generated schedules with predictions, replacing standalone analytics
2. **AI-Driven Generation**: The AI assistant becomes the primary trigger for schedule optimization
3. **Future-Focused**: System generates upcoming schedules rather than analyzing past performance
4. **Scenario Planning**: Multiple forecasts allow comparison of different optimization strategies
5. **Mock Algorithm**: Simple realistic schedule generation prepares for future ML model replacement

The system maintains all existing movie and cinema management capabilities while pivoting the core workflow from analysis to optimization.

---

## Phase 1: Analytics System Removal
**Goal**: Clean removal of existing analytics system to avoid conflicts

### Checklist
- [x] Delete `app/services/analytics_service.py`
- [x] Delete `app/api/analytics.py`
- [x] Remove analytics imports from `app/services/__init__.py`
- [x] Remove analytics imports and router from `main.py`
- [x] Update `app/gemini/function_schemas.py`:
  - [x] Remove all ANALYTICS_FUNCTIONS
  - [x] Remove analytics from FUNCTION_CATEGORIES
  - [x] Update ALL_FUNCTIONS to exclude analytics
- [x] Update `app/gemini/function_executor.py`:
  - [x] Remove analytics function execution methods
  - [x] Remove analytics mapping from function_map
- [x] Test application still runs without analytics components
- [x] Verify movies, cinemas, and existing schedules APIs still work

---

## Phase 2: Database Migration ✅ COMPLETED
**Goal**: Set up new database schema and modify existing tables

### Checklist
- [x] Create Alembic migration file
- [x] Add `forecasts` table with columns:
  - [x] `id` (UUID, PK)
  - [x] `name` (VARCHAR, NOT NULL)
  - [x] `description` (TEXT, nullable)
  - [x] `date_range_start` (TIMESTAMP, NOT NULL)
  - [x] `date_range_end` (TIMESTAMP, NOT NULL)
  - [x] `status` (VARCHAR(20), DEFAULT 'generating')
  - [x] `optimization_parameters` (JSONB, nullable)
  - [x] `created_at` (TIMESTAMP, DEFAULT NOW())
  - [x] `created_by` (VARCHAR, NOT NULL)
  - [x] `total_schedules_generated` (INTEGER, DEFAULT 0)
- [x] Add `prediction_data` table with columns:
  - [x] `id` (UUID, PK)
  - [x] `forecast_id` (UUID, FK to forecasts, CASCADE DELETE)
  - [x] `metrics` (JSONB, NOT NULL)
  - [x] `confidence_score` (FLOAT, NOT NULL)
  - [x] `error_margin` (FLOAT, NOT NULL)
  - [x] `created_at` (TIMESTAMP, DEFAULT NOW())
- [x] Modify `schedules` table:
  - [x] Add `forecast_id` (UUID, nullable FK to forecasts, CASCADE DELETE)
  - [x] Create index `idx_schedules_forecast` on `forecast_id`
- [x] Run migration and verify existing schedules remain unaffected

### Migration Results
- **Migration File**: `0edb4b07b264_add_forecast_system_tables.py`
- **Database Verification**: ✅ All 876 existing schedules retain NULL forecast_id for backward compatibility
- **Schema Validation**: ✅ All tables, columns, foreign keys, and indexes created successfully
- **Relationships**: ✅ Forecast ↔ Schedule ↔ PredictionData relationships established

---

## Phase 3: Model Creation ✅ COMPLETED
**Goal**: Create SQLAlchemy models for new tables

### Checklist
- [x] Create `app/models/forecast.py`
  - [x] `Forecast` model with all fields
  - [x] Relationships to schedules and predictions
  - [x] Proper imports and base class inheritance
- [x] Update `app/models/forecast.py`
  - [x] `PredictionData` model with all fields
  - [x] Relationship back to forecast
- [x] Update `app/models/schedule.py`
  - [x] Add `forecast_id` column
  - [x] Add relationship to forecast
- [x] Update `app/models/__init__.py`
  - [x] Import and export new models

### Models Created
- **Forecast**: Complete model with all fields, relationships to Schedule and PredictionData
- **PredictionData**: Complete model with forecast relationship and JSONB metrics storage
- **Schedule**: Updated with optional forecast_id and forecast relationship
- **__init__.py**: Updated to export Forecast and PredictionData models

---

## Phase 4: Service Development ✅ COMPLETED
**Goal**: Create business logic services for forecast system

### 4a: Forecast Service ✅ COMPLETED
#### Checklist
- [x] Create `app/services/forecast_service.py`
- [x] Implement `ForecastService` class with methods:
  - [x] `create_forecast(date_range_start, date_range_end, params=None, created_by="user")`
    - [x] Auto-generate name: `"Forecast {start_date} to {end_date}"`
    - [x] Set status to 'generating'
    - [x] Store optimization parameters
  - [x] `get_all_forecasts()` - return all forecasts
  - [x] `get_forecast_by_id(forecast_id)` - single forecast with details
  - [x] `delete_forecast(forecast_id)` - cascade delete schedules
  - [x] `update_forecast_status(forecast_id, status)` - update status
  - [x] `get_forecast_schedules(forecast_id)` - get associated schedules
  - [x] `get_forecast_predictions(forecast_id)` - get prediction data

### 4b: Optimization Service ✅ COMPLETED
#### Checklist
- [x] Create `app/services/optimization_service.py`
- [x] Implement `OptimizationService` class with methods:
  - [x] `generate_schedules_for_forecast(forecast)` - main entry point
  - [x] `_get_available_movies()` - helper to get movie catalog
  - [x] `_get_available_cinemas()` - helper to get cinema list
  - [x] `_generate_time_slots(start_date, end_date)` - create time slots
  - [x] `_create_realistic_schedule(movie, cinema, time_slot)` - single schedule
  - [x] `_calculate_pricing(cinema_type, time_slot)` - realistic pricing
  - [x] `_apply_parameters(schedules, params)` - apply optimization params
- [x] Parameter validation:
  - [x] `revenue_goal`: 0.5 to 2.0 multiplier (default 1.0)
  - [x] `occupancy_goal`: 0.3 to 0.9 target rate (default 0.7)
  - [x] `movie_preferences`: dict with movie_id -> weight 0.1-2.0

### 4c: Prediction Service ✅ COMPLETED
#### Checklist
- [x] Create `app/services/prediction_service.py`
- [x] Implement `PredictionService` class with methods:
  - [x] `generate_predictions(forecast_id, schedules)` - main entry point
  - [x] `_calculate_schedule_metrics(schedules)` - shows, cinemas, days, etc.
  - [x] `_calculate_occupancy_metrics(schedules)` - aggregate occupancy
  - [x] `_calculate_revenue_metrics(schedules)` - aggregate revenue
  - [x] `_generate_confidence_score()` - mock confidence (70-85%)
  - [x] `_calculate_error_margin()` - mock error margin (10-20%)
  - [x] `_format_metrics_json(schedule_metrics, forecast_metrics)` - final JSON

### 4d: Service Integration ✅ COMPLETED
#### Checklist
- [x] Update `app/services/__init__.py` to export new services
- [x] Create service orchestration in `ForecastService`:
  - [x] Link optimization and prediction services
  - [x] Handle status updates during generation
  - [x] Error handling and rollback on failure

### Implementation Results
- **Services Created**: ForecastService, OptimizationService, PredictionService
- **Import Verification**: ✅ All services import successfully via Poetry
- **Method Testing**: ✅ Parameter validation and metrics formatting work correctly
- **Service Integration**: Complete forecast workflow with orchestration methods:
  - `generate_complete_forecast()` - Full forecast creation and optimization
  - `regenerate_forecast()` - Re-run optimization for existing forecasts
- **Mock Algorithm Features**:
  - Time slot generation (9 AM - 11 PM, 30-min intervals)
  - Prime time movie selection (6-10 PM preference)
  - Realistic pricing with cinema type and time-based multipliers
  - Occupancy simulation with weekend/prime time bonuses
  - Parameter application for revenue goals and preferences

---

## Phase 5: API Development
**Goal**: Create forecast API and modify schedules API

### 5a: Forecast API
#### Checklist
- [ ] Create `app/api/forecasts.py`
- [ ] Implement endpoints:
  - [ ] `GET /api/forecasts` - list all forecasts
  - [ ] `POST /api/forecasts` - create and trigger optimization
  - [ ] `GET /api/forecasts/{id}` - get forecast details
  - [ ] `DELETE /api/forecasts/{id}` - delete forecast
  - [ ] `GET /api/forecasts/{id}/schedules` - get schedules for forecast
  - [ ] `GET /api/forecasts/{id}/predictions` - get prediction data  
  - [ ] `POST /api/forecasts/{id}/regenerate` - re-run optimization
- [ ] Add request/response models using Pydantic
- [ ] Add proper error handling and HTTP status codes

### 5b: Schedule API Modifications
#### Checklist
- [ ] Modify `app/api/schedules.py`:
  - [ ] Add deprecation warnings to direct schedule creation endpoints
  - [ ] Modify `GET /api/schedules` to include forecast context
  - [ ] Add `forecast_id` filter parameter
  - [ ] Add forecast information to schedule responses
  - [ ] Keep backward compatibility for existing non-forecasted schedules
- [ ] Update schedule response format to include forecast details
- [ ] Add forecast context to all schedule operations

### 5c: API Integration
#### Checklist
- [ ] Add forecast router to `main.py`
- [ ] Update CORS settings if needed
- [ ] Update health check endpoint
- [ ] Remove analytics router import and registration

---

## Phase 6: AI Integration Updates
**Goal**: Update Gemini AI integration for forecast system

### 6a: Function Schema Updates
#### Checklist
- [ ] Update `app/gemini/function_schemas.py`:
  - [ ] Remove all analytics functions
  - [ ] Add forecast functions:
    - [ ] `create_forecast` - create new forecast with optimization
    - [ ] `get_all_forecasts` - list existing forecasts
    - [ ] `get_forecast_details` - get specific forecast info
    - [ ] `get_forecast_schedules` - get schedules for forecast
    - [ ] `get_forecast_predictions` - get prediction data
    - [ ] `regenerate_forecast` - re-run optimization
  - [ ] Update function categories and mappings

### 6b: Function Executor Updates  
#### Checklist
- [ ] Update `app/gemini/function_executor.py`:
  - [ ] Remove analytics function execution methods
  - [ ] Add forecast function execution methods:
    - [ ] `_execute_forecast_function()` - route forecast functions
    - [ ] Handle all forecast function calls properly
  - [ ] Update function mapping dictionary

### 6c: AI System Updates
#### Checklist
- [ ] Update `app/gemini/client.py` system instructions:
  - [ ] Change focus from analytics to schedule optimization
  - [ ] Update AI role description to "schedule optimization assistant"
  - [ ] Update examples and capabilities description
- [ ] Test AI can create and manage forecasts through chat

---

## Phase 7: Cleanup and Migration
**Goal**: Remove analytics system and finalize changes

### 7a: File Removal
#### Checklist
- [ ] Delete `app/services/analytics_service.py`
- [ ] Delete `app/api/analytics.py` 
- [ ] Remove analytics imports from `app/services/__init__.py`
- [ ] Remove analytics imports from `main.py`

### 7b: Final Integration
#### Checklist  
- [ ] Update all import statements across the codebase
- [ ] Update error handling and logging messages
- [ ] Verify cascade deletion works properly
- [ ] Test forecast creation through AI chat
- [ ] Test forecast creation through API
- [ ] Verify existing functionality (movies, cinemas) still works
- [ ] Update notification system to handle forecast events

### 7c: Documentation Updates
#### Checklist
- [ ] Update API documentation
- [ ] Update system architecture documentation  
- [ ] Update AI assistant capabilities description
- [ ] Document new forecast workflow

---

## Key Implementation Notes

### Mock Algorithm Guidelines
- Generate time slots every 30 minutes from 9 AM to 11 PM
- Assign popular movies to prime time slots (6-10 PM) with higher occupancy
- Fill remaining slots with varied movie selection
- Apply realistic occupancy rates: prime time 50-80%, off-peak 20-50%
- Use cinema type multipliers for pricing calculations
- Add controlled randomization to avoid perfect patterns

### Parameter Application
- `revenue_goal`: Apply as multiplier to base pricing calculations
- `occupancy_goal`: Adjust occupancy rate generation towards target
- `movie_preferences`: Weight movie selection probability during assignment

### Metrics JSON Structure
Store in `prediction_data.metrics`:
```json
{
  "schedule": {
    "shows": 112,
    "cinemas": 10,
    "days": 7, 
    "movies": 16,
    "new_movies": 3,
    "efficiency_percent": 68,
    "cleanup_minutes": 235,
    "usable_minutes": 128
  },
  "forecast": {
    "occupancy": {
      "sold": 4040,
      "total": 11189,
      "percent": 37
    },
    "revenue": 11119.9,
    "confidence_percent": 78,
    "error_margin_percent": 15
  }
}
```

### Status Flow
1. **generating**: Forecast created, optimization in progress
2. **completed**: Schedules and predictions generated successfully
3. **failed**: Error during generation process