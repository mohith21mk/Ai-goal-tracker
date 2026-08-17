from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..database import get_connection
from .auth import get_current_user
from ..services.notifications import create_notification
from ..services.rate_limiter import rate_limit

router = APIRouter()

class ConnectionAction(BaseModel):
    user_id: Optional[int] = None
    request_id: Optional[int] = None

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_users(
    q: str = Query(default="", min_length=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_connection()
    cursor = conn.cursor()
    search_q = q.strip().lower()

    if search_q:
        search_term = f"%{search_q}%"
        cursor.execute("""
            SELECT id, username, full_name, avatar_initials, bio
            FROM users
            WHERE (LOWER(COALESCE(username, '')) LIKE ? OR LOWER(COALESCE(full_name, '')) LIKE ?)
              AND id != ?
              AND deactivated_at IS NULL
            LIMIT 20
        """, (search_term, search_term, current_user["id"]))
    else:
        cursor.execute("""
            SELECT id, username, full_name, avatar_initials, bio
            FROM users
            WHERE id != ?
              AND deactivated_at IS NULL
            ORDER BY id DESC
            LIMIT 20
        """, (current_user["id"],))
    
    users = [dict(row) for row in cursor.fetchall()]
    
    if users:
        user_ids = [u["id"] for u in users]
        placeholders = ",".join("?" * len(user_ids))
        
        cursor.execute(f"""
            SELECT requester_id, recipient_id, status 
            FROM user_connections 
            WHERE (requester_id = ? AND recipient_id IN ({placeholders}))
               OR (recipient_id = ? AND requester_id IN ({placeholders}))
        """, [current_user["id"]] + user_ids + [current_user["id"]] + user_ids)
        
        conns = cursor.fetchall()
        
        status_map = {}
        for c in conns:
            other_id = c["recipient_id"] if c["requester_id"] == current_user["id"] else c["requester_id"]
            if c["requester_id"] == current_user["id"]:
                status_map[other_id] = "sent" if c["status"] == "pending" else c["status"]
            else:
                status_map[other_id] = "received" if c["status"] == "pending" else c["status"]
                
        for u in users:
            u["connection_status"] = status_map.get(u["id"], "none")
            
    conn.close()
    return users

@router.get("/connections", response_model=Dict[str, Any])
async def get_connections(current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    
    user_id = current_user["id"]
    
    cursor.execute("""
        SELECT c.id AS request_id,
               c.id AS connection_id,
               u.id,
               u.id AS user_id,
               u.username,
               u.full_name,
               u.avatar_initials,
               u.bio,
               u.mkc_id,
               c.status,
               c.created_at,
               CASE WHEN c.requester_id = ? THEN 'sent' ELSE 'received' END AS direction
        FROM user_connections c
        JOIN users u ON (c.requester_id = u.id OR c.recipient_id = u.id)
        WHERE (c.requester_id = ? OR c.recipient_id = ?) AND u.id != ?
        ORDER BY c.created_at DESC
    """, (user_id, user_id, user_id, user_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    connections = {"accepted": [], "pending_received": [], "pending_sent": [], "blocked": []}
    for row in rows:
        d = dict(row)
        if d["status"] == "accepted":
            connections["accepted"].append(d)
        elif d["status"] == "pending" and d["direction"] == "received":
            connections["pending_received"].append(d)
        elif d["status"] == "pending" and d["direction"] == "sent":
            connections["pending_sent"].append(d)
        elif d["status"] == "blocked":
            connections["blocked"].append(d)
            
    return connections

@router.post(
    "/connections/request",
    response_model=Dict[str, Any],
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60, key_prefix="conn_req"))]
)
async def request_connection(payload: ConnectionAction, current_user: Dict[str, Any] = Depends(get_current_user)):
    target_id = payload.user_id
    if not target_id:
        raise HTTPException(status_code=400, detail="User ID is required to send a connection request")
    if target_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot connect to yourself")
        
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, full_name FROM users WHERE id = ?", (target_id,))
    target_user = cursor.fetchone()
    if not target_user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    cursor.execute(
        """
        SELECT id, status, requester_id, recipient_id 
        FROM user_connections 
        WHERE (requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?)
        """,
        (current_user["id"], target_id, target_id, current_user["id"])
    )
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Connection already exists with status: {existing['status']}")
        
    cursor.execute(
        "INSERT INTO user_connections (requester_id, recipient_id, status) VALUES (?, ?, 'pending')",
        (current_user["id"], target_id)
    )
    conn.commit()
    request_id = cursor.lastrowid
    conn.close()
    
    # Notify recipient with structured request reference and payload
    await create_notification(
        user_id=target_id,
        type="connection_request",
        title="New Connection Request",
        message=f"@{current_user['username']} sent you a connection request.",
        reference_type="connection_request",
        reference_id=request_id,
        data={
            "type": "connection_request",
            "request_id": request_id,
            "sender_id": current_user["id"],
            "sender_username": current_user.get("username", ""),
            "sender_name": current_user.get("full_name") or current_user.get("username", ""),
            "recipient_id": target_id,
            "action": "open_connection_requests"
        }
    )
    
    return {
        "status": "success",
        "message": "Connection request sent",
        "request_id": request_id,
        "recipient_id": target_id
    }

@router.post("/connections/accept", response_model=Dict[str, Any])
async def accept_connection(payload: ConnectionAction, current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    
    if payload.request_id:
        cursor.execute(
            "SELECT id, requester_id, recipient_id, status FROM user_connections WHERE id = ? AND recipient_id = ?",
            (payload.request_id, current_user["id"])
        )
    elif payload.user_id:
        cursor.execute(
            "SELECT id, requester_id, recipient_id, status FROM user_connections WHERE requester_id = ? AND recipient_id = ?",
            (payload.user_id, current_user["id"])
        )
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Either user_id or request_id must be provided")
        
    req = cursor.fetchone()
    
    if not req or req["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=400, detail="No pending request found from this user")
        
    requester_id = req["requester_id"]
    req_id = req["id"]
    
    cursor.execute(
        "UPDATE user_connections SET status = 'accepted' WHERE id = ?",
        (req_id,)
    )
                  
    cursor.execute("""
        SELECT c.id FROM conversations c
        JOIN conversation_members m1 ON c.id = m1.conversation_id
        JOIN conversation_members m2 ON c.id = m2.conversation_id
        WHERE m1.user_id = ? AND m2.user_id = ?
    """, (current_user["id"], requester_id))
    
    conv_row = cursor.fetchone()
    if conv_row:
        conv_id = conv_row["id"]
    else:
        cursor.execute("INSERT INTO conversations DEFAULT VALUES")
        conv_id = cursor.lastrowid
        cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, current_user["id"]))
        cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, requester_id))
        
    conn.commit()
    conn.close()
    
    # Notify requester that their request was accepted
    await create_notification(
        user_id=requester_id,
        type="connection_accepted",
        title="Connection Accepted",
        message=f"@{current_user['username']} accepted your connection request.",
        reference_type="conversation",
        reference_id=conv_id,
        data={
            "type": "connection_accepted",
            "request_id": req_id,
            "user_id": current_user["id"],
            "username": current_user.get("username", ""),
            "conversation_id": conv_id,
            "action": "open_conversation"
        }
    )
    
    return {
        "status": "success",
        "message": "Connection accepted",
        "conversation_id": conv_id,
        "other_user_id": requester_id
    }

@router.post("/connections/reject", response_model=Dict[str, Any])
async def reject_connection(payload: ConnectionAction, current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    
    if payload.request_id:
        cursor.execute(
            "SELECT id, requester_id, recipient_id, status FROM user_connections WHERE id = ? AND recipient_id = ?",
            (payload.request_id, current_user["id"])
        )
    elif payload.user_id:
        cursor.execute(
            "SELECT id, requester_id, recipient_id, status FROM user_connections WHERE requester_id = ? AND recipient_id = ?",
            (payload.user_id, current_user["id"])
        )
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Either user_id or request_id must be provided")
        
    req = cursor.fetchone()
    if not req:
        conn.close()
        raise HTTPException(status_code=404, detail="Connection request not found")
        
    cursor.execute("DELETE FROM user_connections WHERE id = ?", (req["id"],))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Connection request rejected", "request_id": req["id"]}
