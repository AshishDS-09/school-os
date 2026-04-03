import google.generativeai as genai

from app.core.config import settings
from app.core.llm import LLMConfigurationError, LLMServiceError

if not settings.GEMINI_API_KEY:
    raise LLMConfigurationError("GEMINI_API_KEY is not configured for the backend.")

genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")


def ask_gemini(prompt: str):
    try:
        response = model.generate_content(prompt)
    except Exception as exc:
        raise LLMServiceError(f"Gemini request failed: {exc}") from exc

    text = getattr(response, "text", "") or ""
    if not text:
        raise LLMServiceError("Gemini returned an empty response.")

    return text
