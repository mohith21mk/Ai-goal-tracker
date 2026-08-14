import json
import asyncio
from typing import Dict, Any, Optional
from .logger import logger
from .websocket import manager

_redis_client = None
_pubsub_task = None

def get_redis_client():
    """
    Returns initialized Redis client if REDIS_URL is configured and redis-py is installed.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis.asyncio as redis
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        return _redis_client
    except Exception as err:
        # Check if error is related to connection/availability to avoid spamming
        msg = str(err)
        if "Error 22" in msg or "ConnectionRefusedError" in msg or "not found" in msg:
            logger.info("Redis unavailable, using local WebSocket ConnectionManager fallback.")
        else:
            logger.warning(f"Redis initialization unavailable: {err}. Falling back to in-memory WebSocket ConnectionManager.")
        return None


async def publish_chat_event(conversation_id: int, event_data: Dict[str, Any]) -> None:
    """
    Publishes real-time message event to Redis pub/sub channel conversation:{id}.
    Falls back gracefully to local WebSocket manager if Redis is offline.
    """
    event_str = json.dumps(event_data)
    redis_cli = get_redis_client()

    redis_published = False
    if redis_cli:
        try:
            channel_name = f"conversation:{conversation_id}"
            await redis_cli.publish(channel_name, event_str)
            redis_published = True
        except Exception as err:
            logger.warning(f"Failed to publish to Redis channel: {err}. Falling back to local dispatch.")

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
    payload_str = json.dumps(payload)
    redis_cli = get_redis_client()

    redis_published = False
    if redis_cli:
        try:
            channel_name = f"user:{user_id}:notifications"
            await redis_cli.publish(channel_name, payload_str)
            redis_published = True
        except Exception as err:
            logger.warning(f"Failed to publish notification to Redis: {err}. Falling back to local dispatch.")

    if not redis_published:
        await manager.send_personal_json(payload, user_id)


async def start_redis_listener() -> None:
    """
    Background worker task subscribing to Redis Pub/Sub channels to distribute events
    across multiple production application workers.
    """
    global _pubsub_task
    redis_cli = get_redis_client()
    if not redis_cli:
        return

    async def _listener_loop():
        retry_delay = 1
        while True:
            try:
                pubsub = redis_cli.pubsub()
                await pubsub.psubscribe("conversation:*", "user:*:notifications")
                logger.info("Redis Pub/Sub listener active on channels 'conversation:*' and 'user:*:notifications'.")
                retry_delay = 1 # reset on successful connection
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
                break
            except Exception as err:
                msg = str(err)
                if "Error 22" not in msg and "not found" not in msg:
                    logger.warning(f"Redis Pub/Sub listener disconnected: {err}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

    _pubsub_task = asyncio.create_task(_listener_loop())


async def stop_redis_listener() -> None:
    global _pubsub_task
    if _pubsub_task and not _pubsub_task.done():
        _pubsub_task.cancel()
        try:
            await _pubsub_task
        except asyncio.CancelledError:
            pass
    _pubsub_task = None
