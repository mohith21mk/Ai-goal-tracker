from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from .config import settings as app_settings
from .services.logger import logger
from .services.realtime import start_redis_listener, stop_redis_listener

from .api import auth, blueprints, coach, community, goals, habits, health, journal, missions, progress, reflection, search, settings as api_settings, users, social, chat, notifications, progression, credentials, feedback, admin
from .api.auth import get_current_user
from .api.progress import compute_telemetry
from .database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_redis_listener()
    yield
    await stop_redis_listener()


def create_app() -> FastAPI:
    app = FastAPI(title="AI Goal Coach API", version="0.1.0", lifespan=lifespan)

    logger.info("Initializing AI Goal Coach application...")
    logger.info(f"Environment: {app_settings.ENVIRONMENT}")

    # Initialize database tables and seed initial data
    init_db()

    # Configure CORS securely
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.ALLOWED_ORIGINS,
        allow_origin_regex=r"https://.*\.(vercel\.app|netlify\.app)",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/health", tags=["health"])
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(goals.router, prefix="/api/goals", tags=["goals"])
    app.include_router(missions.router, prefix="/api/missions", tags=["missions"])
    app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
    app.include_router(coach.router, prefix="/api/coach", tags=["coach"])
    app.include_router(habits.router, prefix="/api/habits", tags=["habits"])
    app.include_router(journal.router, prefix="/api/journal", tags=["journal"])
    app.include_router(blueprints.router, prefix="/api/blueprints", tags=["blueprints"])
    app.include_router(search.router, prefix="/api/search", tags=["search"])
    app.include_router(api_settings.router, prefix="/api/settings", tags=["settings"])
    app.include_router(community.router, prefix="/api/community", tags=["community"])
    app.include_router(reflection.router, prefix="/api/reflection", tags=["reflection"])
    app.include_router(social.router, prefix="/api/social", tags=["social"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
    app.include_router(progression.router, prefix="/api/progression", tags=["progression"])
    app.include_router(credentials.router, prefix="/api/credentials", tags=["credentials"])
    app.include_router(feedback.router, tags=["feedback"])
    app.include_router(admin.router)

    # Mount static uploads directory for chat media and attachments
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "chat").mkdir(parents=True, exist_ok=True)
    app.mount("/api/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    @app.get("/api/telemetry", response_model=Dict[str, Any], tags=["telemetry"])
    async def get_telemetry_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        return await compute_telemetry(current_user["id"])

    @app.get("/ready", response_model=Dict[str, Any], tags=["health"])
    async def ready_endpoint(response: Response) -> Dict[str, Any]:
        return await health.health_readiness(response)

    @app.get("/")
    async def root() -> Dict[str, str]:
        return {"message": "AI Goal Coach backend is running"}

    return app


app = create_app()
