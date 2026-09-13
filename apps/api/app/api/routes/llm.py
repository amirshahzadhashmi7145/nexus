from fastapi import APIRouter

from app.llm.providers import llm_ping, llm_status
from app.schemas_llm_status import LlmPingOut, LlmStatusOut

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/status", response_model=LlmStatusOut)
def get_llm_status() -> LlmStatusOut:
    return LlmStatusOut(**llm_status())


@router.get("/ping", response_model=LlmPingOut)
def get_llm_ping() -> LlmPingOut:
    """Reach the configured LLM (stub = local ok; vLLM/OpenAI = HTTP probe)."""
    return LlmPingOut(**llm_ping())
