from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    db,
    decisions,
    digital_twin,
    inventory,
    llm,
    orders,
    products,
    rag,
    simulations,
)
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Create any missing tables (decision_runs, audit_logs) without wiping data.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="NEXUS API", version="0.14.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(digital_twin.router, prefix="/api/v1")
app.include_router(simulations.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")
app.include_router(llm.router, prefix="/api/v1")
app.include_router(db.router, prefix="/api/v1")
app.include_router(decisions.router, prefix="/api/v1")
app.include_router(decisions.audit_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
