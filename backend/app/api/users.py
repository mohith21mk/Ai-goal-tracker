import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator

from ..database import get_connection
from ..services.settings import get_or_create_user_settings
from .auth import get_current_user

router = APIRouter()


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    avatar_initials: Optional[str] = None
    bio: Optional[str] = None

    @validator("full_name")
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_str = v.strip()
            if not v_str:
                raise ValueError("Full name cannot be empty")
            if len(v_str) > 100:
                raise ValueError("Full name cannot exceed 100 characters")
            return v_str
        return v

    @validator("avatar_initials")
    def validate_avatar_initials(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_str = v.strip().upper()
            if len(v_str) > 4:
                raise ValueError("Avatar initials cannot exceed 4 characters")
            return v_str
        return v

    @validator("bio")
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) > 500:
                raise ValueError("Bio cannot exceed 500 characters")
            return v.strip()
        return v


def _get_user_profile_dict(user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    user_dict = dict(row)

    # Format member_since
    created_at_str = str(user_dict.get("created_at") or "")
    member_since = "August 2026"
    if created_at_str:
        try:
            dt = datetime.datetime.strptime(created_at_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
            member_since = dt.strftime("%B %Y")
        except Exception:
            pass

    # Real user-isolated telemetry metrics
    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ? AND completed = 1", (user_id,))
    completed_missions = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(xp_reward) FROM missions WHERE user_id = ? AND completed = 1", (user_id,))
    xp_row = cursor.fetchone()[0]
    xp_earned = int(xp_row) if xp_row is not None else 0

    cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'active'", (user_id,))
    active_goals = cursor.fetchone()[0] or 0

    # User-isolated streak calculation
    cursor.execute(
        """
        SELECT DISTINCT DATE(completed_at) as comp_date
        FROM missions
        WHERE user_id = ? AND completed = 1 AND completed_at IS NOT NULL
        ORDER BY comp_date DESC
        """,
        (user_id,),
    )
    date_rows = cursor.fetchall()
    dates = [r["comp_date"] for r in date_rows if r["comp_date"]]

    streak_days = 0
    if dates:
        today = datetime.date.today()
        latest_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d").date()
        if (today - latest_date).days <= 1:
            streak_days = 1
            current = latest_date
            for d_str in dates[1:]:
                d = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                if (current - d).days == 1:
                    streak_days += 1
                    current = d
                else:
                    break

    # Settings profile_visibility
    settings = get_or_create_user_settings(user_id)
    profile_visibility = settings.get("profile_visibility", "public")

    conn.close()

    user_dict.pop("password_hash", None)
    user_dict["is_active"] = True
    user_dict["member_since"] = member_since
    user_dict["streak_days"] = streak_days
    user_dict["xp_earned"] = xp_earned
    user_dict["completed_missions"] = completed_missions
    user_dict["active_goals"] = active_goals
    user_dict["profile_visibility"] = profile_visibility
    user_dict["bio"] = user_dict.get("bio") or "AI Engineering & Full-Stack Systems Mastery"
    user_dict["avatar_initials"] = user_dict.get("avatar_initials") or "MK"

    return user_dict


@router.get("", response_model=Dict[str, Any])
async def get_user_profile_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return _get_user_profile_dict(current_user["id"])


@router.patch("", response_model=Dict[str, Any])
async def update_current_user(
    payload: UserUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    updates = payload.dict(exclude_unset=True)

    if not updates:
        return _get_user_profile_dict(user_id)

    valid_fields = ["full_name", "avatar_initials", "bio"]
    filtered = {k: v for k, v in updates.items() if k in valid_fields and v is not None}

    if not filtered:
        return _get_user_profile_dict(user_id)

    set_clauses = [f"{k} = ?" for k in filtered.keys()]
    params = list(filtered.values())
    params.append(user_id)

    sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()

    return _get_user_profile_dict(user_id)
