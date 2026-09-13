# AMD Developer Cloud + vLLM (NEXUS Phase 15)

NEXUS already talks **OpenAI-compatible** HTTP. vLLM on AMD is the same socket as
OpenAI — change env vars, do not rewrite the app.

```
Your laptop (API + UI + Postgres + RAG)
        │  LLM_BASE_URL
        ▼
AMD GPU box running vLLM  →  /v1/chat/completions
```

## Before you spend credit

1. Demo works on **stub** or **openai_compatible** locally.
2. `GET /api/v1/db/status` is healthy.
3. You have AMD Developer Cloud access / coupon ready.

## On the AMD instance (high level)

1. Start a GPU VM (Instinct / ROCm image when available).
2. Run **vLLM** with an open model that fits the GPU, e.g. Llama 3.1 8B Instruct.
3. Expose the OpenAI-compatible API (often port `8000` or `8001`).
4. Note the public/SSH-forward URL, e.g. `http://<host>:8001/v1`.

Exact Docker/ROCm commands change with AMD’s images — follow their current
[ROCm vLLM docs](https://rocm.docs.amd.com/). Keep `LLM_MODEL` equal to the
model id vLLM loaded.

Example shape (illustrative — adjust for your AMI/image):

```bash
# On the AMD VM (example only)
vllm serve meta-llama/Llama-3.1-8B-Instruct --host 0.0.0.0 --port 8001
```

SSH tunnel from your laptop if the port is not public:

```bash
ssh -L 8001:127.0.0.1:8001 user@amd-vm-host
```

## Point NEXUS at vLLM (laptop)

In repo-root `.env` (or export in the uvicorn shell):

```bash
LLM_PROVIDER=vllm
LLM_BASE_URL=http://127.0.0.1:8001/v1
LLM_API_KEY=EMPTY
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

Restart uvicorn, then:

| Check | Expect |
|---|---|
| `GET /api/v1/llm/status` | `provider: "vllm"` |
| `GET /api/v1/llm/ping` | `ok: true` (models list or tiny chat) |
| Decide UI one-click demo | research step shows `(vllm)` |

CLI:

```bash
cd apps/api && PYTHONPATH=. python -m app.cli llm-ping
```

## Notes

- **RAG embeddings stay local** (`EMBEDDING_PROVIDER=tfidf|minilm`). vLLM is generation only.
- vLLM often lacks OpenAI `response_format=json_object`; NEXUS retries without it and parses JSON (including fenced blocks).
- Prefer a **small** first model (8B-class) to save credit and VRAM.
- Stop the AMD VM when idle — credits burn while the box is up.

## Rollback

```bash
LLM_PROVIDER=stub
# or openai_compatible + your API key
```

Restart uvicorn.
