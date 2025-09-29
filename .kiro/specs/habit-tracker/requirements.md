# Requirements Document

## Introduction

The Habit Tracker API is a REST API system designed to help users track their daily habits and maintain streaks. The system allows users to create, manage, and complete habits while automatically calculating streak counts based on consecutive daily completions. The API provides endpoints for habit management, completion tracking, and statistics reporting.

## Requirements

### Requirement 1

**User Story:** As a user, I want to create new habits with names and optional descriptions, so that I can start tracking behaviors I want to develop.

#### Acceptance Criteria

1. WHEN a user submits a POST request to /habits with a valid name THEN the system SHALL create a new habit with default values (status=pending, streak_days=0, last_completed_at=null)
2. WHEN a user provides an optional description THEN the system SHALL store the description with a maximum length of 280 characters
3. WHEN a user provides a name longer than 80 characters THEN the system SHALL return a 400 error
4. WHEN a habit is successfully created THEN the system SHALL return a 201 status with the complete habit object including auto-generated ID

### Requirement 2

**User Story:** As a user, I want to view all my habits with optional filtering by status, so that I can see my current progress and manage my habit list.

#### Acceptance Criteria

1. WHEN a user requests GET /habits THEN the system SHALL return all habits with their current status, streak count, and last completion date
2. WHEN a user provides a status query parameter THEN the system SHALL filter habits by the specified status (pending or completed)
3. WHEN no habits exist THEN the system SHALL return an empty array with 200 status

### Requirement 3

**User Story:** As a user, I want to update habit details like name and description, so that I can refine my habit definitions over time.

#### Acceptance Criteria

1. WHEN a user submits a PATCH request to /habits/{id} with valid fields THEN the system SHALL update only the provided fields
2. WHEN a user updates the status field THEN the system SHALL change the status but NOT affect streak calculations
3. WHEN a user tries to update a non-existent habit THEN the system SHALL return a 404 error
4. WHEN an update is successful THEN the system SHALL return the complete updated habit object

### Requirement 4

**User Story:** As a user, I want to delete habits I no longer want to track, so that I can keep my habit list relevant and manageable.

#### Acceptance Criteria

1. WHEN a user submits a DELETE request to /habits/{id} for an existing habit THEN the system SHALL remove the habit and return 204 status
2. WHEN a user tries to delete a non-existent habit THEN the system SHALL return a 404 error

### Requirement 5

**User Story:** As a user, I want to mark habits as completed for today, so that I can track my daily progress and build streaks.

#### Acceptance Criteria

1. WHEN a user completes a habit for the first time THEN the system SHALL set status=completed, streak_days=1, and last_completed_at=today
2. WHEN a user completes a habit on consecutive days THEN the system SHALL increment streak_days by 1
3. WHEN a user completes a habit after missing one or more days THEN the system SHALL reset streak_days to 1
4. WHEN a user tries to complete the same habit twice on the same day THEN the system SHALL return a 409 error
5. WHEN a user tries to complete a non-existent habit THEN the system SHALL return a 404 error

### Requirement 6

**User Story:** As a user, I want to view statistics about my habits, so that I can understand my overall progress and motivation.

#### Acceptance Criteria

1. WHEN a user requests GET /stats THEN the system SHALL return total_habits count
2. WHEN a user requests GET /stats THEN the system SHALL return completed_today count for habits completed on the current date
3. WHEN a user requests GET /stats THEN the system SHALL return active_streaks_ge_3 count for habits with streak_days >= 3

### Requirement 7

**User Story:** As a developer, I want the API to have proper validation and documentation, so that it's reliable and easy to integrate with.

#### Acceptance Criteria

1. WHEN the API is running THEN the system SHALL provide OpenAPI documentation at /docs endpoint
2. WHEN invalid data is submitted THEN the system SHALL return appropriate 400 errors with descriptive messages
3. WHEN the API processes requests THEN the system SHALL use Pydantic models for request/response validation
4. WHEN the API code is written THEN the system SHALL include proper type hints throughout

### Requirement 8

**User Story:** As a developer, I want the system to use in-memory storage, so that it's simple to deploy and test without external dependencies.

#### Acceptance Criteria

1. WHEN the API starts THEN the system SHALL use only in-memory data structures (dictionaries and lists)
2. WHEN the API is deployed THEN the system SHALL NOT require any external database connections
3. WHEN the API restarts THEN the system SHALL start with empty data (no persistence required)