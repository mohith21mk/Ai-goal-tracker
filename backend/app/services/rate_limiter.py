import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable, Optional, Tuple
from fastapi import HTTPException, Request, status

from .logger import logger
from .realtime import get_redis_client

# In-memory sliding window fallback
_in_memory_buckets = defaultdict(deque)
_lock = Lock()


async def check_rate_limit(key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
    """
    Checks rate limit using Redis if connected, or sliding window in-memory fallback.
    Returns (is_limited: bool, retry_after: int).
    """
    redis_cli = get_redis_client()
    now = time.time()

    if redis_cli:
        try:
            redis_key = f"ratelimit:{key}"
            pipe = redis_cli.pipeline()
            pipe.incr(redis_key)
            pipe.ttl(redis_key)
            results = await pipe.execute()
            count = results[0]
            ttl = results[1]

            if count == 1 or ttl == -1:
                await redis_cli.expire(redis_key, window_seconds)
                ttl = window_seconds

            if count > max_requests:
                return True, max(1, ttl)
            return False, 0
        except Exception as err:
            logger.debug(f"Redis rate limiting fallback to in-memory: {err}")

    # Fallback in-memory rate limiter
    with _lock:
        timestamps = _in_memory_buckets[key]
        cutoff = now - window_seconds
        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()

        if len(timestamps) >= max_requests:
            oldest = timestamps[0]
            retry_after = max(1, int(window_seconds - (now - oldest)))
            return True, retry_after

        timestamps.append(now)
        return False, 0


def rate_limit(
    max_requests: int,
    window_seconds: int,
    key_prefix: str = "general",
    get_key: Optional[Callable[[Request], str]] = None,
):
    """
    FastAPI dependency for endpoint-level rate limiting.
    """
    async def dependency(request: Request):
        if get_key:
            identifier = get_key(request)
        else:
            # Client IP identifier with X-Forwarded-For support
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
            else:
                client_ip = request.client.host if request.client else "unknown"
            identifier = client_ip

        bucket_key = f"{key_prefix}:{identifier}"
        is_limited, retry_after = await check_rate_limit(bucket_key, max_requests, window_seconds)

        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please wait {retry_after} seconds before trying again.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
