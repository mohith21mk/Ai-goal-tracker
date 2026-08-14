import datetime
import json
from typing import Any, Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, field_validator

from ..config import settings
from ..database import get_connection
from ..services.email import send_verification_email
from ..services.auth import (
    create_email_verification_token,
    delete_user_account,
    is_email_registered,
    is_username_available,
    normalize_username,
    revoke_all_sessions,
    validate_username,
    verify_password,
)
from ..services.settings import get_or_create_user_settings
from .auth import COOKIE_NAME, get_current_user

router = APIRouter()


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    avatar_initials: Optional[str] = None
    bio: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_uname(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid, msg_or_norm = validate_username(v)
            if not valid:
                raise ValueError(msg_or_norm)
            return msg_or_norm
        return v

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_str = v.strip().lower()
            import re
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v_str):
                raise ValueError("Invalid email format")
            return v_str
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_str = v.strip()
            if not v_str:
                raise ValueError("Full name cannot be empty")
            if len(v_str) > 100:
                raise ValueError("Full name cannot exceed 100 characters")
            return v_str
        return v

    @field_validator("avatar_initials")
    @classmethod
    def validate_avatar_initials(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_str = v.strip().upper()
            if len(v_str) > 4:
                raise ValueError("Avatar initials cannot exceed 4 characters")
            return v_str
        return v

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) > 500:
                raise ValueError("Bio cannot exceed 500 characters")
            return v.strip()
        return v


class OnboardingRequest(BaseModel):
    primary_goal: Optional[str] = None
    commitment_level: Optional[str] = None
    improvement_area: Optional[str] = None
    first_mission_title: Optional[str] = None


class AccountDeleteRequest(BaseModel):
    current_password: str
    confirmation_text: str


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
    user_dict["email_verified"] = bool(user_dict.get("email_verified", 0))
    user_dict["onboarding_completed"] = bool(user_dict.get("onboarding_completed", 0))
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


