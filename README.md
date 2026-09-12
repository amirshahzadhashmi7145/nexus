# NEXUS

AI digital-twin and decision-intelligence platform for organizations.

> Simulate decisions. Discover better strategies. Act with confidence.

Built for the **lablab.ai × AMD** hackathon.

## MVP

NovaCart — a fictional e-commerce digital twin. Ask strategic questions, simulate futures, compare strategies, and approve safe actions with full traces.

## Stack

- **Backend:** Python, FastAPI, PostgreSQL, Redis
- **Frontend:** Next.js / React / TypeScript
- **AI:** LLM abstraction, RAG, multi-agent orchestration, MCP
- **Simulation:** demand, inventory, pricing, financial models
- **Infra:** Docker Compose; AMD ROCm / optional vLLM later (CPU-first)

## Docs

Product docs live locally in `nexus-docs/` (gitignored). Company policies used by RAG are in `apps/api/data/company/`.

## Local setup (Phase 0)

```bash
# venv (uv; system python3-venv may be missing)
uv venv .venv
source .venv/bin/activate
uv pip install -r apps/api/requirements.txt

# API
cd apps/api && uvicorn app.main:app --reload

# Tests
cd apps/api && PYTHONPATH=. pytest -q

# Seed NovaCart (sqlite file by default)
cd apps/api && PYTHONPATH=. python -m app.cli generate-data --seed 42

# API (serves seeded sqlite by default)
cd apps/api && uvicorn app.main:app --reload
# then open http://127.0.0.1:8000/docs

# RAG: query NovaCart policies
# POST /api/v1/rag/query  {"question": "...", "top_k": 3}

# Structured policy answer (RAG + LLM provider; default stub)
# POST /api/v1/decisions/policy-question

# Full pricing decision (manager + research + ops + sim + critic)
# POST /api/v1/decisions/analyze-price-change

# Web dashboard (API must be running)
cd apps/web && cp -n .env.example .env.local && npm run dev
# open http://127.0.0.1:3000

# MCP server (for Cursor / other hosts) — see mcp.json.example
# cd apps/api && PYTHONPATH=. python -m app.mcp_server

# Human approval + audit
# POST /api/v1/decisions/{id}/approve
# GET  /api/v1/audit

# Infra skeleton (Postgres/Redis when you are ready)
docker compose up -d
```

## Status

Phase 10 — approval + audit on `phase-10-approval-audit`.
