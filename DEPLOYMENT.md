# Mastery Key Coach (MKC) — Production Deployment Guide

## 1. System Architecture Overview

```
                        [ Internet User ]
                                │
                                ▼
                       [ HTTPS Port 443 ]
                                │
                       [ Reverse Proxy / Nginx ]
                                │
             ┌──────────────────┴──────────────────┐
             ▼                                     ▼
   [Frontend Static SPA]                 [Backend API Gunicorn/Uvicorn]
 (React 19 / Vite / Nginx)                     (FastAPI / Python 3.11)
             │                                     │
             │                           ┌─────────┴─────────┐
             ▼                           ▼                   ▼
    [Browser Client]             [PostgreSQL 16]      [Redis 7 Broker]
 (WebSockets wss://)             (Relational DB)     (Pub/Sub & Sockets)
```

---

## 2. Environment Variables & Security Configuration

Create a `.env` file in the root directory based on `.env.example`:

| Environment Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Yes | `production` | App environment (`development`, `staging`, `production`). |
| `DEBUG` | Yes | `false` | Disable debug stack traces in production. |
| `SECRET_KEY` | **Yes** | *None* | 64-char secret key for JWT session signing. |
| `DATABASE_URL` | **Yes** | `postgresql://...` | PostgreSQL connection string. |
| `REDIS_URL` | **Yes** | `redis://...` | Redis connection URL for multi-worker WebSocket event distribution. |
| `GEMINI_API_KEY` | **Yes** | *None* | Google Gemini AI API key for RAG Coach inference. |
| `FRONTEND_URL` | **Yes** | `https://app...` | Production frontend domain for CORS origins. |
| `CORS_ORIGINS` | No | `$FRONTEND_URL` | Comma-separated list of allowed CORS origins. |
| `SESSION_COOKIE_SECURE` | Yes | `true` | Enforces HTTPS-only cookies in production. |

---

## 3. Database Migration & Setup

### Alembic Migrations
Run database migrations before starting the application:

```bash
cd backend
alembic upgrade head
```

---

## 4. Docker Production Deployment

To start the complete production stack (PostgreSQL 16, Redis 7, Backend Uvicorn/Gunicorn, Frontend Nginx):

```bash
docker-compose up -d --build
```

### Container Health Probes
- **Liveness Probe**: `GET http://localhost:8000/api/health`
- **Readiness Probe**: `GET http://localhost:8000/api/health/ready`

---

## 5. WebSockets & Nginx Reverse Proxy Setup

Nginx must proxy `/api/chat/ws` and `/api/notifications/ws` with WebSocket upgrade headers:

```nginx
location /api/chat/ws {
    proxy_pass http://backend:8000/api/chat/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $host;
}
```

---

## 6. Backup & Disaster Recovery Procedures

### PostgreSQL Automated Backup
```bash
docker exec -t mkc_postgres pg_dump -U mkc_user -d mkc_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### PostgreSQL Restore
```bash
gunzip -c backup_20260812_120000.sql.gz | docker exec -i mkc_postgres psql -U mkc_user -d mkc_db
```
