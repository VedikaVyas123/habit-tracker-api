# Design Document

## Overview

The Habit Tracker API is a FastAPI-based REST service that provides habit management and streak tracking functionality. The system uses in-memory storage with Pydantic models for data validation and automatic OpenAPI documentation generation. The architecture follows REST principles with clear separation between data models, business logic, and API endpoints.

## Architecture

The application follows a layered architecture pattern:

```
┌─────────────────────────────────────┐
│           API Layer                 │
│        (FastAPI Routes)             │
├─────────────────────────────────────┤
│         Service Layer               │
│      (Business Logic)               │
├─────────────────────────────────────┤
│         Data Layer                  │
│     (In-Memory Storage)             │
└─────────────────────────────────────┘
```

### Key Architectural Decisions

1. **FastAPI Framework**: Chosen for automatic OpenAPI documentation, built-in validation with Pydantic, and excellent performance
2. **In-Memory Storage**: Simple dictionary-based storage for habits with auto-incrementing IDs
3. **Pydantic Models**: Used for request/response validation and serialization
4. **Service Layer**: Encapsulates business logic for habit management and streak calculations
5. **Date Handling**: Uses Python's `date` type for consistent date operations

## Components and Interfaces

### Data Models

#### Habit Model
```python
class Habit(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=280)
    status: Literal["pending", "completed"] = "pending"
    streak_days: int = Field(default=0, ge=0)
    last_completed_at: Optional[date] = None
```

#### Request/Response Models
```python
class CreateHabitRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=280)

class UpdateHabitRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=280)
    status: Optional[Literal["pending", "completed"]] = None

class StatsResponse(BaseModel):
    total_habits: int
    completed_today: int
    active_streaks_ge_3: int
```

### Service Layer

#### HabitService
Handles all business logic for habit operations:

- **create_habit()**: Creates new habits with default values
- **get_habits()**: Retrieves habits with optional status filtering
- **update_habit()**: Updates habit fields without affecting streaks
- **delete_habit()**: Removes habits from storage
- **complete_habit_today()**: Handles completion logic and streak calculations
- **get_stats()**: Calculates and returns habit statistics

#### Streak Calculation Logic
The streak calculation follows these rules:
1. First completion: streak_days = 1, last_completed_at = today
2. Consecutive day completion: streak_days += 1
3. Gap in completion: streak_days = 1 (reset)
4. Same day completion: Return 409 error

### Storage Layer

#### HabitRepository
Manages in-memory data storage:

```python
class HabitRepository:
    def __init__(self):
        self._habits: Dict[int, Habit] = {}
        self._next_id: int = 1
    
    def create(self, habit_data: dict) -> Habit
    def get_by_id(self, habit_id: int) -> Optional[Habit]
    def get_all(self) -> List[Habit]
    def update(self, habit_id: int, updates: dict) -> Optional[Habit]
    def delete(self, habit_id: int) -> bool
```

### API Layer

#### Route Structure
- `POST /habits` - Create new habit
- `GET /habits` - List habits with optional status filter
- `PATCH /habits/{id}` - Update habit details
- `DELETE /habits/{id}` - Delete habit
- `POST /habits/{id}/complete` - Mark habit completed for today
- `GET /stats` - Get habit statistics
- `GET /docs` - OpenAPI documentation (automatic)

## Data Models

### Core Entities

#### Habit Entity
- **id**: Auto-incrementing integer primary key
- **name**: Required string (1-80 characters)
- **description**: Optional string (max 280 characters)
- **status**: Enum ["pending", "completed"]
- **streak_days**: Non-negative integer representing consecutive completion days
- **last_completed_at**: Optional date of last completion

### Data Relationships
- No complex relationships required (single entity system)
- All data stored in a single dictionary keyed by habit ID

### Data Validation Rules
1. Name must be 1-80 characters
2. Description must be ≤280 characters if provided
3. Status must be "pending" or "completed"
4. Streak days must be ≥0
5. Dates must be valid ISO format (YYYY-MM-DD)

## Error Handling

### HTTP Status Codes
- **200**: Successful GET/PATCH/POST operations
- **201**: Successful habit creation
- **204**: Successful deletion
- **400**: Invalid request data or validation errors
- **404**: Habit not found
- **409**: Conflict (e.g., completing habit twice same day)

### Error Response Format
```python
class ErrorResponse(BaseModel):
    error: str
```

### Exception Handling Strategy
1. **Validation Errors**: Automatically handled by FastAPI/Pydantic
2. **Business Logic Errors**: Custom exceptions with appropriate HTTP status codes
3. **Not Found Errors**: Return 404 with descriptive error message
4. **Conflict Errors**: Return 409 for business rule violations

## Testing Strategy

### Unit Tests
- **Model Tests**: Validate Pydantic model behavior and constraints
- **Service Tests**: Test business logic including streak calculations
- **Repository Tests**: Verify data storage and retrieval operations

### Integration Tests
- **API Endpoint Tests**: Test complete request/response cycles
- **Error Handling Tests**: Verify proper error responses
- **Business Flow Tests**: Test multi-step operations (create → complete → stats)

### Test Scenarios
1. **Happy Path**: Create habit → complete daily → verify streak increment
2. **Streak Reset**: Complete habit → skip day → complete → verify reset
3. **Duplicate Completion**: Complete habit twice same day → verify 409 error
4. **Data Validation**: Submit invalid data → verify 400 errors
5. **Statistics Accuracy**: Create/complete habits → verify stats calculations

### Test Data Management
- Use pytest fixtures for consistent test data setup
- Reset in-memory storage between tests
- Mock date/time for consistent streak testing

### Coverage Requirements
- Minimum 90% code coverage
- All business logic paths tested
- All error conditions tested
- All API endpoints tested