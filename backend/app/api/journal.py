from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from ..services.journal import (
    compute_journal_stats,
    delete_journal_entry,
    generate_journal_ai_analysis,
    get_journal_entry_by_id,
    get_journal_history,
    get_today_journal_entry,
    upsert_journal_entry,
)
from .auth import get_current_user

router = APIRouter()

ALLOWED_MOODS = {"energized", "focused", "neutral", "challenged", "exhausted"}


class JournalUpsertRequest(BaseModel):
    entry_date: Optional[str] = None
    mood: Optional[str] = "focused"
    energy_level: Optional[int] = 7
    wins_text: Optional[str] = ""
    challenges_text: Optional[str] = ""
    learnings_text: Optional[str] = ""
    growth_next_text: Optional[str] = ""
    analyze: Optional[bool] = False

    @field_validator("mood")
    @classmethod
    def validate_mood(cls, v: Optional[str]) -> str:
        if v and v.lower() not in ALLOWED_MOODS:
            raise ValueError(f"Invalid mood. Allowed moods: {', '.join(sorted(ALLOWED_MOODS))}")
        return (v or "focused").lower()

    @field_validator("energy_level")
    @classmethod
    def validate_energy(cls, v: Optional[int]) -> int:
        if v is not None and (v < 1 or v > 10):
            raise ValueError("Energy level must be between 1 and 10.")
        return v or 7

    @field_validator("entry_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v:
            try:
                dt = datetime.strptime(v, "%Y-%m-%d").date()
                if dt > datetime.now(timezone.utc).date():
                    raise ValueError("Cannot log journal reflections for future dates.")
            except ValueError as err:
                if "Cannot log" in str(err):
                    raise err
                raise ValueError("Invalid date format. Expected YYYY-MM-DD.")
        return v


@router.get("/today", response_model=Dict[str, Any])
async def fetch_today_entry(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = current_user["id"]
    entry = get_today_journal_entry(user_id)
    return {"entry": entry}


@router.get("/history", response_model=Dict[str, Any])
async def fetch_history(
    limit: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    safe_limit = max(1, min(100, limit))
    entries = get_journal_history(user_id, safe_limit)
    return {"entries": entries, "count": len(entries)}


@router.get("/stats", response_model=Dict[str, Any])
async def fetch_stats(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = current_user["id"]
    return compute_journal_stats(user_id)


@router.post("", response_model=Dict[str, Any])
async def save_journal_reflection(
    payload: JournalUpsertRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    try:
        data = payload.model_dump()
        should_analyze = data.pop("analyze", False)

        saved_entry = upsert_journal_entry(user_id, data)

        if should_analyze:
            try:
                analysis_res = await generate_journal_ai_analysis(saved_entry["id"], user_id)
                saved_entry = analysis_res["entry"]
            except Exception as err:
                print(f"AI analysis trigger warning: {err}")

        return {"entry": saved_entry}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to save journal entry: {err}")


@router.post("/{entry_id}/analyze", response_model=Dict[str, Any])
async def analyze_entry(
    entry_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    try:
        result = await generate_journal_ai_analysis(entry_id, user_id)
        return result
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"AI reflection analysis failed: {err}")


@router.delete("/{entry_id}", response_model=Dict[str, str])
async def remove_entry(
    entry_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    user_id = current_user["id"]
    deleted = delete_journal_entry(entry_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found.")
    return {"message": f"Journal entry {entry_id} deleted successfully."}
