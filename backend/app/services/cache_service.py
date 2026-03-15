# backend/app/services/cache_service.py

import json
import redis.asyncio as aioredis
from typing import Optional, Any
from app.core.config import settings

# Shared Redis client for caching
_cache_client = None

async def get_cache_client() -> aioredis.Redis:
    global _cache_client
    if _cache_client is None:
        _cache_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _cache_client


# ── TTL strategy: how long each data type lives in cache ────────────
# Short TTL = fresher data but more DB hits
# Long TTL  = faster but potentially stale data
CACHE_TTL = {
    "student_list":     300,   # 5 min  — student roster changes rarely
    "student_detail":   600,   # 10 min — individual student profile
    "class_report":     600,   # 10 min — class performance summary
    "attendance_today": 120,   # 2 min  — changes every time teacher marks
    "fee_status":       900,   # 15 min — changes only on payment
    "agent_dashboard":  60,    # 1 min  — admin wants near-real-time
    "marks_summary":    300,   # 5 min  — subject averages
}


async def cache_get(key: str) -> Optional[Any]:
    """
    Read a value from Redis cache.
    Returns None if key doesn't exist or has expired.
    """
    client = await get_cache_client()
    data = await client.get(key)
    if data:
        return json.loads(data)
    return None


async def cache_set(key: str, value: Any, ttl: int) -> None:
    """
    Write a value to Redis cache with expiry.
    value must be JSON-serialisable (dicts, lists, strings, numbers).
    """
    client = await get_cache_client()
    await client.setex(key, ttl, json.dumps(value, default=str))


async def cache_invalidate(pattern: str) -> None:
    """
    Delete all keys matching a pattern.
    Call this whenever data changes so stale cache is cleared.
    
    Example: when a new student is added to school 1:
        await cache_invalidate("students:1:*")
    This clears student_list, student_detail, class_report etc. for that school.
    """
    client = await get_cache_client()
    keys = await client.keys(pattern)
    if keys:
        await client.delete(*keys)


def make_cache_key(resource: str, school_id: int, *args) -> str:
    """
    Build a consistent, namespaced cache key.
    
    Examples:
        make_cache_key("students", 1)           → "students:1"
        make_cache_key("students", 1, 42)       → "students:1:42"
        make_cache_key("attendance", 1, "today") → "attendance:1:today"
    """
    parts = [resource, str(school_id)] + [str(a) for a in args]
    return ":".join(parts)