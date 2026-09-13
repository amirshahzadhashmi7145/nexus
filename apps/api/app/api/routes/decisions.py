import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import DecisionRun
from app.schemas_approval import (
    ApprovalIn,
    AuditEventOut,
    AuditListOut,
    DecisionListOut,
    DecisionRecordOut,
)
from app.schemas_decision import PriceDecisionIn, PriceDecisionOut
from app.schemas_llm import PolicyQuestionIn, PolicyQuestionOut
from app.services.approvals import (
    get_decision,
    list_audit,
    list_decisions,
    resolve_decision,
    save_price_decision,
)
from app.services.orchestrator import analyze_price_decision
from app.services.policy_qa import answer_policy_question

router = APIRouter(prefix="/decisions", tags=["decisions"])


def _to_record(row: DecisionRun) -> DecisionRecordOut:
    return DecisionRecordOut(
        decision_id=row.decision_id,
        kind=row.kind,
        sku=row.sku,
        status=row.status,
        recommendation=row.recommendation,
        system_approve=row.system_approve,
        created_at=row.created_at,
        decided_at=row.decided_at,
        decided_by=row.decided_by,
        decision_note=row.decision_note,
        payload=json.loads(row.payload_json),
    )


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
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/analyze-price-change", response_model=PriceDecisionOut)
def post_analyze_price_change(
    body: PriceDecisionIn,
    db: Session = Depends(get_db),
) -> PriceDecisionOut:
    try:
        result = analyze_price_decision(db, body)
        save_price_decision(db, result)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("", response_model=DecisionListOut)
def get_decisions(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DecisionListOut:
    rows = list_decisions(db, limit=limit)
    items = [_to_record(row) for row in rows]
    return DecisionListOut(items=items, count=len(items))


@router.get("/{decision_id}", response_model=DecisionRecordOut)
def get_decision_record(decision_id: str, db: Session = Depends(get_db)) -> DecisionRecordOut:
    row = get_decision(db, decision_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Decision not found: {decision_id}")
    return _to_record(row)


@router.post("/{decision_id}/approve", response_model=DecisionRecordOut)
def post_approve(
    decision_id: str,
    body: ApprovalIn,
    db: Session = Depends(get_db),
) -> DecisionRecordOut:
    try:
        row = resolve_decision(
            db, decision_id=decision_id, approve=True, actor=body.actor, note=body.note
        )
    except ValueError as exc:
        msg = str(exc)
        status = 404 if "not found" in msg.lower() else 409
        raise HTTPException(status_code=status, detail=msg) from exc
    return _to_record(row)


@router.post("/{decision_id}/reject", response_model=DecisionRecordOut)
def post_reject(
    decision_id: str,
    body: ApprovalIn,
    db: Session = Depends(get_db),
) -> DecisionRecordOut:
    try:
        row = resolve_decision(
            db, decision_id=decision_id, approve=False, actor=body.actor, note=body.note
        )
    except ValueError as exc:
        msg = str(exc)
        status = 404 if "not found" in msg.lower() else 409
        raise HTTPException(status_code=status, detail=msg) from exc
    return _to_record(row)


audit_router = APIRouter(prefix="/audit", tags=["audit"])


@audit_router.get("", response_model=AuditListOut)
def get_audit_log(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> AuditListOut:
    rows = list_audit(db, limit=limit)
    items = [
        AuditEventOut(
            id=row.id,
            created_at=row.created_at,
            actor=row.actor,
            action=row.action,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            detail=row.detail,
        )
        for row in rows
    ]
    return AuditListOut(items=items, count=len(items))
