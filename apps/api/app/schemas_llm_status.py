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


class LlmPingOut(BaseModel):
    ok: bool
    provider: str
    method: str
    model: str | None = None
    models_seen: list[str] = Field(default_factory=list)
    model_listed: bool | None = None
    detail: str
    base_url: str | None = None
