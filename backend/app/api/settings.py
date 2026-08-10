import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator

from ..services.habits import get_demo_user_id
from ..services.settings import get_or_create_user_settings, update_user_settings

router = APIRouter()


class SettingsUpdateRequest(BaseModel):
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    coach_style: Optional[str] = None
    daily_reminder_time: Optional[str] = None
    profile_visibility: Optional[str] = None

    @validator("theme")
    def validate_theme(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.lower() not in ("dark", "light"):
            raise ValueError("Theme must be 'dark' or 'light'")
        return v.lower() if v else v

    @validator("coach_style")
    def validate_coach_style(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.lower() not in ("strategic", "empathetic", "relentless"):
            raise ValueError("Coach style must be 'strategic', 'empathetic', or 'relentless'")
        return v.lower() if v else v

    @validator("profile_visibility")
    def validate_profile_visibility(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.lower() not in ("public", "private"):
            raise ValueError("Profile visibility must be 'public' or 'private'")
        return v.lower() if v else v

    @validator("daily_reminder_time")
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
                raise ValueError("Daily reminder time must be in HH:MM 24-hour format")
        return v


@router.get("", response_model=Dict[str, Any])
async def get_settings() -> Dict[str, Any]:
    user_id = get_demo_user_id()
    return get_or_create_user_settings(user_id)


@router.patch("", response_model=Dict[str, Any])
async def patch_settings(payload: SettingsUpdateRequest) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    updates = payload.dict(exclude_unset=True)

    if not updates:
        return get_or_create_user_settings(user_id)

    try:
        return update_user_settings(user_id, updates)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {err}")
