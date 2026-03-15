# backend/app/core/llm.py

import asyncio
import logging
from typing import Optional

from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from openai import RateLimitError, APITimeoutError, APIConnectionError

from app.core.config import settings
from app.core.rate_limiter import openai_rate_limiter

logger = logging.getLogger(__name__)

# Single shared OpenAI client for the whole app
_openai_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# Cost per 1000 tokens (approximate, update as OpenAI changes pricing)
COST_PER_1K = {
    "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
    "gpt-4o":      {"input": 0.005000, "output": 0.015000},
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
    reraise=True,
)
async def safe_llm_call(
    prompt: str,
    system_prompt: str = "You are a helpful school management AI assistant.",
    model: str = "gpt-4o-mini",   # cheap model for most tasks
    max_tokens: int = 800,
    temperature: float = 0.3,     # low temp = consistent, structured output
    expect_json: bool = False,     # if True, instructs model to return JSON only
) -> tuple[str, float]:
    """
    Make a safe OpenAI API call with:
    - Token bucket rate limiting (max 50 calls/min)
    - Automatic retry with exponential backoff
    - Cost tracking

    Returns:
        (response_text, cost_usd)

    Model choice guide:
        gpt-4o-mini  → fee reminders, simple alerts, routine messages  (cheap)
        gpt-4o       → lesson plans, learning paths, complex analysis  (expensive)

    Example:
        text, cost = await safe_llm_call(
            prompt="Analyse this student's marks: ...",
            model="gpt-4o-mini",
            expect_json=True
        )
    """
    # Acquire rate limit token — waits if bucket is empty
    async with openai_rate_limiter:
        client = get_openai_client()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ]

        kwargs: dict = dict(
            model       = model,
            messages    = messages,
            max_tokens  = max_tokens,
            temperature = temperature,
        )

        # Ask model to return pure JSON when we need structured data
        if expect_json:
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)

        text = response.choices[0].message.content or ""

        # Calculate approximate cost
        usage = response.usage
        rates = COST_PER_1K.get(model, COST_PER_1K["gpt-4o-mini"])
        cost  = (
            (usage.prompt_tokens     / 1000) * rates["input"] +
            (usage.completion_tokens / 1000) * rates["output"]
        )

        logger.debug(
            f"LLM call: model={model} tokens={usage.total_tokens} "
            f"cost=${cost:.6f}"
        )

        return text, cost