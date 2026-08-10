from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..services.ai_coach import (
    delete_chat_history,
    fetch_chat_history,
    generate_coaching_response,
)
from .auth import get_current_user

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.get("/history", response_model=Dict[str, Any])
async def get_history(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    try:
        if not isinstance(limit, int):
            limit = int(getattr(limit, "default", 50))
        user_id = current_user["id"]
        messages = fetch_chat_history(user_id=user_id, limit=limit)
        return {"messages": messages, "count": len(messages)}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat history: {err}")


@router.delete("/history", response_model=Dict[str, Any])
async def clear_history(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        user_id = current_user["id"]
        deleted_count = delete_chat_history(user_id=user_id)
        return {"message": "Chat history cleared successfully", "deleted_count": deleted_count}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {err}")


@router.post("/chat", response_model=Dict[str, Any])
async def chat_with_coach(
    payload: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message prompt cannot be empty")

    user_id = current_user["id"]
    try:
        response_data = await generate_coaching_response(payload.message.strip(), user_id)
        return response_data
    except RuntimeError as err:
        raise HTTPException(status_code=500, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {err}")
