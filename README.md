# NEXUS

AI digital-twin and decision-intelligence platform for organizations.

> Simulate decisions. Discover better strategies. Act with confidence.

Built for the **lablab.ai × AMD** hackathon.

## MVP

NovaCart — a fictional e-commerce digital twin. Ask strategic questions, simulate futures, compare strategies, and approve safe actions with full traces.

## 60-second demo (judges)

With API + web running:

1. Open **http://127.0.0.1:3000** — twin snapshot from the business DB  
2. Click **Run the 60-second demo** → **One-click demo (P-0001 −10%)**  
3. Watch agent trace (RAG + Monte Carlo + critic) → **Human approve** → audit log appears  

Stub LLM answers are fine for CPU demos. For **live** generation on your laptop (no GPU download):

```bash
export LLM_PROVIDER=openai_compatible
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini
# restart uvicorn, then GET /api/v1/llm/status  → provider should be openai_compatible
```

Same knobs work for Groq/Together/etc. (OpenAI-compatible base URL). Later: `LLM_PROVIDER=vllm` + AMD GPU. RAG embeddings stay separate (`EMBEDDING_PROVIDER`).

## Stack

- **Backend:** Python, FastAPI, PostgreSQL, Redis
- **Frontend:** Next.js / React / TypeScript
- **AI:** LLM abstraction, RAG, multi-agent orchestration, MCP
- **Simulation:** demand, inventory, pricing, financial models
- **Infra:** Docker Compose; AMD ROCm / optional vLLM later (CPU-first)

## Docs

Product docs live locally in `nexus-docs/` (gitignored). Company policies used by RAG are in `apps/api/data/company/`.

## Local setup

```bash
# venv (uv; system python3-venv may be missing)
uv venv .venv
source .venv/bin/activate
uv pip install -r apps/api/requirements.txt

# --- Preferred: Postgres (business source of truth) ---
docker compose up -d postgres
cp -n .env.example .env   # DATABASE_URL already points at local Postgres
cd apps/api && PYTHONPATH=. python -m app.cli generate-data --seed 42
# GET /api/v1/db/status → dialect=postgresql, ok=true

# --- Fallback: SQLite (no Docker) ---
# unset DATABASE_URL; leave NEXUS_DB unset (or NEXUS_DB=sqlite)
# cd apps/api && PYTHONPATH=. python -m app.cli generate-data --seed 42

# API
cd apps/api && uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs

# Web dashboard (second terminal)
cd apps/web && cp -n .env.example .env.local && npm run dev
# http://127.0.0.1:3000

# Tests (always use in-memory SQLite)
cd apps/api && PYTHONPATH=. pytest -q

# Status helpers
# GET  /api/v1/db/status
# GET  /api/v1/llm/status
# GET  /api/v1/rag/status
# POST /api/v1/rag/query
# POST /api/v1/decisions/policy-question
# POST /api/v1/decisions/analyze-price-change
# GET  /api/v1/audit

# MCP server (for Cursor / other hosts) — see mcp.json.example
# cd apps/api && PYTHONPATH=. python -m app.mcp_server

# Optional neural embeddings
# EMBEDDING_PROVIDER=minilm
# uv pip install -r apps/api/requirements-embeddings.txt

# Full infra (Postgres + Redis)
docker compose up -d
```

## Status

Phase 14 — Postgres-first business DB on `phase-14-postgres` (`NEXUS_DB` / `DATABASE_URL`, `GET /api/v1/db/status`; SQLite still the zero-setup fallback).
