from fastapi import FastAPI

from app.api.routes import inventory, orders, products

app = FastAPI(title="NEXUS API", version="0.2.0")

app.include_router(products.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
