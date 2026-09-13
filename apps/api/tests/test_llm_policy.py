from pathlib import Path

from fastapi.testclient import TestClient

from app.llm.providers import (
    OpenAICompatibleProvider,
    StubProvider,
    _parse_json_content,
    get_provider,
    llm_ping,
    llm_status,
)
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


def test_openai_compatible_selected_with_key(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    provider = get_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.name == "openai_compatible"
    assert provider.model == "gpt-4o-mini"


def test_openai_without_key_falls_back_to_stub(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    assert get_provider().name == "stub"


def test_vllm_provider_name(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "vllm")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:8001/v1")
    monkeypatch.setenv("LLM_API_KEY", "EMPTY")
    monkeypatch.setenv("LLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    provider = get_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.name == "vllm"
    assert provider.prefer_json_object is False


def test_vllm_defaults_base_url(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "vllm")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "EMPTY")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    provider = get_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.base_url == "http://127.0.0.1:8001/v1"
    assert "Llama" in (provider.model or "")


def test_parse_json_content_fenced() -> None:
    raw = (
        'Here you go:\n```json\n{"answer_summary": "ok", "findings": [], '
        '"evidence": [], "assumptions": [], "uncertainties": [], '
        '"recommended_actions": []}\n```'
    )
    parsed = _parse_json_content(raw)
    assert parsed["answer_summary"] == "ok"


def test_llm_status_reports_stub(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    status = llm_status()
    assert status["provider"] == "stub"
    assert status["fallback_to_stub"] is False
    assert status["api_key_configured"] is False or isinstance(
        status["api_key_configured"], bool
    )


def test_llm_ping_stub(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    result = llm_ping()
    assert result["ok"] is True
    assert result["provider"] == "stub"
    assert result["method"] == "local"


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


def test_llm_status_api(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    response = client.get("/api/v1/llm/status")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "stub"
    assert body["env_provider"] == "stub"
    assert "note" in body


def test_llm_ping_api(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    response = client.get("/api/v1/llm/ping")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["provider"] == "stub"
