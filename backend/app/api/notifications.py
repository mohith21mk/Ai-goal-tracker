from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from .auth import get_current_user
from ..services.auth import get_user_from_session
from ..services.notifications import (
    delete_notification,
    get_unread_notification_count,
    get_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from ..services.websocket import manager

router = APIRouter()


async def get_current_user_ws(websocket: WebSocket) -> Optional[Dict[str, Any]]:
    token = websocket.cookies.get("mkc_session")
    if not token:
        token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return None
    user = get_user_from_session(token)
    if not user:
        await websocket.close(code=1008)
        return None
    return user


@router.get("", response_model=List[Dict[str, Any]])
async def get_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    user_id = current_user["id"]
    return get_user_notifications(user_id=user_id, limit=limit, offset=offset)


@router.get("/unread-count", response_model=Dict[str, int])
async def get_unread_count(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, int]:
    user_id = current_user["id"]
    count = get_unread_notification_count(user_id=user_id)
    return {"unread_count": count}


@router.patch("/read_all", response_model=Dict[str, Any])
@router.patch("/read-all", response_model=Dict[str, Any])
async def mark_all_read(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    user_id = current_user["id"]
    updated = mark_all_notifications_read(user_id=user_id)
    return {"status": "success", "message": "All notifications marked as read", "count": updated}


@router.patch("/{notification_id}/read", response_model=Dict[str, str])
async def mark_single_read(
    notification_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    user_id = current_user["id"]
    success = mark_notification_read(user_id=user_id, notification_id=notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success", "message": "Notification marked as read"}


@router.delete("/{notification_id}", response_model=Dict[str, Any])
async def delete_single_notification(
    notification_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    user_id = current_user["id"]
    success = delete_notification(user_id=user_id, notification_id=notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success", "message": "Notification deleted", "id": notification_id}


@router.websocket("/ws")
async def notifications_websocket_endpoint(websocket: WebSocket):
    user = await get_current_user_ws(websocket)
    if not user:
        return

    user_id = user["id"]
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep socket alive and handle client ping/messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
