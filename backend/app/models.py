from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    email: str
    full_name: str
    is_active: bool = True
    created_at: Optional[str] = None


@dataclass
class Goal:
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    category: str = "general"
    status: str = "active"
    target_date: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Mission:
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
