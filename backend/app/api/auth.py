import random
import re
import string
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, field_validator

from ..config import settings
from ..database import get_connection
from ..services.websocket import manager
from ..services.email import send_password_reset_email, send_verification_email
from ..services.auth import (
    create_email_verification_token,
    create_password_reset_token,
    create_session,
    delete_session,
    get_user_from_session,
    hash_password,
    is_email_registered,
    is_username_available,
    list_user_sessions,
    normalize_username,
    revoke_all_sessions,
    revoke_session_by_id,
    validate_username,
    verify_and_use_reset_token,
    verify_email_token,
    verify_password,
)

router = APIRouter()

COOKIE_NAME = "mkc_session"


class RegisterRequest(BaseModel):
    full_name: str
    username: str
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_str(cls, v: str) -> str:
        v_str = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v_str):
            raise ValueError("Invalid email format")
        return v_str

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v_str = v.strip()
        if not v_str:
            raise ValueError("Full name is required")
        if len(v_str) > 100:
            raise ValueError("Full name cannot exceed 100 characters")
        return v_str

    @field_validator("username")
    @classmethod
    def validate_user(cls, v: str) -> str:
        valid, msg_or_norm = validate_username(v)
        if not valid:
            raise ValueError(msg_or_norm)
        return msg_or_norm

    @field_validator("password")
    @classmethod
    def validate_pass(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password cannot exceed 128 characters")
        return v


class LoginRequest(BaseModel):
    identifier: str
    password: str


class ForgotPasswordRequest(BaseModel):
    identifier: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_pass(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password cannot exceed 128 characters")
        return v


class VerifyEmailRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_pass(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must contain at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password cannot exceed 128 characters")
        return v


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
async def register_user(payload: RegisterRequest, request: Request, response: Response) -> Dict[str, Any]:
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
            INSERT INTO users (email, username, password_hash, full_name, mkc_id, avatar_initials, bio, email_verified, onboarding_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
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

        # Generate single-use verification token
        verif_token = create_email_verification_token(user_id, norm_email)
        send_verification_email(norm_email, payload.full_name, verif_token)

    except Exception as err:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="Registration conflict: Username or email is already taken.",
        ) from err
    finally:
        conn.close()

    # Capture device info
    ua = request.headers.get("user-agent")
    client_ip = request.client.host if request.client else None

    # Create session cookie
    token = create_session(user_id, user_agent=ua, ip_address=client_ip)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        max_age=30 * 24 * 3600,
        path="/",
    )

    res_data = {
        "id": user_id,
        "username": norm_username,
        "full_name": payload.full_name,
        "email": norm_email,
        "mkc_id": mkc_id,
        "avatar_initials": initials,
        "bio": "AI Engineering & Full-Stack Systems Mastery",
        "email_verified": False,
        "onboarding_completed": False,
        "is_active": True,
    }

    # Only include dev token in local development responses
    if settings.DEBUG and settings.ENVIRONMENT != "production":
        res_data["dev_verification_token"] = verif_token

    return res_data


@router.post("/login", response_model=Dict[str, Any])
async def login_user(payload: LoginRequest, request: Request, response: Response) -> Dict[str, Any]:
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
        raise HTTPException(status_code=403, detail="Account is deactivated. Please contact support or reactivate.")

    # Capture device info
    ua = request.headers.get("user-agent")
    client_ip = request.client.host if request.client else None

    # Create session token
    user_id = user_dict["id"]
    token = create_session(user_id, user_agent=ua, ip_address=client_ip)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        max_age=30 * 24 * 3600,
        path="/",
    )

    user_dict.pop("password_hash", None)
    user_dict["is_active"] = True
    user_dict["email_verified"] = bool(user_dict.get("email_verified", 0))
    user_dict["onboarding_completed"] = bool(user_dict.get("onboarding_completed", 0))
    return user_dict


@router.post("/logout", response_model=Dict[str, Any])
async def logout_user(request: Request, response: Response) -> Dict[str, Any]:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        user = get_user_from_session(token)
        if user:
            await manager.disconnect_user(user["id"])
        delete_session(token)
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=Dict[str, Any])
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return current_user


