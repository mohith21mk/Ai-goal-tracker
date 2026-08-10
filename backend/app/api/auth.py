import random
import string
from typing import Any, Dict, Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, validator

from ..database import get_connection
from ..services.auth import (
    create_session,
    delete_session,
    get_user_from_session,
    hash_password,
    is_email_registered,
    is_username_available,
    normalize_username,
    validate_username,
    verify_password,
)

router = APIRouter()

COOKIE_NAME = "mkc_session"


class RegisterRequest(BaseModel):
    full_name: str
    username: str
    email: str
    password: str

    @validator("email")
    def validate_email_str(cls, v: str) -> str:
        v_str = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v_str):
            raise ValueError("Invalid email format")
        return v_str

    @validator("full_name")
    def validate_name(cls, v: str) -> str:
        v_str = v.strip()
        if not v_str:
            raise ValueError("Full name is required")
        if len(v_str) > 100:
            raise ValueError("Full name cannot exceed 100 characters")
        return v_str

    @validator("username")
    def validate_user(cls, v: str) -> str:
        valid, msg_or_norm = validate_username(v)
        if not valid:
            raise ValueError(msg_or_norm)
        return msg_or_norm

    @validator("password")
    def validate_pass(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password cannot exceed 128 characters")
        return v


class LoginRequest(BaseModel):
    identifier: str
    password: str


def get_current_user(request: Request) -> Dict[str, Any]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")

    user = get_user_from_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please log in again.")

    return user


def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return get_user_from_session(token)


@router.get("/check-username", response_model=Dict[str, Any])
async def check_username_availability(username: str = Query(..., min_length=1)) -> Dict[str, Any]:
    valid, norm_or_msg = validate_username(username)
    if not valid:
        return {"available": False, "username": normalize_username(username), "reason": norm_or_msg}

    available = is_username_available(norm_or_msg)
    return {"available": available, "username": norm_or_msg}


@router.post("/register", response_model=Dict[str, Any])
async def register_user(payload: RegisterRequest, response: Response) -> Dict[str, Any]:
    norm_username = normalize_username(payload.username)
    norm_email = payload.email.strip().lower()

    if not is_username_available(norm_username):
        raise HTTPException(
            status_code=409,
            detail=f"@{norm_username} is already taken. Please choose another username.",
        )

    if is_email_registered(norm_email):
        raise HTTPException(
            status_code=409,
            detail="Email address is already registered. Please log in instead.",
        )

    # Derive avatar initials
    parts = payload.full_name.strip().split()
    if len(parts) >= 2:
        initials = (parts[0][0] + parts[-1][0]).upper()
    elif len(parts) == 1:
        initials = parts[0][:2].upper()
    else:
        initials = "MK"

    # Generate permanent MKC ID
    year = "2026"
    rnd_hex = "".join(random.choices(string.hexdigits.upper()[:16], k=6))
    mkc_id = f"MKC-{year}-{rnd_hex}"

    hashed_pwd = hash_password(payload.password)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (email, username, password_hash, full_name, mkc_id, avatar_initials, bio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                norm_email,
                norm_username,
                hashed_pwd,
                payload.full_name,
                mkc_id,
                initials,
                "AI Engineering & Full-Stack Systems Mastery",
            ),
        )
        conn.commit()
        user_id = cursor.lastrowid

        # Seed default user settings for new user
        cursor.execute(
            """
            INSERT INTO user_settings (user_id, theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility)
            VALUES (?, 'dark', 1, 'strategic', '08:00', 'public')
            """,
            (user_id,),
        )
        conn.commit()

        # Seed initial sample goals, habits, missions for new user
        cursor.execute(
            """
            INSERT INTO goals (user_id, title, description, category, status, target_date)
            VALUES (?, 'AI Systems Mastery', 'Build autonomous agentic platforms and modern AI applications.', 'learning', 'active', '2026-12-31')
            """,
            (user_id,),
        )
        conn.commit()
        goal_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO missions (user_id, goal_id, title, description, category, time, difficulty, xp_reward, completed)
            VALUES (?, ?, 'Morning Protocol & System Architecture Block', 'Execute deep work block and protocol tasks.', 'productivity', '30 min', 'easy', 15, 0)
            """,
            (user_id, goal_id),
        )
        conn.commit()

    except Exception as err:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="Registration conflict: Username or email is already taken.",
        ) from err
    finally:
        conn.close()

    # Create session cookie
    token = create_session(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Local dev
        max_age=30 * 24 * 3600,
        path="/",
    )

    return {
        "id": user_id,
        "username": norm_username,
        "full_name": payload.full_name,
        "email": norm_email,
        "mkc_id": mkc_id,
        "avatar_initials": initials,
        "bio": "AI Engineering & Full-Stack Systems Mastery",
        "is_active": True,
    }


@router.post("/login", response_model=Dict[str, Any])
async def login_user(payload: LoginRequest, response: Response) -> Dict[str, Any]:
    raw_id = payload.identifier.strip()
    norm_id = normalize_username(raw_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM users
        WHERE LOWER(email) = LOWER(?) OR LOWER(username) = LOWER(?)
        """,
        (raw_id, norm_id),
    )
    user_row = cursor.fetchone()
    conn.close()

    generic_error = HTTPException(
        status_code=401,
        detail="Invalid username/email or password.",
    )

    if not user_row:
        raise generic_error

    user_dict = dict(user_row)

    if not user_dict.get("password_hash"):
        raise generic_error

    if not verify_password(payload.password, user_dict["password_hash"]):
        raise generic_error

    if user_dict.get("is_active") == 0:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    # Create session token
    user_id = user_dict["id"]
    token = create_session(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=30 * 24 * 3600,
        path="/",
    )

    user_dict.pop("password_hash", None)
    user_dict["is_active"] = True
    return user_dict


@router.post("/logout", response_model=Dict[str, Any])
async def logout_user(request: Request, response: Response) -> Dict[str, Any]:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        delete_session(token)
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=Dict[str, Any])
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return current_user
