"""Persist decisions and append-only audit events.

Mentor:
- Analyze = recommend. Approve = human gate. Audit = proof for judges/regulators.
- Postgres/SQLite remains source of truth; we do not 'act' on inventory until approved
  (and even then Phase 10 only records the approval — safe for the twin demo).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, DecisionRun
from app.schemas_decision import PriceDecisionOut


def write_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    detail: str | None = None,
) -> AuditLog:
    row = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(row)
    db.flush()
    return row


def save_price_decision(db: Session, result: PriceDecisionOut) -> DecisionRun:
    payload = result.model_dump(mode="json")
    row = DecisionRun(
        decision_id=result.decision_id,
        kind="price_change",
        sku=result.simulation.sku,
        status="pending",
        recommendation=result.recommendation,
        system_approve=result.approve,
        payload_json=json.dumps(payload),
    )
    db.add(row)
    write_audit(
        db,
        actor="system",
        action="decision.created",
        entity_type="decision_run",
        entity_id=result.decision_id,
        detail=result.recommendation[:500],
    )
    db.commit()
    db.refresh(row)
    return row


def get_decision(db: Session, decision_id: str) -> DecisionRun | None:
    return db.scalar(select(DecisionRun).where(DecisionRun.decision_id == decision_id))


def list_decisions(db: Session, *, limit: int = 20) -> list[DecisionRun]:
    stmt = select(DecisionRun).order_by(DecisionRun.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))


def resolve_decision(
    db: Session,
    *,
    decision_id: str,
    approve: bool,
    actor: str,
    note: str | None = None,
) -> DecisionRun:
    row = get_decision(db, decision_id)
    if row is None:
        raise ValueError(f"Decision not found: {decision_id}")
    if row.status != "pending":
        raise ValueError(f"Decision already {row.status}")

    row.status = "approved" if approve else "rejected"
    row.decided_at = datetime.now(UTC).replace(tzinfo=None)
    row.decided_by = actor
    row.decision_note = note
    write_audit(
        db,
        actor=actor,
        action="decision.approved" if approve else "decision.rejected",
        entity_type="decision_run",
        entity_id=decision_id,
        detail=note,
    )
    db.commit()
    db.refresh(row)
    return row


def list_audit(db: Session, *, limit: int = 50) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))