@router.post("/forgot-password", response_model=Dict[str, Any])
async def forgot_password(payload: ForgotPasswordRequest) -> Dict[str, Any]:
    raw_id = payload.identifier.strip()
    norm_id = normalize_username(raw_id)

    generic_msg = "If an account exists for this address, you'll receive password reset instructions."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, email, full_name FROM users
        WHERE LOWER(email) = LOWER(?) OR LOWER(username) = LOWER(?)
        """,
        (raw_id, norm_id),
    )
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        return {"message": generic_msg}

    reset_token = create_password_reset_token(user_row["id"])
    send_password_reset_email(user_row["email"], user_row["full_name"], reset_token)

    res_data = {"message": generic_msg}
    if settings.DEBUG and settings.ENVIRONMENT != "production":
        res_data["dev_reset_token"] = reset_token

    return res_data


@router.post("/reset-password", response_model=Dict[str, Any])
async def reset_password(payload: ResetPasswordRequest) -> Dict[str, Any]:
    success = verify_and_use_reset_token(payload.token.strip(), payload.new_password)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Password reset token is invalid or has expired. Please request a new link.",
        )
    return {"message": "Password updated successfully."}


@router.post("/verify-email", response_model=Dict[str, Any])
async def verify_email(payload: VerifyEmailRequest) -> Dict[str, Any]:
    success = verify_email_token(payload.token.strip())
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Email verification link is invalid or has expired.",
        )
    return {"message": "Email address verified successfully!"}


@router.post("/resend-verification", response_model=Dict[str, Any])
async def resend_verification(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("email_verified"):
        return {"message": "Your email address is already verified."}

    verif_token = create_email_verification_token(current_user["id"], current_user["email"])
    send_verification_email(current_user["email"], current_user.get("full_name", "Member"), verif_token)

    res_data = {"message": "Verification email sent. Please check your inbox."}
    if settings.DEBUG and settings.ENVIRONMENT != "production":
        res_data["dev_verification_token"] = verif_token

    return res_data


@router.post("/change-password", response_model=Dict[str, Any])
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (current_user["id"],))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["password_hash"] or not verify_password(payload.current_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect current password.")

    # Update password_hash
    new_hash = hash_password(payload.new_password)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, current_user["id"]))
    conn.commit()
    conn.close()

    # Revoke all OTHER active sessions
    current_token = request.cookies.get(COOKIE_NAME)
    revoke_all_sessions(current_user["id"], except_token=current_token)
    
    # Send disconnect signal to frontend so websockets close
    await manager.disconnect_user(current_user["id"])

    return {"message": "Password changed successfully. All other devices have been logged out."}


@router.get("/sessions", response_model=Dict[str, Any])
async def get_sessions(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    current_token = request.cookies.get(COOKIE_NAME)
    sessions = list_user_sessions(current_user["id"], current_token=current_token)
    return {"sessions": sessions}


@router.delete("/sessions/{session_id}", response_model=Dict[str, Any])
async def delete_session_by_id(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    success = revoke_session_by_id(current_user["id"], session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or already revoked.")
    
    # Ensure any open websocket associated with this user receives the revocation
    # We disconnect all their WS connections since they need to re-authenticate if they are the ones we killed. 
    # (In a more complex system, we'd only disconnect the specific session, but disconnecting all is safest for security).
    await manager.disconnect_user(current_user["id"])
    
    return {"message": "Session revoked successfully."}


@router.post("/sessions/revoke-others", response_model=Dict[str, Any])
async def revoke_others(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    current_token = request.cookies.get(COOKIE_NAME)
    revoked_count = revoke_all_sessions(current_user["id"], except_token=current_token)
    
    await manager.disconnect_user(current_user["id"])
    
    return {"message": f"Successfully logged out {revoked_count} other session(s)."}


@router.post("/deactivate", response_model=Dict[str, Any])
async def deactivate_account(
    request: Request,
    response: Response,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = 0, deactivated_at = ? WHERE id = ?", (now_str, current_user["id"]))
    conn.commit()
    conn.close()

    # Revoke sessions
    revoke_all_sessions(current_user["id"])
    await manager.disconnect_user(current_user["id"])
    
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"message": "Account deactivated successfully."}

