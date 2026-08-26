from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator

from ..database import get_connection
from ..services.community import (
    create_community_comment,
    create_community_post,
    delete_community_comment,
    delete_community_like,
    delete_community_post,
    get_post_by_id,
    list_community_comments,
    list_community_posts,
    toggle_community_like,
    update_community_comment,
    update_community_post,
)
from .auth import get_current_user

router = APIRouter()


INAPPROPRIATE_WORDS = {"shit", "fuck", "bitch", "asshole", "crap", "bastard", "damn", "dick", "piss", "cunt"}


def check_positive_language(text: str) -> None:
    words = text.lower().split()
    for w in words:
        cleaned = "".join(ch for ch in w if ch.isalnum())
        if cleaned in INAPPROPRIATE_WORDS:
            raise ValueError("Please keep community interactions positive, respectful, and constructive.")


class PostCreateRequest(BaseModel):
    content: str
    category: Optional[str] = "general"
    credential_id: Optional[int] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Post content cannot be empty")
        if len(s) > 1000:
            raise ValueError("Post content cannot exceed 1000 characters")
        check_positive_language(s)
        return s

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> str:
        cat = (v or "general").lower()
        if cat not in ("general", "wins", "mindset", "questions"):
            raise ValueError("Category must be 'general', 'wins', 'mindset', or 'questions'")
        return cat


class PostUpdateRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Post content cannot be empty")
        if len(s) > 1000:
            raise ValueError("Post content cannot exceed 1000 characters")
        check_positive_language(s)
        return s


class CommentCreateRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Comment content cannot be empty")
        if len(s) > 500:
            raise ValueError("Comment content cannot exceed 500 characters")
        check_positive_language(s)
        return s


class CommentUpdateRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Comment content cannot be empty")
        if len(s) > 500:
            raise ValueError("Comment content cannot exceed 500 characters")
        check_positive_language(s)
        return s


def get_author_display_name(user_id: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, username FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["full_name"] or f"@{row['username']}"
    return "Member"


@router.get("/posts", response_model=List[Dict[str, Any]])
async def get_posts(
    category: Optional[str] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    if not isinstance(category, str) and category is not None:
        category = getattr(category, "default", None)
    user_id = current_user["id"]
    return list_community_posts(user_id=user_id, category=category)


@router.get("/posts/{post_id}", response_model=Dict[str, Any])
async def get_single_post(
    post_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    post = get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/posts", response_model=Dict[str, Any])
async def create_post(
    payload: PostCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    author_name = get_author_display_name(user_id)
    try:
        return create_community_post(
            user_id=user_id,
            author_name=author_name,
            content=payload.content,
            category=payload.category or "general",
            credential_id=payload.credential_id,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.patch("/posts/{post_id}", response_model=Dict[str, Any])
async def update_post(
    post_id: int,
    payload: PostUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    try:
        return update_community_post(user_id=user_id, post_id=post_id, content=payload.content)
    except PermissionError:
        raise HTTPException(status_code=403, detail="You can only edit your own posts")
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.delete("/posts/{post_id}", response_model=Dict[str, Any])
async def delete_post(
    post_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    is_admin = current_user.get("role") == "admin"
    try:
        success = delete_community_post(user_id=user_id, post_id=post_id, is_admin=is_admin)
        if not success:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post deleted successfully", "id": post_id}
    except PermissionError:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {err}")


@router.post("/posts/{post_id}/like", response_model=Dict[str, Any])
async def toggle_like(
    post_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    try:
        return await toggle_community_like(user_id=user_id, post_id=post_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to toggle like: {err}")


@router.delete("/posts/{post_id}/like", response_model=Dict[str, Any])
async def unlike_post(
    post_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    try:
        return delete_community_like(user_id=user_id, post_id=post_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.get("/posts/{post_id}/comments", response_model=List[Dict[str, Any]])
async def get_comments(
    post_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    try:
        return list_community_comments(post_id=post_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/posts/{post_id}/comments", response_model=Dict[str, Any])
async def add_comment(
    post_id: int,
    payload: CommentCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    author_name = get_author_display_name(user_id)
    try:
        return await create_community_comment(
            user_id=user_id,
            author_name=author_name,
            post_id=post_id,
            content=payload.content,
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {err}")


@router.patch("/comments/{comment_id}", response_model=Dict[str, Any])
async def update_comment(
    comment_id: int,
    payload: CommentUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    try:
        return update_community_comment(user_id=user_id, comment_id=comment_id, content=payload.content)
    except PermissionError:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.delete("/comments/{comment_id}", response_model=Dict[str, Any])
async def delete_comment(
    comment_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    try:
        success = delete_community_comment(user_id=user_id, comment_id=comment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Comment not found")
        return {"message": "Comment deleted successfully", "id": comment_id}
    except PermissionError:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
