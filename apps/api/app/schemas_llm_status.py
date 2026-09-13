from pydantic import BaseModel, Field


class LlmStatusOut(BaseModel):
    provider: str
    model: str | None = None
    env_provider: str
    base_url: str | None = None
    model_env: str
    api_key_configured: bool
    fallback_to_stub: bool
    note: str
