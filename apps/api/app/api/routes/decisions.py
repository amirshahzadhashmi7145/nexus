from fastapi import APIRouter, HTTPException

from app.schemas_llm import PolicyQuestionIn, PolicyQuestionOut
from app.services.policy_qa import answer_policy_question

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("/policy-question", response_model=PolicyQuestionOut)
def post_policy_question(body: PolicyQuestionIn) -> PolicyQuestionOut:
    try:
        return answer_policy_question(
            question=body.question,
            top_k=body.top_k,
            provider_name=body.provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
