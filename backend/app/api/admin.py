import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..database import get_connection
from ..services.feedback import get_feedback_stats
from ..services.progression import calculate_user_xp, calculate_level, calculate_rank, get_user_max_habit_streak
from .auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency ensuring only accounts with role == 'admin' can access admin endpoints."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrator privileges required."
        )
    return current_user


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., description="Role: 'admin' or 'user'")


class UserStatusUpdateRequest(BaseModel):
    is_active: bool = Field(..., description="Active status")


@router.get("/overview", summary="Admin analytics overview")
async def get_admin_overview(
    admin_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Real server-authoritative system metrics across all users.
    """
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = now.strftime("%Y-%m-%d 00:00:00")
    seven_days_ago = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    thirty_days_ago = (now - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

    # 1. Total Registered Users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0] or 0

    # 2. Active Users (last 7d / 30d by session activity or last_seen_at)
    cursor.execute(
        """
        SELECT COUNT(DISTINCT user_id) 
        FROM app_sessions 
        WHERE last_seen_at >= ? OR expires_at >= ?
        """,
        (seven_days_ago, now.strftime("%Y-%m-%d %H:%M:%S")),
    )
    active_users_7d = cursor.fetchone()[0] or 0

    cursor.execute(
        """
        SELECT COUNT(DISTINCT user_id) 
        FROM app_sessions 
        WHERE last_seen_at >= ? OR expires_at >= ?
        """,
        (thirty_days_ago, now.strftime("%Y-%m-%d %H:%M:%S")),
    )
    active_users_30d = cursor.fetchone()[0] or 0

    # Fallback to at least total active accounts if sessions empty
    if active_users_7d == 0 and total_users > 0:
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users_7d = min(cursor.fetchone()[0] or 0, total_users)
        active_users_30d = active_users_7d

    # 3. New Users
    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", (today_start,))
    new_users_today = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", (seven_days_ago,))
    new_users_7d = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", (thirty_days_ago,))
    new_users_30d = cursor.fetchone()[0] or 0

    # 4. User Registration Timeline (past 14 days daily counts)
    timeline = []
    for i in range(13, -1, -1):
        day_dt = now.date() - datetime.timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        d_start = f"{day_str} 00:00:00"
        d_end = f"{day_str} 23:59:59"
        cursor.execute("SELECT COUNT(*) FROM users WHERE created_at BETWEEN ? AND ?", (d_start, d_end))
        cnt = cursor.fetchone()[0] or 0
        timeline.append({"date": day_str, "count": cnt})

    # 5. Global Engagement Stats
    cursor.execute("SELECT COUNT(*) FROM missions WHERE completed = 1")
    total_missions_completed = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM habits WHERE status = 'active'")
    total_active_habits = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM habit_logs")
    total_habit_logs = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM life_blueprints")
    total_blueprints = cursor.fetchone()[0] or 0

    # Total XP Awarded System-wide
    cursor.execute("SELECT COALESCE(SUM(xp_reward), 0) FROM missions WHERE completed = 1")
    mission_xp_sum = cursor.fetchone()[0] or 0
    total_xp_awarded = int(mission_xp_sum) + (int(total_habit_logs) * 15)

    conn.close()

    # 6. Feedback Summary
    feedback_stats = get_feedback_stats()

    return {
        "total_users": total_users,
        "active_users_7d": active_users_7d,
        "active_users_30d": active_users_30d,
        "new_users_today": new_users_today,
        "new_users_7d": new_users_7d,
        "new_users_30d": new_users_30d,
        "user_growth_timeline": timeline,
        "engagement": {
            "missions_completed": total_missions_completed,
            "active_habits": total_active_habits,
            "habit_logs": total_habit_logs,
            "blueprints_created": total_blueprints,
            "total_xp_awarded": total_xp_awarded,
        },
        "feedback": feedback_stats,
    }


@router.get("/users", summary="Admin users directory with progression details")
async def get_admin_users(
    q: Optional[str] = Query(None, description="Search query"),
    role: Optional[str] = Query(None, description="Filter by role ('admin', 'user')"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Search and paginate user directory with live XP, Level, Rank, and Streak statistics.
    """
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if q and q.strip():
        search_term = f"%{q.strip().lower()}%"
        conditions.append("(LOWER(username) LIKE ? OR LOWER(full_name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(COALESCE(mkc_id, '')) LIKE ?)")
        params.extend([search_term, search_term, search_term, search_term])

    if role and role.strip():
        conditions.append("role = ?")
        params.append(role.strip().lower())

    if is_active is not None:
        conditions.append("is_active = ?")
        params.append(1 if is_active else 0)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Total count query
    count_sql = f"SELECT COUNT(*) FROM users {where_clause}"
    cursor.execute(count_sql, tuple(params))
    total = cursor.fetchone()[0] or 0

    # User rows query
    users_sql = f"""
        SELECT id, username, email, full_name, mkc_id, avatar_initials, bio, role, 
               is_active, email_verified, onboarding_completed, created_at
        FROM users
        {where_clause}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(users_sql, tuple(params + [limit, offset]))
    rows = cursor.fetchall()

    users_list = []
    for r in rows:
        u_dict = dict(r)
        uid = u_dict["id"]

        # Compute live progression for each user
        xp_data = calculate_user_xp(uid)
        tot_xp = xp_data["total_xp"]
        lvl = calculate_level(tot_xp)
        rnk = calculate_rank(lvl)
        streak = get_user_max_habit_streak(uid)

        # Count completed missions, active goals, habits, and credentials
        cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ? AND completed = 1", (uid,))
        comp_m = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'active'", (uid,))
        act_g = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM habits WHERE user_id = ? AND status = 'active'", (uid,))
        act_h = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM user_credentials WHERE user_id = ?", (uid,))
        cred_c = cursor.fetchone()[0] or 0

        # Latest session last_seen_at
        cursor.execute("SELECT MAX(last_seen_at) FROM app_sessions WHERE user_id = ?", (uid,))
        last_seen = cursor.fetchone()[0]

        u_dict.update({
            "user_id": uid,
            "total_xp": tot_xp,
            "xp": tot_xp,
            "mission_xp": xp_data["mission_xp"],
            "habit_xp": xp_data["habit_xp"],
            "level": lvl,
            "rank": rnk,
            "streak_days": streak,
            "discipline_streak": streak,
            "completed_missions": comp_m,
            "active_goals": act_g,
            "active_habits": act_h,
            "earned_credentials_count": cred_c,
            "credentials_count": cred_c,
            "last_seen_at": last_seen,
            "last_activity": last_seen or (str(u_dict.get("created_at")) if u_dict.get("created_at") else None),
        })
        users_list.append(u_dict)

    conn.close()

    return {
        "items": users_list,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch("/users/{user_id}/role", summary="Update user role (Admin only)")
async def update_user_role(
    user_id: int,
    payload: UserRoleUpdateRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    new_role = payload.role.strip().lower()
    if new_role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'user'.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")

    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"User {user_id} role updated to '{new_role}'.",
        "user_id": user_id,
        "role": new_role,
    }


@router.patch("/users/{user_id}/status", summary="Toggle user active status (Admin only)")
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdateRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")

    new_status = 1 if payload.is_active else 0
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    if not payload.is_active:
        # Revoke active sessions
        cursor.execute("DELETE FROM app_sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"User {user_id} active status updated to {payload.is_active}.",
        "user_id": user_id,
        "is_active": payload.is_active,
    }
