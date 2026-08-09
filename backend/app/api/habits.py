from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.habits import (
    get_demo_user_id,
    get_user_habits,
    get_habit_by_id,
    create_habit,
    update_habit,
    delete_habit,
    toggle_habit_log,
    get_aggregate_habit_stats,
)

router = APIRouter()


class HabitCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = "general"
    frequency: Optional[str] = "daily"
    target_days_per_week: Optional[int] = 7


class HabitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    frequency: Optional[str] = None
    target_days_per_week: Optional[int] = None
    status: Optional[str] = None


class ToggleRequest(BaseModel):
    date: str


@router.get("", response_model=List[Dict[str, Any]])
async def list_habits() -> List[Dict[str, Any]]:
    user_id = get_demo_user_id()
    return get_user_habits(user_id)


@router.get("/stats", response_model=Dict[str, Any])
async def get_stats() -> Dict[str, Any]:
    user_id = get_demo_user_id()
    return get_aggregate_habit_stats(user_id)


@router.post("", response_model=Dict[str, Any])
async def create_new_habit(payload: HabitCreate) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    try:
        new_habit = create_habit(user_id, payload.model_dump())
        return new_habit
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/{habit_id}", response_model=Dict[str, Any])
async def get_single_habit(habit_id: int) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    habit = get_habit_by_id(habit_id, user_id)
    if not habit:
        raise HTTPException(status_code=404, detail=f"Habit {habit_id} not found.")
    return habit


@router.patch("/{habit_id}", response_model=Dict[str, Any])
async def update_existing_habit(habit_id: int, payload: HabitUpdate) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    updated = update_habit(habit_id, user_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Habit {habit_id} not found.")
    return updated


@router.delete("/{habit_id}", response_model=Dict[str, str])
async def remove_habit(habit_id: int) -> Dict[str, str]:
    user_id = get_demo_user_id()
    deleted = delete_habit(habit_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Habit {habit_id} not found.")
    return {"message": f"Habit {habit_id} deleted successfully."}


@router.post("/{habit_id}/toggle", response_model=Dict[str, Any])
async def toggle_habit_completion(habit_id: int, payload: ToggleRequest) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    try:
        result = toggle_habit_log(habit_id, user_id, payload.date)
        return result
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Toggle failed: {err}")
