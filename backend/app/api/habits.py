from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..services.habits import (
    create_habit,
    delete_habit,
    get_aggregate_habit_stats,
    get_habit_by_id,
    get_user_habits,
    toggle_habit_log,
    update_habit,
)
from .auth import get_current_user

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
async def list_habits(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    user_id = current_user["id"]
    return get_user_habits(user_id)


@router.get("/stats", response_model=Dict[str, Any])
async def get_stats(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = current_user["id"]
    return get_aggregate_habit_stats(user_id)


@router.post("", response_model=Dict[str, Any])
async def create_new_habit(
    payload: HabitCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    try:
        new_habit = create_habit(user_id, payload.model_dump())
        return new_habit
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/{habit_id}", response_model=Dict[str, Any])
async def get_single_habit(
    habit_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    habit = get_habit_by_id(habit_id, user_id)
    if not habit:
        raise HTTPException(status_code=404, detail=f"Habit {habit_id} not found.")
    return habit


@router.patch("/{habit_id}", response_model=Dict[str, Any])
async def update_existing_habit(
    habit_id: int,
    payload: HabitUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    updated = update_habit(habit_id, user_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Habit {habit_id} not found.")
    return updated


@router.delete("/{habit_id}", response_model=Dict[str, str])
async def remove_habit(
    habit_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    user_id = current_user["id"]
    deleted = delete_habit(habit_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Habit {habit_id} not found.")
    return {"message": f"Habit {habit_id} deleted successfully."}


@router.post("/{habit_id}/toggle", response_model=Dict[str, Any])
async def toggle_habit_completion(
    habit_id: int,
    payload: ToggleRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    try:
        result = toggle_habit_log(habit_id, user_id, payload.date)
        return result
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Toggle failed: {err}")
