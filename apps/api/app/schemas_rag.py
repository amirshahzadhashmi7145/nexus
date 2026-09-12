from pydantic import BaseModel, Field


class RagHit(BaseModel):
    source: str
    chunk_id: str
    score: float
    text: str


class RagQueryIn(BaseModel):
    question: str = Field(min_length=3, examples=["Do promotions need approval under 14 days coverage?"])
    top_k: int = Field(default=3, ge=1, le=10)


class RagQueryOut(BaseModel):
    question: str
    hits: list[RagHit]
    context: str
    note: str = (
        "Retrieved policy context only (Phase 5). "
        "LLM answer generation comes in Phase 6."
    )


class RagDocumentsOut(BaseModel):
    documents: list[str]
    chunk_count: int
