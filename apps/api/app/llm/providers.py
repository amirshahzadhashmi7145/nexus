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
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.schemas_llm import Evidence, PolicyAnalysis

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


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


def _parse_json_content(content: str) -> dict[str, Any]:
    """Parse model JSON, including fenced ```json blocks from some open models."""
    text = (content or "").strip()
    if not text:
        raise json.JSONDecodeError("empty content", text, 0)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = _JSON_FENCE.search(text)
    if match:
        parsed = json.loads(match.group(1).strip())
        if isinstance(parsed, dict):
            return parsed
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    raise json.JSONDecodeError("no JSON object found", text, 0)


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
        prefer_json_object: bool | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        # vLLM / some open models reject response_format; retry without it.
        if prefer_json_object is None:
            prefer_json_object = name != "vllm"
        self.prefer_json_object = prefer_json_object

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=self._headers(), json=payload)
                response.raise_for_status()
                return response.json()
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

    def analyze_policy(self, *, question: str, context: str) -> PolicyAnalysis:
        schema_hint = PolicyAnalysis.model_json_schema()
        system = (
            "You are NEXUS, a decision-intelligence assistant for NovaCart. "
            "Answer ONLY using the provided policy context. "
            "Return a single JSON object matching the given schema. "
            "If context is insufficient, say so in uncertainties. "
            "Do not wrap the JSON in markdown fences."
        )
        user = (
            f"Question:\n{question}\n\n"
            f"Policy context:\n{context}\n\n"
            f"JSON schema:\n{json.dumps(schema_hint)}"
        )
        base_payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
        }

        data: dict[str, Any]
        if self.prefer_json_object:
            try:
                data = self._chat({**base_payload, "response_format": {"type": "json_object"}})
            except RuntimeError as exc:
                # Many vLLM builds / smaller models reject response_format.
                if "response_format" in str(exc).lower() or "400" in str(exc):
                    data = self._chat(base_payload)
                else:
                    raise
        else:
            data = self._chat(base_payload)

        try:
            content = data["choices"][0]["message"]["content"]
            parsed = _parse_json_content(content if isinstance(content, str) else json.dumps(content))
            return PolicyAnalysis.model_validate(parsed)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"LLM provider '{self.name}' returned unusable JSON content"
            ) from exc

    def ping(self) -> dict[str, Any]:
        """Cheap connectivity check: list models, else tiny completion."""
        models_url = f"{self.base_url}/models"
        try:
            with httpx.Client(timeout=min(self.timeout, 20.0)) as client:
                response = client.get(models_url, headers=self._headers())
                if response.status_code == 200:
                    payload = response.json()
                    ids = [item.get("id") for item in payload.get("data", []) if isinstance(item, dict)]
                    return {
                        "ok": True,
                        "method": "models",
                        "model": self.model,
                        "models_seen": ids[:12],
                        "model_listed": self.model in ids if ids else None,
                        "detail": f"Reached {models_url}",
                    }
        except httpx.HTTPError:
            pass

        data = self._chat(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": "Reply with exactly: pong"}],
                "max_tokens": 8,
                "temperature": 0,
            }
        )
        content = data["choices"][0]["message"]["content"]
        return {
            "ok": True,
            "method": "chat",
            "model": self.model,
            "models_seen": [],
            "model_listed": None,
            "detail": f"chat ok: {str(content)[:80]}",
        }


def get_provider(name: str | None = None) -> LLMProvider:
    """Resolve provider from explicit name or LLM_PROVIDER (default stub)."""
    chosen = (name or os.getenv("LLM_PROVIDER", "stub")).strip().lower()
    if chosen in {"stub", "heuristic", "local"}:
        return StubProvider()

    if chosen in {"openai_compatible", "openai", "vllm"}:
        default_base = (
            "http://127.0.0.1:8001/v1"
            if chosen == "vllm"
            else "https://api.openai.com/v1"
        )
        default_model = (
            "meta-llama/Llama-3.1-8B-Instruct"
            if chosen == "vllm"
            else "gpt-4o-mini"
        )
        base_url = os.getenv("LLM_BASE_URL", default_base).rstrip("/")
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model = os.getenv("LLM_MODEL", default_model).strip()
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
    default_base = (
        "http://127.0.0.1:8001/v1"
        if env_provider.strip().lower() == "vllm"
        else "https://api.openai.com/v1"
    )
    base_url = os.getenv("LLM_BASE_URL", default_base)
    default_model = (
        "meta-llama/Llama-3.1-8B-Instruct"
        if env_provider.strip().lower() == "vllm"
        else "gpt-4o-mini"
    )
    model_env = os.getenv("LLM_MODEL", default_model)
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
            else "Stub uses retrieved policy text heuristics; set LLM_PROVIDER=vllm or openai_compatible for live models."
        ),
    }


def llm_ping() -> dict[str, Any]:
    """Actively probe the configured LLM (models list or tiny chat)."""
    provider = get_provider()
    status = llm_status()
    if isinstance(provider, StubProvider):
        return {
            "ok": True,
            "provider": "stub",
            "method": "local",
            "model": None,
            "models_seen": [],
            "model_listed": None,
            "detail": "Stub provider is local; no network call.",
            "base_url": status.get("base_url"),
        }
    if not isinstance(provider, OpenAICompatibleProvider):
        return {
            "ok": False,
            "provider": provider.name,
            "method": "unsupported",
            "model": provider.model,
            "models_seen": [],
            "model_listed": None,
            "detail": f"Ping not implemented for {provider.name}",
            "base_url": status.get("base_url"),
        }
    try:
        result = provider.ping()
        return {
            **result,
            "provider": provider.name,
            "base_url": status.get("base_url"),
        }
    except RuntimeError as exc:
        return {
            "ok": False,
            "provider": provider.name,
            "method": "error",
            "model": provider.model,
            "models_seen": [],
            "model_listed": None,
            "detail": str(exc),
            "base_url": status.get("base_url"),
        }
