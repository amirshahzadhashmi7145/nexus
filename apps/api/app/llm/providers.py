"""LLM provider abstraction.

Learn:
- App code talks to a Provider interface, not to one vendor SDK.
- Default for local/dev/tests: StubProvider (no API key, deterministic).
- Optional: OpenAI-compatible HTTP API (OpenAI, Groq, Together, vLLM, …) via env.
- FINAL hackathon target: LLM_PROVIDER=vllm → same HTTP shape, AMD GPU server.
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
    model: str | None = None

    @abstractmethod
    def analyze_policy(self, *, question: str, context: str) -> PolicyAnalysis:
        raise NotImplementedError


class StubProvider(LLMProvider):
    """Heuristic structured answer from retrieved context (no external LLM)."""

    name = "stub"
    model = None

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

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        name: str = "openai_compatible",
        timeout: float = 60.0,
    ) -> None:
        self.name = name
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
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise RuntimeError(
                f"LLM provider '{self.name}' HTTP {exc.response.status_code} "
                f"at {url}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"LLM provider '{self.name}' request failed at {url}: {exc}"
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return PolicyAnalysis.model_validate(parsed)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"LLM provider '{self.name}' returned unusable JSON content"
            ) from exc


def get_provider(name: str | None = None) -> LLMProvider:
    """Resolve provider from explicit name or LLM_PROVIDER (default stub)."""
    chosen = (name or os.getenv("LLM_PROVIDER", "stub")).strip().lower()
    if chosen in {"stub", "heuristic", "local"}:
        return StubProvider()

    if chosen in {"openai_compatible", "openai", "vllm"}:
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
        display = "vllm" if chosen == "vllm" else "openai_compatible"

        # OpenAI cloud needs a real key; without one, keep demos working via stub.
        if not api_key and "api.openai.com" in base_url:
            return StubProvider()

        return OpenAICompatibleProvider(
            base_url=base_url,
            api_key=api_key or "EMPTY",
            model=model,
            name=display,
        )

    raise ValueError(f"Unknown LLM provider: {chosen}")


def llm_status() -> dict[str, Any]:
    """Inspect which generation backend the API will use (does not call the model)."""
    env_provider = os.getenv("LLM_PROVIDER", "stub")
    provider = get_provider()
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model_env = os.getenv("LLM_MODEL", "gpt-4o-mini")
    has_key = bool(os.getenv("LLM_API_KEY", "").strip())
    fallback = provider.name == "stub" and env_provider.strip().lower() not in {
        "stub",
        "heuristic",
        "local",
        "",
    }
    return {
        "provider": provider.name,
        "model": provider.model,
        "env_provider": env_provider,
        "base_url": None if provider.name == "stub" else base_url.rstrip("/"),
        "model_env": model_env,
        "api_key_configured": has_key,
        "fallback_to_stub": fallback,
        "note": (
            "Generation only — RAG embeddings are separate (EMBEDDING_PROVIDER)."
            if provider.name != "stub"
            else "Stub uses retrieved policy text heuristics; set LLM_PROVIDER + key for live models."
        ),
    }
