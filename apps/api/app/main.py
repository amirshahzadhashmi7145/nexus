from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import decisions, digital_twin, inventory, orders, products, rag, simulations

app = FastAPI(title="NEXUS API", version="0.8.0")

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
app.include_router(decisions.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
