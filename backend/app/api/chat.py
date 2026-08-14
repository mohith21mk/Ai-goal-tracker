import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..database import get_connection
from .auth import get_current_user
from ..services.auth import get_user_from_session
from ..services.websocket import manager
from ..services.notifications import create_notification
from ..services.realtime import publish_chat_event

router = APIRouter()


class CreateConversationRequest(BaseModel):
    target_user_id: Optional[int] = None
    user_id: Optional[int] = None


async def get_current_user_ws(websocket: WebSocket) -> Optional[Dict[str, Any]]:
    token = websocket.cookies.get("mkc_session")
    if not token:
        # Check query parameters for token (useful for clients passing token=...)
        token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return None
    user = get_user_from_session(token)
    if not user:
        await websocket.close(code=1008)
        return None
    return user


@router.post("/conversations", response_model=Dict[str, Any])
async def create_or_get_conversation(
    payload: CreateConversationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    target_id = payload.target_user_id or payload.user_id
    if not target_id:
        raise HTTPException(status_code=400, detail="target_user_id is required")
    if target_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot start conversation with yourself")

    conn = get_connection()
    cursor = conn.cursor()

    # Validate target user exists
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (target_id,))
    target_user = cursor.fetchone()
    if not target_user:
        conn.close()
        raise HTTPException(status_code=404, detail="Target user not found")

    # Verify accepted connection exists between the two users
    cursor.execute(
        """
        SELECT status FROM user_connections
        WHERE (requester_id = ? AND recipient_id = ?)
           OR (requester_id = ? AND recipient_id = ?)
        """,
        (current_user["id"], target_id, target_id, current_user["id"])
    )
    connection = cursor.fetchone()
    if not connection or connection["status"] != "accepted":
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="You must be connected to message this user."
        )

    # Check for existing 1-to-1 conversation
    cursor.execute(
        """
        SELECT c.id FROM conversations c
        JOIN conversation_members cm1 ON c.id = cm1.conversation_id
        JOIN conversation_members cm2 ON c.id = cm2.conversation_id
        WHERE cm1.user_id = ? AND cm2.user_id = ?
        """,
        (current_user["id"], target_id)
    )
    existing = cursor.fetchone()
    if existing:
        conv_id = existing["id"]
        conn.close()
        return {"id": conv_id, "conversation_id": conv_id, "is_new": False}

    # Create new conversation
    cursor.execute("INSERT INTO conversations DEFAULT VALUES")
    conv_id = cursor.lastrowid
    cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, current_user["id"]))
    cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, target_id))
    conn.commit()
    conn.close()

    return {"id": conv_id, "conversation_id": conv_id, "is_new": True}


