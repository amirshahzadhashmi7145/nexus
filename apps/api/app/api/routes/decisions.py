from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas_decision import PriceDecisionIn, PriceDecisionOut
from app.schemas_llm import PolicyQuestionIn, PolicyQuestionOut
from app.services.orchestrator import analyze_price_decision
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


@router.post("/analyze-price-change", response_model=PriceDecisionOut)
def post_analyze_price_change(
    body: PriceDecisionIn,
    db: Session = Depends(get_db),
) -> PriceDecisionOut:
    try:
        return analyze_price_decision(db, body)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
