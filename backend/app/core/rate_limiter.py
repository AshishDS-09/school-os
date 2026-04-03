# backend/app/core/rate_limiter.py

import asyncio
import logging
import time
import redis.asyncio as aioredis
from redis.exceptions import RedisError
from app.core.config import settings

# Keep async Redis clients scoped to the current event loop.
# Sharing one asyncio client across Celery task loops causes
# "Future attached to a different loop" / "Event loop is closed" errors.
_redis_clients: dict[int, aioredis.Redis] = {}
logger = logging.getLogger(__name__)

async def get_redis():
    loop_id = id(asyncio.get_running_loop())
    client = _redis_clients.get(loop_id)
    if client is None:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        _redis_clients[loop_id] = client
    return client


class LLMRateLimiter:
    """
    Token bucket rate limiter for Gemini API calls.
    
    Allows max 50 calls per minute across ALL agents and ALL schools.
    If bucket is empty, waits 2 seconds and retries automatically.
    
    This prevents a scenario where 500 students all trigger the academic
    agent at once (after bulk marks entry) and generate a $500 API bill.
    
    Usage inside any agent:
        async with llm_rate_limiter:
            response = await gemini_model.generate_content(...)
    """
    BUCKET_KEY     = "llm:rate_limit:tokens"
    MAX_TOKENS     = 50    # max calls per minute
    REFILL_SECONDS = 60    # bucket refills every 60 seconds

    def __init__(self):
        self._local_locks: dict[int, asyncio.Lock] = {}
        self._local_tokens = self.MAX_TOKENS
        self._local_reset_at = time.monotonic() + self.REFILL_SECONDS

    def _get_local_lock(self) -> asyncio.Lock:
        loop_id = id(asyncio.get_running_loop())
        lock = self._local_locks.get(loop_id)
        if lock is None:
            lock = asyncio.Lock()
            self._local_locks[loop_id] = lock
        return lock

    async def _init_bucket(self):
        """Create the bucket if it doesn't exist yet"""
        r = await get_redis()
        exists = await r.exists(self.BUCKET_KEY)
        if not exists:
            await r.setex(self.BUCKET_KEY, self.REFILL_SECONDS, self.MAX_TOKENS)

    async def _acquire_local_token(self):
        """Fallback token bucket for local development when Redis is unavailable."""
        while True:
            async with self._get_local_lock():
                now = time.monotonic()
                if now >= self._local_reset_at:
                    self._local_tokens = self.MAX_TOKENS
                    self._local_reset_at = now + self.REFILL_SECONDS

                if self._local_tokens > 0:
                    self._local_tokens -= 1
                    return
            await asyncio.sleep(2)

    async def __aenter__(self):
        try:
            await self._init_bucket()
            r = await get_redis()
            while True:
                tokens = await r.get(self.BUCKET_KEY)
                if tokens and int(tokens) > 0:
                    await r.decr(self.BUCKET_KEY)
                    return
                # Bucket empty — wait and retry
                await asyncio.sleep(2)
        except (RedisError, RuntimeError):
            logger.warning(
                "Redis is unavailable for Gemini rate limiting, or async state "
                "cannot be reused in this event loop. "
                "Falling back to an in-memory token bucket."
            )
            await self._acquire_local_token()

    async def __aexit__(self, *args):
        pass  # nothing to clean up


# Global singleton — import this in every Gemini-backed LLM call
llm_rate_limiter = LLMRateLimiter()
