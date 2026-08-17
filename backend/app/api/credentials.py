from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_user
from ..database import get_connection
from ..services.progression import (
    evaluate_and_issue_credentials,
    list_user_credentials,
)

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
async def get_my_credentials(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get all credentials earned by the current authenticated user.
    """
    user_id = current_user["id"]
    return list_user_credentials(user_id)


@router.get("/user/{user_id}", response_model=List[Dict[str, Any]])
async def get_user_public_credentials(
    user_id: int
) -> List[Dict[str, Any]]:
    """
    Get public credentials earned by a specific user.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return list_user_credentials(user_id)


@router.get("/verify/{credential_id}", response_model=Dict[str, Any])
async def verify_credential_public(credential_id: int) -> Dict[str, Any]:
    """
    Publicly verify a credential without requiring authentication.
    Returns the verified recipient details, credential attributes, and authoritative hash.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.user_id, c.credential_type, c.slug, c.title, c.description,
               c.tier, c.xp_value, c.evidence_type, c.evidence_id, c.issued_at,
               u.username, u.full_name, u.avatar_initials, u.mkc_id
        FROM user_credentials c
        JOIN users u ON c.user_id = u.id
        WHERE c.id = ?
    """, (credential_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Credential not found or unverified")

    cred = dict(row)
    cred["is_verified"] = True
    cred["verification_hash"] = f"MKC-AUTH-{(cred.get('slug') or 'CRED').upper()}-{cred['id']}"
    cred["authority"] = "MASTER CREDENTIAL AUTHORITY"
    return cred


@router.post("/check", response_model=Dict[str, Any])
async def check_and_issue_credentials(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Evaluate server-authoritative evidence and issue any newly earned credentials.
    Anti-spoofing: Does not accept client claims; calculates strictly from DB records.
    """
    user_id = current_user["id"]
    result = evaluate_and_issue_credentials(user_id)
    return result
