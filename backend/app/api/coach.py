from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.ai_coach import generate_coaching_response

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat", response_model=Dict[str, Any])
async def chat_with_coach(payload: ChatRequest) -> Dict[str, Any]:
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message prompt cannot be empty")

    response_data = await generate_coaching_response(payload.message.strip())
    return response_data
