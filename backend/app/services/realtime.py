import json
import asyncio
from typing import Dict, Any, Optional
from .logger import logger
from .websocket import manager
from ..config import settings

_redis_client = None
_pubsub_task = None
_redis_available = False
_logged_offline = False


def get_redis_client():
    """
    Returns initialized async Redis client if REDIS_URL is configured and redis-py is installed.
    Uses connection pooling and socket timeouts to prevent thread starvation.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = settings.REDIS_URL or ""
    if not redis_url:
        return None

    try:
        import redis.asyncio as redis
        _redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=3.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        return _redis_client
    except Exception as err:
        logger.warning(f"Redis client initialization error: {err}. Falling back to in-memory WebSocket manager.")
        return None


async def check_redis_health() -> bool:
    """
    Pings Redis server and returns True if healthy, False otherwise.
    """
    global _redis_available
    redis_cli = get_redis_client()
    if not redis_cli:
        _redis_available = False
        return False
    try:
        await redis_cli.ping()
        _redis_available = True
        return True
    except Exception:
        _redis_available = False
        return False


async def publish_chat_event(conversation_id: int, event_data: Dict[str, Any]) -> None:
    """
    Publishes real-time message event to Redis pub/sub channel conversation:{id}.
    Falls back gracefully to local WebSocket manager if Redis is offline.
    """
    event_str = json.dumps(event_data, default=str)
    redis_cli = get_redis_client()

    redis_published = False
    if redis_cli and _redis_available:
        try:
            channel_name = f"conversation:{conversation_id}"
            await redis_cli.publish(channel_name, event_str)
            redis_published = True
        except Exception as err:
            logger.debug(f"Redis publish failed: {err}. Falling back to local WebSocket dispatch.")

    if not redis_published:
        # Fallback: Dispatch directly to local active connections for recipient/sender
        target_user_id = event_data.get("recipient_id") or event_data.get("sender_id")
        sender_id = event_data.get("sender_id")

        if sender_id:
            await manager.send_personal_message(event_str, sender_id)
        if target_user_id and target_user_id != sender_id:
            await manager.send_personal_message(event_str, target_user_id)


async def publish_notification_event(user_id: int, notification_data: Dict[str, Any]) -> None:
    """
    Publishes real-time notification event to Redis channel user:{user_id}:notifications.
    Falls back gracefully to local WebSocket manager.
    """
    payload = {
        "type": "new_notification",
        "notification": notification_data
    }
    payload_str = json.dumps(payload, default=str)
    redis_cli = get_redis_client()

    redis_published = False
    if redis_cli and _redis_available:
        try:
            channel_name = f"user:{user_id}:notifications"
            await redis_cli.publish(channel_name, payload_str)
            redis_published = True
        except Exception as err:
            logger.debug(f"Redis notification publish failed: {err}. Falling back to local WebSocket dispatch.")

    if not redis_published:
        await manager.send_personal_json(payload, user_id)


async def start_redis_listener() -> None:
    """
    Background worker task subscribing to Redis Pub/Sub channels to distribute events
    across multiple production application workers.
    """
    global _pubsub_task, _redis_available, _logged_offline
    redis_cli = get_redis_client()
    if not redis_cli:
        logger.info("Redis not configured. Operating in single-node in-memory WebSocket mode.")
        return

    async def _listener_loop():
        global _redis_available, _logged_offline
        retry_delay = 1
        while True:
            pubsub = None
            try:
                # Test connectivity with ping before subscribing
                await redis_cli.ping()
                _redis_available = True
                _logged_offline = False

                pubsub = redis_cli.pubsub()
                await pubsub.psubscribe("conversation:*", "user:*:notifications")
                logger.info("Redis Pub/Sub connected on 'conversation:*' and 'user:*:notifications'.")
                retry_delay = 1

                async for message in pubsub.listen():
                    if message and message.get("type") in ("pmessage", "message"):
                        data_str = message.get("data")
                        channel = message.get("channel", "")
                        if not data_str:
                            continue
                        try:
                            data = json.loads(data_str)
                            if channel.startswith("conversation:"):
                                target_user_id = data.get("recipient_id") or data.get("sender_id")
                                sender_id = data.get("sender_id")
                                if sender_id:
                                    await manager.send_personal_message(data_str, sender_id)
                                if target_user_id and target_user_id != sender_id:
                                    await manager.send_personal_message(data_str, target_user_id)
                            elif "notifications" in channel:
                                user_id = data.get("notification", {}).get("user_id") or data.get("user_id")
                                if user_id:
                                    await manager.send_personal_json(data, user_id)
                        except Exception as err:
                            logger.warning(f"Error processing Redis Pub/Sub message: {err}")
            except asyncio.CancelledError:
                if pubsub:
                    try:
                        await pubsub.close()
                    except Exception:
                        pass
                break
            except Exception as err:
                _redis_available = False
                if pubsub:
                    try:
                        await pubsub.close()
                    except Exception:
                        pass
                if not _logged_offline:
                    if settings.ENVIRONMENT == "production":
                        logger.warning(f"Redis Pub/Sub connection offline: {err}. Retrying with backoff...")
                    else:
                        logger.info(f"Redis offline ({err}). Operating in local WebSocket fallback mode.")
                    _logged_offline = True

                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)

    _pubsub_task = asyncio.create_task(_listener_loop())


async def stop_redis_listener() -> None:
    """
    Gracefully shuts down Redis Pub/Sub task and closes client connections.
    """
    global _pubsub_task, _redis_client, _redis_available
    if _pubsub_task and not _pubsub_task.done():
        _pubsub_task.cancel()
        try:
            await _pubsub_task
        except asyncio.CancelledError:
            pass
    _pubsub_task = None

    if _redis_client:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
    _redis_available = False
