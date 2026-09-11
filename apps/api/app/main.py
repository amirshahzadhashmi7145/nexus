from fastapi import FastAPI

from app.api.routes import digital_twin, inventory, orders, products

app = FastAPI(title="NEXUS API", version="0.3.0")

app.include_router(products.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(digital_twin.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
