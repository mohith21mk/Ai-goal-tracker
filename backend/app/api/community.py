from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, validator

from ..database import get_connection
from ..services.community import (
    create_community_comment,
    create_community_post,
    delete_community_post,
    list_community_comments,
    list_community_posts,
    toggle_community_like,
)
from ..services.habits import get_demo_user_id

router = APIRouter()


class PostCreateRequest(BaseModel):
    content: str
    category: Optional[str] = "general"

    @validator("content")
    def validate_content(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Post content cannot be empty")
        if len(s) > 1000:
            raise ValueError("Post content cannot exceed 1000 characters")
        return s

    @validator("category")
    def validate_category(cls, v: Optional[str]) -> str:
        cat = (v or "general").lower()
        if cat not in ("general", "wins", "mindset", "questions"):
            raise ValueError("Category must be 'general', 'wins', 'mindset', or 'questions'")
        return cat


class CommentCreateRequest(BaseModel):
    content: str

    @validator("content")
    def validate_content(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Comment content cannot be empty")
        if len(s) > 500:
            raise ValueError("Comment content cannot exceed 500 characters")
        return s


def get_demo_author_name(user_id: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["full_name"] if row else "Mohith"


@router.get("/posts", response_model=List[Dict[str, Any]])
async def get_posts(category: Optional[str] = Query(default=None)) -> List[Dict[str, Any]]:
    user_id = get_demo_user_id()
    return list_community_posts(user_id=user_id, category=category)


@router.post("/posts", response_model=Dict[str, Any])
async def create_post(payload: PostCreateRequest) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    author_name = get_demo_author_name(user_id)
    return create_community_post(
        user_id=user_id,
        author_name=author_name,
        content=payload.content,
        category=payload.category or "general",
    )


@router.delete("/posts/{post_id}", response_model=Dict[str, Any])
async def delete_post(post_id: int) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    try:
        success = delete_community_post(user_id=user_id, post_id=post_id)
        if not success:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post deleted successfully", "id": post_id}
    except PermissionError:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {err}")


@router.post("/posts/{post_id}/like", response_model=Dict[str, Any])
async def toggle_like(post_id: int) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    try:
        return toggle_community_like(user_id=user_id, post_id=post_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to toggle like: {err}")


@router.get("/posts/{post_id}/comments", response_model=List[Dict[str, Any]])
async def get_comments(post_id: int) -> List[Dict[str, Any]]:
    try:
        return list_community_comments(post_id=post_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/posts/{post_id}/comments", response_model=Dict[str, Any])
async def add_comment(post_id: int, payload: CommentCreateRequest) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    author_name = get_demo_author_name(user_id)
    try:
        return create_community_comment(
            user_id=user_id,
            author_name=author_name,
            post_id=post_id,
            content=payload.content,
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {err}")
