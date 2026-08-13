import sqlite3
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..database import get_connection
from .auth import get_current_user
from ..services.notifications import create_notification

router = APIRouter()

class ConnectionAction(BaseModel):
    user_id: int

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_users(q: str = Query(..., min_length=3), current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    search_term = f"%{q}%"
    cursor.execute("""
        SELECT id, username, full_name, avatar_initials, bio 
        FROM users 
        WHERE (username LIKE ? OR full_name LIKE ?) AND id != ?
        LIMIT 20
    """, (search_term, search_term, current_user["id"]))
    
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
        SELECT u.id, u.username, u.full_name, u.avatar_initials, c.status,
               CASE WHEN c.requester_id = ? THEN 'sent' ELSE 'received' END as direction
        FROM user_connections c
        JOIN users u ON (c.requester_id = u.id OR c.recipient_id = u.id)
        WHERE (c.requester_id = ? OR c.recipient_id = ?) AND u.id != ?
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

@router.post("/connections/request", response_model=Dict[str, str])
async def request_connection(payload: ConnectionAction, current_user: Dict[str, Any] = Depends(get_current_user)):
    target_id = payload.user_id
    if target_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot connect to yourself")
        
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE id = ?", (target_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    cursor.execute("SELECT status FROM user_connections WHERE (requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?)",
                  (current_user["id"], target_id, target_id, current_user["id"]))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Connection already exists with status: {existing['status']}")
        
    cursor.execute("INSERT INTO user_connections (requester_id, recipient_id, status) VALUES (?, ?, 'pending')",
                  (current_user["id"], target_id))
    conn.commit()
    conn.close()
    
    # Notify recipient
    await create_notification(
        user_id=target_id,
        type="connection_request",
        title="New Connection Request",
        message=f"@{current_user['username']} sent you a connection request.",
        reference_type="user",
        reference_id=current_user["id"]
    )
    
    return {"status": "success", "message": "Connection request sent"}

@router.post("/connections/accept", response_model=Dict[str, str])
async def accept_connection(payload: ConnectionAction, current_user: Dict[str, Any] = Depends(get_current_user)):
    requester_id = payload.user_id
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT status FROM user_connections WHERE requester_id = ? AND recipient_id = ?",
                  (requester_id, current_user["id"]))
    req = cursor.fetchone()
    
    if not req or req["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=400, detail="No pending request found from this user")
        
    cursor.execute("UPDATE user_connections SET status = 'accepted' WHERE requester_id = ? AND recipient_id = ?",
                  (requester_id, current_user["id"]))
                  
    cursor.execute("""
        SELECT c.id FROM conversations c
        JOIN conversation_members m1 ON c.id = m1.conversation_id
        JOIN conversation_members m2 ON c.id = m2.conversation_id
        WHERE m1.user_id = ? AND m2.user_id = ?
    """, (current_user["id"], requester_id))
    
    if not cursor.fetchone():
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
        reference_type="user",
        reference_id=current_user["id"]
    )
    
    return {"status": "success", "message": "Connection accepted"}

@router.post("/connections/reject", response_model=Dict[str, str])
async def reject_connection(payload: ConnectionAction, current_user: Dict[str, Any] = Depends(get_current_user)):
    requester_id = payload.user_id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_connections WHERE requester_id = ? AND recipient_id = ?",
                  (requester_id, current_user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Connection request rejected"}
