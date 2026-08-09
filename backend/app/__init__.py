from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, coach, goals, habits, journal, missions, progress, users
from .api.progress import compute_telemetry
from .database import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="AI Goal Coach API", version="0.1.0")

    # Initialize database tables and seed initial data
    init_db()

    # Configure CORS for development frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(goals.router, prefix="/api/goals", tags=["goals"])
    app.include_router(missions.router, prefix="/api/missions", tags=["missions"])
    app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
    app.include_router(coach.router, prefix="/api/coach", tags=["coach"])
    app.include_router(habits.router, prefix="/api/habits", tags=["habits"])
    app.include_router(journal.router, prefix="/api/journal", tags=["journal"])

    @app.get("/api/telemetry", response_model=Dict[str, Any], tags=["telemetry"])
    async def get_telemetry() -> Dict[str, Any]:
        return await compute_telemetry()

    @app.get("/")
    async def root() -> Dict[str, str]:
        return {"message": "AI Goal Coach backend is running"}

    return app


app = create_app()
