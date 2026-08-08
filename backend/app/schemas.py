from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool = True
    created_at: Optional[str] = None


class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = "general"
    target_date: Optional[str] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    target_date: Optional[str] = None


class GoalResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    category: str = "general"
    status: str = "active"
    target_date: Optional[str] = None
    created_at: Optional[str] = None


class MissionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = "general"
    time: Optional[str] = "15 min"
    difficulty: Optional[str] = "easy"
    xp_reward: Optional[int] = 10
    goal_id: Optional[int] = None


class MissionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str = "general"
    time: str = "15 min"
    difficulty: str = "easy"
    xp_reward: int = 10
    completed: bool = False
    user_id: Optional[int] = None
    goal_id: Optional[int] = None


class ProgressUpdate(BaseModel):
    completed: bool
