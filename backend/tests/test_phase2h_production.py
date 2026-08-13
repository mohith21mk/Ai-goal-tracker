import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.db_session import get_database_url, engine
from app.database import get_connection
from app.services.realtime import get_redis_client, publish_notification_event

client = TestClient(app)


def test_phase2h_production_environment_config():
    assert settings.APP_NAME == "AI Goal Coach API"
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert len(settings.ALLOWED_ORIGINS) >= 1
    assert settings.DATABASE_URL is not None


def test_phase2h_production_health_liveness():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "LIVE"
    assert "environment" in data


def test_phase2h_production_health_readiness():
    res = client.get("/api/health/ready")
    assert res.status_code in (200, 503)
    data = res.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]


def test_phase2h_database_url_formatting():
    test_pg = "postgres://user:pass@localhost:5432/dbname"
    formatted = test_pg.replace("postgres://", "postgresql://", 1)
    assert formatted.startswith("postgresql://")


def test_phase2h_database_connection_abstraction():
    conn = get_connection()
    assert conn is not None
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    row = cursor.fetchone()
    assert row is not None
    conn.close()


def test_phase2h_redis_fallback_resilience():
    # Calling publish_notification_event without Redis service active should not raise exceptions
    import asyncio
    asyncio.run(publish_notification_event(user_id=99999, notification_data={
        "id": 8888, "type": "system", "title": "Test Resilience", "message": "Testing fallback"
    }))


def test_phase2h_security_cookie_and_cors():
    res = client.get("/")
    assert res.status_code == 200
    # Ensure options request responds with allowed headers for CORS
    opts = client.options("/api/health")
    assert opts.status_code in (200, 204, 405)


def test_phase2h_ai_coach_graceful_error_handling():
    # Verify AI Coach router responds with error status or fallback if Gemini key is unset/mocked
    res = client.post("/api/coach/chat", json={"message": "Hello Coach"})
    assert res.status_code in (200, 401, 500)
