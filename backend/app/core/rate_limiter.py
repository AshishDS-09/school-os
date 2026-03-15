# backend/app/core/rate_limiter.py

import asyncio
import redis.asyncio as aioredis
from app.core.config import settings

# Single shared Redis client for rate limiting
_redis_client = None

async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


class OpenAIRateLimiter:
    """
    Token bucket rate limiter for OpenAI API calls.
    
    Allows max 50 calls per minute across ALL agents and ALL schools.
    If bucket is empty, waits 2 seconds and retries automatically.
    
    This prevents a scenario where 500 students all trigger the academic
    agent at once (after bulk marks entry) and generate a $500 API bill.
    
    Usage inside any agent:
        async with openai_rate_limiter:
            response = await openai_client.chat.completions.create(...)
    """
    BUCKET_KEY     = "openai:rate_limit:tokens"
    MAX_TOKENS     = 50    # max calls per minute
    REFILL_SECONDS = 60    # bucket refills every 60 seconds

    async def _init_bucket(self):
        """Create the bucket if it doesn't exist yet"""
        r = await get_redis()
        exists = await r.exists(self.BUCKET_KEY)
        if not exists:
            await r.setex(self.BUCKET_KEY, self.REFILL_SECONDS, self.MAX_TOKENS)

    async def __aenter__(self):
        await self._init_bucket()
        r = await get_redis()
        while True:
            tokens = await r.get(self.BUCKET_KEY)
            if tokens and int(tokens) > 0:
                await r.decr(self.BUCKET_KEY)
                return  # got a token — proceed with OpenAI call
            # Bucket empty — wait and retry
            await asyncio.sleep(2)

    async def __aexit__(self, *args):
        pass  # nothing to clean up


# Global singleton — import this in every agent
openai_rate_limiter = OpenAIRateLimiter()