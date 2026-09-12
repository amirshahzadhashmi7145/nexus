"""Orchestrate RAG retrieval + structured LLM analysis."""

from __future__ import annotations

from app.llm.providers import LLMProvider, get_provider
from app.rag.retriever import retrieve
from app.schemas_llm import PolicyQuestionOut


def answer_policy_question(
    *,
    question: str,
    top_k: int = 4,
    provider_name: str | None = None,
    provider: LLMProvider | None = None,
) -> PolicyQuestionOut:
    hits = retrieve(question, top_k=top_k)
    context = "\n\n".join(f"[{h.source}] {h.text}" for h in hits)
    llm = provider or get_provider(provider_name)
    analysis = llm.analyze_policy(question=question, context=context or "No context retrieved.")
    return PolicyQuestionOut(
        question=question,
        provider=llm.name,
        analysis=analysis,
        retrieved_sources=sorted({h.source for h in hits}),
        context_used=context,
    )
