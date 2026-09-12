from pathlib import Path

from fastapi.testclient import TestClient

from app.rag.chunking import chunk_text, load_markdown_documents
from app.rag.retriever import build_index, retrieve

DOCS = Path(__file__).resolve().parents[1] / "data" / "company"


def test_company_docs_exist() -> None:
    docs = load_markdown_documents(DOCS)
    names = {name for name, _ in docs}
    assert "pricing_policy.md" in names
    assert "inventory_policy.md" in names
    assert len(docs) >= 5


def test_chunking_creates_overlapping_pieces() -> None:
    chunks = chunk_text("policy.md", "word " * 200, size=100, overlap=20)
    assert len(chunks) >= 2
    assert chunks[0].source == "policy.md"


def test_retriever_finds_coverage_rule() -> None:
    hits = retrieve(
        "Do promotions need manager approval when inventory coverage is below 14 days?",
        top_k=3,
        docs_dir=DOCS,
    )
    assert hits
    blob = " ".join(h.text.lower() for h in hits)
    assert "14" in blob
    assert hits[0].score > 0


def test_rag_api_query(client: TestClient) -> None:
    # Force index from package docs for API process
    build_index(DOCS)
    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What approval is needed for a 10% price cut?", "top_k": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["hits"]
    assert "Phase 5" in body["note"]
    assert body["context"]


def test_rag_documents_endpoint(client: TestClient) -> None:
    build_index(DOCS)
    response = client.get("/api/v1/rag/documents")
    assert response.status_code == 200
    body = response.json()
    assert body["chunk_count"] > 0
    assert any("pricing" in name for name in body["documents"])
