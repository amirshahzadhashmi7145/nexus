from datetime import datetime

from pydantic import BaseModel, Field


class ApprovalIn(BaseModel):
    actor: str = Field(default="human", min_length=1, examples=["amir"])
    note: str | None = Field(default=None, examples=["Approved after reviewing stockout risk."])


class DecisionRecordOut(BaseModel):
    decision_id: str
    kind: str
    sku: str | None
    status: str
    recommendation: str
    system_approve: bool
    created_at: datetime
    decided_at: datetime | None
    decided_by: str | None
    decision_note: str | None
    payload: dict


class AuditEventOut(BaseModel):
    id: int
    created_at: datetime
    actor: str
    action: str
    entity_type: str
    entity_id: str
    detail: str | None


class AuditListOut(BaseModel):
    items: list[AuditEventOut]
    count: int


class DecisionListOut(BaseModel):
    items: list[DecisionRecordOut]
    count: int
