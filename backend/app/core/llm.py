# backend/app/core/llm.py

import asyncio
import logging

import google.generativeai as genai
from google.api_core.exceptions import (
    DeadlineExceeded,
    GoogleAPIError,
    ResourceExhausted,
    ServiceUnavailable,
)
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.rate_limiter import llm_rate_limiter

logger = logging.getLogger(__name__)

_gemini_models: dict[str, genai.GenerativeModel] = {}
MODEL_ALIASES = {
    "gpt-4o-mini": "gemini-2.0-flash",
    "gpt-4o": "gemini-2.5-pro",
    "gemini-1.5-flash": "gemini-2.0-flash",
    "gemini-1.5-pro": "gemini-2.5-pro",
}


class LLMConfigurationError(RuntimeError):
    """Raised when the app is missing required LLM configuration."""


class LLMServiceError(RuntimeError):
    """Raised when the upstream LLM provider request fails."""


def get_gemini_model(model_name: str) -> genai.GenerativeModel:
    model_name = MODEL_ALIASES.get(model_name, model_name)
    if not settings.GEMINI_API_KEY:
        raise LLMConfigurationError(
            "GEMINI_API_KEY is not configured for the backend."
        )

    if model_name not in _gemini_models:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_models[model_name] = genai.GenerativeModel(model_name)

    return _gemini_models[model_name]


# Cost per 1000 tokens (approximate, update as Gemini pricing changes)
COST_PER_1K = {
    "gemini-2.0-flash": {"input": 0.000075, "output": 0.000300},
    "gemini-2.5-pro": {"input": 0.001250, "output": 0.005000},
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ResourceExhausted, DeadlineExceeded, ServiceUnavailable)),
    reraise=True,
)
async def safe_llm_call(
    prompt: str,
    system_prompt: str = "You are a helpful school management AI assistant.",
    model: str = "gemini-2.0-flash",
    max_tokens: int = 800,
    temperature: float = 0.3,
    expect_json: bool = False,
) -> tuple[str, float]:
    """
    Make a safe Gemini API call with:
    - Token bucket rate limiting (max 50 calls/min)
    - Automatic retry with exponential backoff
    - Cost tracking

    Returns:
        (response_text, cost_usd)

    Model choice guide:
        gemini-2.0-flash  → routine prompts, summaries, quick generation
        gemini-2.5-pro    → more complex analysis and longer outputs

    Example:
        text, cost = await safe_llm_call(
            prompt="Analyse this student's marks: ...",
            model="gemini-2.0-flash",
            expect_json=True
        )
    """
    async with llm_rate_limiter:
        model = MODEL_ALIASES.get(model, model)
        gemini_model = get_gemini_model(model)

        final_prompt = (
            f"System instructions:\n{system_prompt}\n\n"
            f"User request:\n{prompt}"
        )
        if expect_json:
            final_prompt += (
                "\n\nReturn valid JSON only. Do not wrap it in markdown fences."
            )

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if expect_json:
            generation_config["response_mime_type"] = "application/json"

        try:
            response = await asyncio.to_thread(
                gemini_model.generate_content,
                final_prompt,
                generation_config=generation_config,
            )
        except GoogleAPIError as exc:
            logger.exception("Gemini request failed for model %s", model)
            if isinstance(exc, ResourceExhausted):
                raise LLMServiceError(
                    "Gemini quota exceeded for the configured API key. "
                    "Update billing or replace GEMINI_API_KEY in backend/.env."
                ) from exc
            raise LLMServiceError(f"Gemini request failed: {exc}") from exc

        text = getattr(response, "text", "") or ""
        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) or 0
        total_tokens = getattr(usage, "total_token_count", prompt_tokens + completion_tokens)

        rates = COST_PER_1K.get(model, COST_PER_1K["gemini-2.0-flash"])
        cost = (
            (prompt_tokens / 1000) * rates["input"] +
            (completion_tokens / 1000) * rates["output"]
        )

        logger.debug(
            "LLM call: model=%s tokens=%s cost=$%.6f",
            model,
            total_tokens,
            cost,
        )

        return text, cost
