from pydantic import BaseModel, Field


class DbStatusOut(BaseModel):
    dialect: str
    url: str
    env_database_url_set: bool
    nexus_db: str
    ok: bool
    error: str | None = None
    counts: dict[str, int | None] = Field(default_factory=dict)
