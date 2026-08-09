from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..services.ai_coach import (
    generate_coaching_response,
    fetch_chat_history,
    delete_chat_history,
    get_db_context,
)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.get("/history", response_model=Dict[str, Any])
async def get_history(limit: int = Query(default=50, ge=1, le=100)) -> Dict[str, Any]:
    try:
        context = get_db_context()
        user_id = context["user_id"]
        messages = fetch_chat_history(user_id=user_id, limit=limit)
        return {"messages": messages, "count": len(messages)}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat history: {err}")


@router.delete("/history", response_model=Dict[str, Any])
async def clear_history() -> Dict[str, Any]:
    try:
        context = get_db_context()
        user_id = context["user_id"]
        deleted_count = delete_chat_history(user_id=user_id)
        return {"message": "Chat history cleared successfully", "deleted_count": deleted_count}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {err}")


@router.post("/chat", response_model=Dict[str, Any])
async def chat_with_coach(payload: ChatRequest) -> Dict[str, Any]:
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message prompt cannot be empty")

    try:
        response_data = await generate_coaching_response(payload.message.strip())
        return response_data
    except RuntimeError as err:
        raise HTTPException(status_code=500, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {err}")
