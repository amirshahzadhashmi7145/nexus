"""LLM provider abstraction.

Learn:
- App code talks to a Provider interface, not to one vendor SDK.
- Default for local/dev/tests: StubProvider (no API key, deterministic).
- Optional: OpenAI-compatible HTTP API (OpenAI, vLLM, Azure, etc.) via env vars.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.schemas_llm import Evidence, PolicyAnalysis


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def analyze_policy(self, *, question: str, context: str) -> PolicyAnalysis:
        raise NotImplementedError


class StubProvider(LLMProvider):
    """Heuristic structured answer from retrieved context (no external LLM)."""

    name = "stub"

    def analyze_policy(self, *, question: str, context: str) -> PolicyAnalysis:
        snippets = [s.strip() for s in context.split("\n\n") if s.strip()]
        evidence: list[Evidence] = []
        findings: list[str] = []

        for snippet in snippets[:4]:
            source = "unknown"
            text = snippet
            if snippet.startswith("[") and "]" in snippet:
                source = snippet[1 : snippet.index("]")]
                text = snippet[snippet.index("]") + 1 :].strip()
            claim = text[:180] + ("…" if len(text) > 180 else "")
            evidence.append(Evidence(source=source, claim=claim, confidence=0.7))
            findings.append(claim)

        q = question.lower()
        if "14" in context and ("promo" in q or "coverage" in q or "approv" in q):
            findings.insert(
                0,
                "Retrieved policies require manager approval for promotions when coverage is below 14 days.",
            )
            actions = [
                "Check current inventory coverage for the SKU",
                "Request manager approval before launching the promo",
                "Optionally run a price/stockout simulation",
            ]
        else:
            actions = [
                "Validate claims against the cited policy sources",
                "Confirm with Finance/Operations if approval thresholds apply",
            ]

        if not findings:
            findings = ["No strongly matching policy chunks were retrieved."]
            actions = ["Add or refine company documents, then re-query."]

        return PolicyAnalysis(
            answer_summary=(
                findings[0]
                if findings
                else "Insufficient policy context to answer confidently."
            ),
            findings=findings[:5],
            evidence=evidence or [
                Evidence(source="none", claim="No context retrieved", confidence=0.2)
            ],
            assumptions=[
                "Retrieved chunks are complete enough for this question",
                "Stub provider approximates an LLM using retrieval only",
            ],
            uncertainties=[
                "No neural LLM was called; wording is heuristic",
                "Numeric coverage for a live SKU was not computed in this step",
            ],
            recommended_actions=actions,
        )


class OpenAICompatibleProvider(LLMProvider):
    """Calls an OpenAI-compatible chat completions endpoint with JSON object response."""

    name = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def analyze_policy(self, *, question: str, context: str) -> PolicyAnalysis:
        schema_hint = PolicyAnalysis.model_json_schema()
        system = (
            "You are NEXUS, a decision-intelligence assistant for NovaCart. "
            "Answer ONLY using the provided policy context. "
            "Return a single JSON object matching the given schema. "
            "If context is insufficient, say so in uncertainties."
        )
        user = (
            f"Question:\n{question}\n\n"
            f"Policy context:\n{context}\n\n"
            f"JSON schema:\n{json.dumps(schema_hint)}"
        )
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return PolicyAnalysis.model_validate(parsed)


def get_provider(name: str | None = None) -> LLMProvider:
    chosen = (name or os.getenv("LLM_PROVIDER", "stub")).strip().lower()
    if chosen in {"stub", "heuristic", "local"}:
        return StubProvider()
    if chosen in {"openai_compatible", "openai", "vllm"}:
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        api_key = os.getenv("LLM_API_KEY", "")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        if not api_key and "api.openai.com" in base_url:
            # Fall back so local demos never crash without keys.
            return StubProvider()
        return OpenAICompatibleProvider(base_url=base_url, api_key=api_key or "EMPTY", model=model)
    raise ValueError(f"Unknown LLM provider: {chosen}")
