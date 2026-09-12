from pathlib import Path

from fastapi.testclient import TestClient

from app.llm.providers import StubProvider, get_provider
from app.rag.retriever import build_index
from app.services.policy_qa import answer_policy_question

DOCS = Path(__file__).resolve().parents[1] / "data" / "company"


def test_stub_provider_returns_policy_analysis_shape() -> None:
    provider = StubProvider()
    analysis = provider.analyze_policy(
        question="Can we promo with low coverage?",
        context="[inventory_policy.md] coverage below 14 days require manager approval for promotional campaigns.",
    )
    assert analysis.answer_summary
    assert analysis.findings
    assert analysis.evidence
    assert analysis.recommended_actions


def test_get_provider_defaults_to_stub() -> None:
    assert get_provider("stub").name == "stub"


def test_policy_qa_uses_rag_then_structured_output() -> None:
    build_index(DOCS)
    result = answer_policy_question(
        question="Do promotions need manager approval when inventory coverage is below 14 days?",
        top_k=3,
        provider_name="stub",
    )
    assert result.provider == "stub"
    assert result.analysis.findings
    assert result.retrieved_sources
    assert "14" in result.context_used or "14" in result.analysis.answer_summary


def test_policy_question_api(client: TestClient) -> None:
    build_index(DOCS)
    response = client.post(
        "/api/v1/decisions/policy-question",
        json={
            "question": "What approval is needed for promotions under 14 days coverage?",
            "top_k": 3,
            "provider": "stub",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "stub"
    assert "answer_summary" in body["analysis"]
    assert body["analysis"]["evidence"]
    assert body["retrieved_sources"]
