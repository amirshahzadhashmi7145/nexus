"""Multi-agent style decision orchestration schemas.

Learn: each 'agent' is a responsibility with a typed result — not a separate
chatbot. The manager sequences them and produces one recommendation.
"""

from pydantic import BaseModel, Field

from app.schemas_llm import PolicyAnalysis
from app.schemas_simulation import PriceSimulationOut
from app.schemas_twin import DigitalTwinOut


class AgentStep(BaseModel):
    agent: str
    role: str
    status: str = "completed"
    summary: str


class PriceDecisionIn(BaseModel):
    sku: str = Field(examples=["P-0001"])
    price_change_pct: float = Field(examples=[-10.0])
    simulations: int = Field(default=100, ge=10, le=2000)
    horizon_days: int = Field(default=30, ge=1, le=365)
    seed: int = Field(default=42)
    top_k_policies: int = Field(default=4, ge=1, le=10)
    provider: str | None = Field(
        default=None,
        description="Optional LLM override: stub | openai_compatible | vllm. Default from LLM_PROVIDER.",
    )


class PriceDecisionOut(BaseModel):
    decision_id: str
    question: str
    plan: list[str]
    agent_trace: list[AgentStep]
    digital_twin: DigitalTwinOut
    policy: PolicyAnalysis
    simulation: PriceSimulationOut
    recommendation: str
    approve: bool
    risks: list[str]
    next_actions: list[str]
