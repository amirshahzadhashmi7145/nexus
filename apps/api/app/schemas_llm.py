"""Structured decision / policy analysis schemas (LLM outputs).

Learn: we never trust free-form chat as the API contract. The model must fill
a Pydantic shape so agents and the UI can use findings, evidence, and risks.
"""

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source: str = Field(description="Document or system that supports the claim")
    claim: str
    confidence: float = Field(ge=0.0, le=1.0)


class PolicyAnalysis(BaseModel):
    answer_summary: str
    findings: list[str]
    evidence: list[Evidence]
    assumptions: list[str]
    uncertainties: list[str]
    recommended_actions: list[str]


class PolicyQuestionIn(BaseModel):
    question: str = Field(min_length=5, examples=["Can we run a promo if coverage is under 14 days?"])
    top_k: int = Field(default=4, ge=1, le=10)
    provider: str | None = Field(
        default=None,
        description="Optional override: stub | openai_compatible. Default from LLM_PROVIDER env.",
    )


class PolicyQuestionOut(BaseModel):
    question: str
    provider: str
    analysis: PolicyAnalysis
    retrieved_sources: list[str]
    context_used: str
