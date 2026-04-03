from fastapi import APIRouter, HTTPException

from app.services.gemini_service import ask_gemini
from app.core.llm import LLMConfigurationError, LLMServiceError

router = APIRouter()


@router.get("/ask")
def ask_ai(q: str):
    try:
        answer = ask_gemini(q)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"response": answer}