@router.delete("/messages/{message_id}", response_model=Dict[str, Any])
async def delete_message(
    message_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, sender_id, conversation_id FROM chat_messages WHERE id = ?",
        (message_id,)
    )
    message = cursor.fetchone()

    if not message:
        conn.close()
        raise HTTPException(status_code=404, detail="Message not found")

    if message["sender_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="You can only delete your own messages")

    cursor.execute("DELETE FROM chat_messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()

    return {"status": "success", "message": "Message deleted", "id": message_id}


@router.get("/conversations", response_model=List[Dict[str, Any]])
async def get_conversations(current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, c.updated_at, 
               u.id as other_user_id, u.username as other_username, u.avatar_initials as other_avatar, u.full_name as other_full_name,
               (SELECT message FROM chat_messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message,
               (SELECT created_at FROM chat_messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message_time,
               (SELECT COUNT(*) FROM chat_messages m WHERE m.conversation_id = c.id AND m.sender_id != ? AND m.read_at IS NULL) as unread_count
        FROM conversations c
        JOIN conversation_members cm1 ON c.id = cm1.conversation_id
        JOIN conversation_members cm2 ON c.id = cm2.conversation_id
        JOIN users u ON cm2.user_id = u.id
        WHERE cm1.user_id = ? AND cm2.user_id != ?
        ORDER BY c.updated_at DESC
    """, (current_user["id"], current_user["id"], current_user["id"]))
    
    convs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return convs


@router.get("/conversations/{conversation_id}/messages", response_model=List[Dict[str, Any]])
async def get_conversation_messages(
    conversation_id: int,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verify user is in conversation
    cursor.execute(
        "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND user_id = ?", 
        (conversation_id, current_user["id"])
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
        
    # Fetch messages
    cursor.execute("""
        SELECT m.id, m.conversation_id, m.sender_id, m.message as content, m.message, m.created_at, m.read_at, u.username as sender_username
        FROM chat_messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.conversation_id = ?
        ORDER BY m.created_at ASC
        LIMIT ?
    """, (conversation_id, limit))
    
    messages = [dict(row) for row in cursor.fetchall()]
    
    # Mark as read
    cursor.execute(
        "UPDATE chat_messages SET read_at = CURRENT_TIMESTAMP WHERE conversation_id = ? AND sender_id != ? AND read_at IS NULL",
        (conversation_id, current_user["id"])
    )
    conn.commit()
    conn.close()
    
    return messages


@router.post("/conversations/{conversation_id}/read", response_model=Dict[str, Any])
async def mark_conversation_read(
    conversation_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
        (conversation_id, current_user["id"])
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    cursor.execute(
        "UPDATE chat_messages SET read_at = CURRENT_TIMESTAMP WHERE conversation_id = ? AND sender_id != ? AND read_at IS NULL",
        (conversation_id, current_user["id"])
    )
    read_count = cursor.rowcount
    conn.commit()
    conn.close()

    return {"status": "success", "read_count": read_count}


@router.websocket("/ws")
@router.websocket("/ws/conversations/{target_conv_id}")
async def websocket_endpoint(websocket: WebSocket, target_conv_id: Optional[int] = None):
    user = await get_current_user_ws(websocket)
    if not user:
        return
        
    user_id = user["id"]
    await manager.connect(websocket, user_id)
    await websocket.send_json({"type": "connection.ready", "user_id": user_id})

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                event_type = payload.get("type", "message.send")
                conversation_id = payload.get("conversation_id") or target_conv_id
                message_text = payload.get("content") or payload.get("message")
                
                if conversation_id and message_text:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    # Verify user is in conversation
                    cursor.execute(
                        "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND user_id = ?", 
                        (conversation_id, user_id)
                    )
                    if cursor.fetchone():
                        # Save message
                        cursor.execute(
                            "INSERT INTO chat_messages (conversation_id, sender_id, message) VALUES (?, ?, ?)",
                            (conversation_id, user_id, message_text)
                        )
                        msg_id = cursor.lastrowid
                        cursor.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conversation_id,))
                        
                        # Fetch sender username
                        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                        sender_row = cursor.fetchone()
                        sender_username = sender_row["username"] if sender_row else "Someone"
                        
                        # Find recipient
                        cursor.execute(
                            "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND user_id != ?",
                            (conversation_id, user_id)
                        )
                        other_member = cursor.fetchone()
                        recipient_id = other_member["user_id"] if other_member else None
                        
                        conn.commit()
                        conn.close()
                        
                        # Create notification for recipient
                        if recipient_id:
                            await create_notification(
                                user_id=recipient_id,
                                type="chat_message",
                                title="New Message",
                                message=f"New message from @{sender_username}",
                                reference_type="conversation",
                                reference_id=conversation_id
                            )
                        
                        # Broadcast event via Redis & local manager
                        event_data = {
                            "type": "message.created",
                            "message": {
                                "id": msg_id,
                                "conversation_id": conversation_id,
                                "sender_id": user_id,
                                "sender_username": sender_username,
                                "content": message_text,
                                "message": message_text,
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "read_at": None
                            },
                            "conversation_id": conversation_id,
                            "sender_id": user_id,
                            "recipient_id": recipient_id
                        }
                        await publish_chat_event(conversation_id, event_data)
                        
                        # Send ack to sender
                        await websocket.send_json({"type": "message.ack", "message_id": msg_id, "conversation_id": conversation_id})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON format"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