@router.get("/search", response_model=Dict[str, Any])
async def search_public_users(
    q: str = Query(..., min_length=2),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    search_term = f"%{q.strip().lower()}%"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, mkc_id, username, full_name, avatar_initials, bio
        FROM users
        WHERE (LOWER(COALESCE(username, '')) LIKE ? 
            OR LOWER(COALESCE(full_name, '')) LIKE ? 
            OR LOWER(COALESCE(mkc_id, '')) LIKE ?) 
          AND id != ?
        ORDER BY id ASC LIMIT 20
        """,
        (search_term, search_term, search_term, current_user["id"])
    )
    rows = cursor.fetchall()

    users_list = []
    if rows:
        user_ids = [r["id"] for r in rows]
        placeholders = ",".join("?" * len(user_ids))
        cursor.execute(
            f"""
            SELECT requester_id, recipient_id, status
            FROM user_connections
            WHERE (requester_id = ? AND recipient_id IN ({placeholders}))
               OR (recipient_id = ? AND requester_id IN ({placeholders}))
            """,
            [current_user["id"]] + user_ids + [current_user["id"]] + user_ids
        )
        conn_rows = cursor.fetchall()
        status_map = {}
        for c in conn_rows:
            other_id = c["recipient_id"] if c["requester_id"] == current_user["id"] else c["requester_id"]
            if c["requester_id"] == current_user["id"]:
                status_map[other_id] = "sent" if c["status"] == "pending" else c["status"]
            else:
                status_map[other_id] = "received" if c["status"] == "pending" else c["status"]

        for r in rows:
            u_id = r["id"]
            users_list.append({
                "id": u_id,
                "mkc_id": r["mkc_id"] or f"MKC-{u_id:04d}",
                "display_name": r["full_name"] or r["username"],
                "full_name": r["full_name"] or r["username"],
                "username": r["username"],
                "avatar_initials": r["avatar_initials"] or r["username"][:2].upper(),
                "bio": r["bio"] or "",
                "connection_status": status_map.get(u_id, "none"),
            })
    conn.close()

    return {"users": users_list}


@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_public_user_profile_endpoint(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Fetch public profile for a specific user ID with bidirectional connection status.
    """
    profile = _get_user_profile_dict(user_id)

    if user_id == current_user["id"]:
        profile["connection_status"] = "self"
        return profile

    # Hide private email from other users
    profile.pop("email", None)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT requester_id, recipient_id, status
        FROM user_connections
        WHERE (requester_id = ? AND recipient_id = ?)
           OR (requester_id = ? AND recipient_id = ?)
        """,
        (current_user["id"], user_id, user_id, current_user["id"])
    )
    conn_row = cursor.fetchone()
    conn.close()

    if not conn_row:
        connection_status = "none"
    elif conn_row["status"] == "accepted":
        connection_status = "accepted"
    elif conn_row["status"] == "blocked":
        connection_status = "blocked"
    elif conn_row["status"] == "pending":
        if conn_row["requester_id"] == current_user["id"]:
            connection_status = "sent"
        else:
            connection_status = "received"
    else:
        connection_status = conn_row["status"]

    profile["connection_status"] = connection_status
    return profile


@router.patch("", response_model=Dict[str, Any])
async def update_current_user(
    payload: UserUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    updates = payload.dict(exclude_unset=True)

    if not updates:
        return _get_user_profile_dict(user_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, email FROM users WHERE id = ?", (user_id,))
    current_row = cursor.fetchone()

    # Validate Username change
    if "username" in updates and updates["username"]:
        new_username = normalize_username(updates["username"])
        if current_row and current_row["username"] and current_row["username"].lower() != new_username:
            if not is_username_available(new_username):
                conn.close()
                raise HTTPException(status_code=409, detail=f"@{new_username} is already taken.")
            updates["username"] = new_username

    # Validate Email change
    new_verif_token = None
    if "email" in updates and updates["email"]:
        new_email = updates["email"].strip().lower()
        if current_row and current_row["email"].lower() != new_email:
            if is_email_registered(new_email):
                conn.close()
                raise HTTPException(status_code=409, detail="Email address is already in use.")
            updates["email"] = new_email
            updates["email_verified"] = 0
            new_verif_token = create_email_verification_token(user_id, new_email)
            send_verification_email(new_email, current_user.get("full_name", "Member"), new_verif_token)

    valid_fields = ["full_name", "username", "email", "email_verified", "avatar_initials", "bio"]
    filtered = {k: v for k, v in updates.items() if k in valid_fields and v is not None}

    if not filtered:
        conn.close()
        return _get_user_profile_dict(user_id)

    set_clauses = [f"{k} = ?" for k in filtered.keys()]
    params = list(filtered.values())
    params.append(user_id)

    sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
    cursor.execute(sql, params)
    conn.commit()
    conn.close()

    result = _get_user_profile_dict(user_id)
    if new_verif_token and settings.DEBUG and settings.ENVIRONMENT != "production":
        result["dev_verification_token"] = new_verif_token
    return result


@router.post("/onboarding", response_model=Dict[str, Any])
async def complete_onboarding(
    payload: OnboardingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    onboarding_data_str = json.dumps(payload.dict())

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET onboarding_completed = 1, onboarding_data = ? WHERE id = ?",
        (onboarding_data_str, user_id),
    )
    conn.commit()

    # Optionally seed user's first mission if provided
    if payload.first_mission_title and payload.first_mission_title.strip():
        cursor.execute(
            """
            INSERT INTO missions (user_id, title, description, category, time, difficulty, xp_reward, completed)
            VALUES (?, ?, 'User-created onboarding protocol task', 'productivity', '15 min', 'easy', 15, 0)
            """,
            (user_id, payload.first_mission_title.strip()),
        )
        conn.commit()

    conn.close()
    return {"message": "Onboarding completed successfully!", "onboarding_completed": True}


@router.delete("/account", response_model=Dict[str, Any])
async def delete_account_endpoint(
    payload: AccountDeleteRequest,
    response: Response,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]

    # Verify confirmation string
    if payload.confirmation_text.strip() != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=400,
            detail="Confirmation phrase mismatch. Please type exactly 'DELETE MY ACCOUNT' to confirm deletion.",
        )

    # Verify password
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["password_hash"] or not verify_password(payload.current_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect password. Account deletion denied.")

    # Perform safe cascade deletion
    delete_user_account(user_id)

    # Clear auth cookie
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"message": "Your account and all associated data have been permanently deleted."}

