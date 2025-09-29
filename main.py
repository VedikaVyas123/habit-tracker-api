from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Literal

from models.habit import (
    Habit, 
    CreateHabitRequest, 
    UpdateHabitRequest, 
    StatsResponse, 
    ErrorResponse,
    HabitNotFoundErrorResponse,
    DuplicateCompletionErrorResponse,
    InvalidHabitDataErrorResponse
)
from services.habit_service import (
    HabitService, 
    HabitNotFoundError, 
    DuplicateCompletionError,
    InvalidHabitDataError,
    HabitOperationError,
    HabitServiceError
)
from repositories.habit_repository import HabitRepository

# Create FastAPI app instance
app = FastAPI(
    title="Habit Tracker API",
    description="A REST API for tracking daily habits and maintaining streaks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize repository and service
habit_repository = HabitRepository()
habit_service = HabitService(habit_repository)


# Custom exception handlers
@app.exception_handler(HabitNotFoundError)
async def habit_not_found_handler(request, exc: HabitNotFoundError):
    """Handle habit not found errors with 404 status."""
    return JSONResponse(
        status_code=404,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "habit_id": exc.habit_id
        }
    )


@app.exception_handler(DuplicateCompletionError)
async def duplicate_completion_handler(request, exc: DuplicateCompletionError):
    """Handle duplicate completion errors with 409 status."""
    return JSONResponse(
        status_code=409,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "habit_name": exc.habit_name,
            "completion_date": exc.completion_date
        }
    )


@app.exception_handler(InvalidHabitDataError)
async def invalid_habit_data_handler(request, exc: InvalidHabitDataError):
    """Handle invalid habit data errors with 400 status."""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "field": exc.field,
            "value": exc.value,
            "constraint": exc.constraint
        }
    )


@app.exception_handler(HabitOperationError)
async def habit_operation_handler(request, exc: HabitOperationError):
    """Handle habit operation errors with 400 status."""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "operation": exc.operation,
            "reason": exc.reason
        }
    )


@app.exception_handler(HabitServiceError)
async def habit_service_error_handler(request, exc: HabitServiceError):
    """Handle general habit service errors with 500 status."""
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.message,
            "error_code": exc.error_code or "INTERNAL_SERVICE_ERROR"
        }
    )

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Habit Tracker API is running"}


@app.post("/habits", response_model=Habit, status_code=201, responses={
    400: {"model": InvalidHabitDataErrorResponse, "description": "Invalid habit data"},
    422: {"description": "Validation error"}
})
async def create_habit(request: CreateHabitRequest):
    """
    Create a new habit with validation.
    
    Creates a new habit with the provided name and optional description.
    The habit starts with default values: status=pending, streak_days=0, last_completed_at=null.
    """
    try:
        habit = habit_service.create_habit(request)
        return habit
    except HabitServiceError:
        # Let the custom exception handlers deal with these
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, 
            detail={
                "error": f"An unexpected error occurred while creating the habit: {str(e)}",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )


@app.get("/habits", response_model=List[Habit])
async def get_habits(
    status: Optional[Literal["pending", "completed"]] = Query(
        None, 
        description="Filter habits by status (pending or completed)"
    )
):
    """
    Retrieve all habits with optional status filtering.
    
    Returns all habits or filters by status if provided.
    Returns an empty array if no habits exist.
    """
    try:
        habits = habit_service.get_habits(status=status)
        return habits
    except HabitServiceError:
        # Let the custom exception handlers deal with these
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, 
            detail={
                "error": f"An unexpected error occurred while retrieving habits: {str(e)}",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )


@app.patch("/habits/{habit_id}", response_model=Habit, responses={
    400: {"model": InvalidHabitDataErrorResponse, "description": "Invalid habit data"},
    404: {"model": HabitNotFoundErrorResponse, "description": "Habit not found"},
    422: {"description": "Validation error"}
})
async def update_habit(habit_id: int, request: UpdateHabitRequest):
    """
    Update habit details like name, description, or status.
    
    Updates only the provided fields. Status changes do not affect streak calculations.
    Returns the complete updated habit object.
    """
    try:
        habit = habit_service.update_habit(habit_id, request)
        return habit
    except HabitServiceError:
        # Let the custom exception handlers deal with these
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, 
            detail={
                "error": f"An unexpected error occurred while updating habit {habit_id}: {str(e)}",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )


@app.delete("/habits/{habit_id}", status_code=204, responses={
    400: {"model": InvalidHabitDataErrorResponse, "description": "Invalid habit data"},
    404: {"model": HabitNotFoundErrorResponse, "description": "Habit not found"},
    422: {"description": "Validation error"}
})
async def delete_habit(habit_id: int):
    """
    Delete a habit by its ID.
    
    Removes the habit from storage. Returns 204 on success.
    """
    try:
        habit_service.delete_habit(habit_id)
        return None
    except HabitServiceError:
        # Let the custom exception handlers deal with these
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, 
            detail={
                "error": f"An unexpected error occurred while deleting habit {habit_id}: {str(e)}",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )


@app.post("/habits/{habit_id}/complete", response_model=Habit, responses={
    400: {"model": InvalidHabitDataErrorResponse, "description": "Invalid habit data"},
    404: {"model": HabitNotFoundErrorResponse, "description": "Habit not found"},
    409: {"model": DuplicateCompletionErrorResponse, "description": "Habit already completed today"},
    422: {"description": "Validation error"}
})
async def complete_habit(habit_id: int):
    """
    Mark a habit as completed for today.
    
    Marks the specified habit as completed for the current date.
    Automatically calculates and updates streak based on completion pattern:
    - First completion: streak_days = 1
    - Consecutive day: streak_days += 1  
    - Gap in completion: streak_days = 1 (reset)
    
    Returns the updated habit with new streak information.
    """
    try:
        habit = habit_service.complete_habit_today(habit_id)
        return habit
    except HabitServiceError:
        # Let the custom exception handlers deal with these
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, 
            detail={
                "error": f"An unexpected error occurred while completing habit {habit_id}: {str(e)}",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get habit statistics.
    
    Returns statistics about all habits including:
    - total_habits: Total number of habits
    - completed_today: Number of habits completed today
    - active_streaks_ge_3: Number of habits with streaks >= 3 days
    
    Statistics are calculated dynamically based on current habit states.
    """
    try:
        stats = habit_service.get_stats()
        return stats
    except HabitServiceError:
        # Let the custom exception handlers deal with these
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, 
            detail={
                "error": f"An unexpected error occurred while calculating statistics: {str(e)}",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)