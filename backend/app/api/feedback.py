from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ..services.feedback import (
    create_feedback,
    get_feedback_by_id,
    list_feedback,
    update_feedback,
    delete_feedback,
    get_feedback_stats,
    VALID_CATEGORIES,
    VALID_SEVERITIES,
    VALID_STATUSES
)
from ..services.rate_limiter import rate_limit
from .auth import get_current_user

router = APIRouter()


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency ensuring only accounts with role == 'admin' can access admin endpoints."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrator privileges required."
        )
    return current_user


class FeedbackCreateRequest(BaseModel):
    category: str = Field(..., description="Feedback category e.g. Bug, Feature Request, UI/UX, etc.")
    message: str = Field(..., min_length=3, max_length=5000, description="Detailed feedback text")
    severity: Optional[str] = Field("Normal", description="Severity level: Low, Normal, High, Critical")
    page_url: Optional[str] = Field(None, max_length=1000, description="Optional current page URL")


class FeedbackUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="Status: new, reviewing, resolved, closed")
    severity: Optional[str] = Field(None, description="Severity: Low, Normal, High, Critical")
    admin_notes: Optional[str] = Field(None, max_length=5000, description="Private administrator notes")


# =========================================================================
# USER ENDPOINTS (Strict Isolation: Users can only submit feedback)
# =========================================================================

@router.post(
    "/api/feedback",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60, key_prefix="feedback"))],
    summary="Submit user feedback"
)
async def submit_user_feedback(
    payload: FeedbackCreateRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Authenticated users submit feedback. User ID is derived strictly from authentication.
    """
    if payload.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category '{payload.category}'. Allowed categories: {sorted(VALID_CATEGORIES)}"
        )

    if payload.severity and payload.severity not in VALID_SEVERITIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid severity '{payload.severity}'. Allowed severities: {sorted(VALID_SEVERITIES)}"
        )

    user_agent = request.headers.get("user-agent", "")[:500]

    try:
        res = await create_feedback(
            user_id=current_user["id"],
            category=payload.category,
            message=payload.message,
            severity=payload.severity or "Normal",
            page_url=payload.page_url,
            user_agent=user_agent
        )
        return {
            "success": True,
            "message": "Thank you. Your feedback has been received.",
            "id": res["id"]
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# =========================================================================
# ADMIN-ONLY ENDPOINTS (Requires role == 'admin')
# =========================================================================

@router.get("/api/admin/feedback/stats", summary="Get feedback statistics (Admin only)")
async def admin_get_feedback_stats(
    admin_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Admin dashboard stats for feedback tickets."""
    return get_feedback_stats()


@router.get("/api/admin/feedback", summary="List all user feedback (Admin only)")
async def admin_list_feedback(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Admin endpoint to list and filter all user feedback submissions."""
    items, total = list_feedback(
        limit=limit,
        offset=offset,
        category=category,
        status=status,
        severity=severity
    )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/api/admin/feedback/{feedback_id}", summary="Get feedback details (Admin only)")
async def admin_get_feedback_detail(
    feedback_id: int,
    admin_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Retrieve full feedback detail including private admin notes and user metadata."""
    item = get_feedback_by_id(feedback_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found.")
    return item


@router.patch("/api/admin/feedback/{feedback_id}", summary="Update feedback status/notes (Admin only)")
async def admin_update_feedback(
    feedback_id: int,
    payload: FeedbackUpdateRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Update feedback status, severity, or private admin notes."""
    try:
        updated = update_feedback(
            feedback_id=feedback_id,
            status=payload.status,
            severity=payload.severity,
            admin_notes=payload.admin_notes
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found.")
        return updated
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.delete("/api/admin/feedback/{feedback_id}", summary="Delete feedback (Admin only)")
async def admin_delete_feedback(
    feedback_id: int,
    admin_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Delete a feedback ticket."""
    deleted = delete_feedback(feedback_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found.")
    return {"success": True, "message": "Feedback deleted successfully."}
