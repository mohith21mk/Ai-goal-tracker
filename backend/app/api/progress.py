import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends

from ..services.progress_engine import compute_comprehensive_progress
from .auth import get_current_user

router = APIRouter()


def compute_telemetry_sync(user_id: int) -> Dict[str, Any]:
    """Compute overall lifetime performance telemetry for user_id synchronously."""
    try:
        data = compute_comprehensive_progress(user_id)
        return data["overall"]
    except Exception as e:
        import traceback
        from ..services.logger import logger
        from ..services.progression import get_user_progression
        logger.exception(f"Error computing telemetry for user {user_id}: {e}\n{traceback.format_exc()}")
        prog = get_user_progression(user_id)
        return {
            "discipline_score": 0.0,
            "discipline_score_change": 0.0,
            "mindset_strength": 0.0,
            "mindset_strength_change": 0.0,
            "consistency": 0.0,
            "consistency_change": 0.0,
            "growth_index": 0.0,
            "growth_index_change": 0.0,
            "financial_goal": 0,
            "financial_goal_change": 0.0,
            "financial_goal_pct": 0,
            "active_days": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "streak_days": 0,
            "streak_days_change": 0,
            "missions_completed_change": 0,
            "xp_earned": prog["total_xp"],
            "xp_earned_change": 0,
            "progression": prog,
            "sparklines": {
                "discipline_score": [0, 0, 0, 0, 0, 0, 0],
                "mindset_strength": [0, 0, 0, 0, 0, 0, 0],
                "consistency": [0, 0, 0, 0, 0, 0, 0],
                "growth_index": [0, 0, 0, 0, 0, 0, 0],
                "financial_goal": [0, 0, 0, 0, 0, 0, 0],
                "missions_completed": [0, 0, 0, 0, 0, 0, 0],
                "streak_days": [0, 0, 0, 0, 0, 0, 0],
                "xp_earned": [0, 0, 0, 0, 0, 0, 0],
            },
            "mission_completion": {"completed": 0, "total": 0, "percentage": 0},
            "goals": {"total": 0, "active": 0, "completed": 0},
            "habits": {"active_habits_count": 0, "habits": []},
            "journal": {"total_entries": 0, "journal_streak": 0, "avg_energy_7d": 0.0, "latest_mood": None},
            "blueprint": {"active_blueprint": None, "completion_percentage": 0},
        }


async def compute_telemetry(user_id: int) -> Dict[str, Any]:
    """Compute overall lifetime performance telemetry for user_id."""
    return compute_telemetry_sync(user_id)


@router.get("", response_model=Dict[str, Any])
async def get_progress(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get consolidated progress payload containing both Daily Progress (System 2)
    and Overall Performance Metrics (System 1).
    """
    user_id = current_user["id"]
    data = compute_comprehensive_progress(user_id)
    daily = data["daily"]
    overall = data["overall"]

    return {
        "completed": daily["completed_actions"],
        "total": daily["total_actions"],
        "percentage": daily["completion_percentage"],
        "daily": daily,
        "overall": overall,
    }


@router.get("/daily", response_model=Dict[str, Any])
async def get_daily_progress_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get System 2 — Daily Progress strictly for the current calendar day.
    Resets each new calendar day.
    """
    user_id = current_user["id"]
    data = compute_comprehensive_progress(user_id)
    return data["daily"]


@router.get("/telemetry", response_model=Dict[str, Any])
async def get_telemetry_subroute(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get System 1 — Overall Performance Metrics across user's complete journey.
    Never resets automatically on a new day.
    """
    user_id = current_user["id"]
    data = compute_comprehensive_progress(user_id)
    return data["overall"]
