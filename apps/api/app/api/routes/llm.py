from fastapi import APIRouter

from app.llm.providers import llm_status
from app.schemas_llm_status import LlmStatusOut

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/status", response_model=LlmStatusOut)
def get_llm_status() -> LlmStatusOut:
    return LlmStatusOut(**llm_status())
