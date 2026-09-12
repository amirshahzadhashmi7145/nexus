from pathlib import Path

import pytest

from app.rag.embeddings import MiniLMEmbedder, TfidfEmbedder, get_embedder
from app.rag.retriever import build_index, rag_status, retrieve

DOCS = Path(__file__).resolve().parents[1] / "data" / "company"


def test_get_embedder_defaults_to_tfidf(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    assert get_embedder().name == "tfidf"


def test_tfidf_and_minilm_provider_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "tfidf")
    assert isinstance(get_embedder(), TfidfEmbedder)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "minilm")
    assert isinstance(get_embedder(), MiniLMEmbedder)


def test_build_index_reports_provider() -> None:
    index = build_index(DOCS, provider="tfidf")
    assert index.provider == "tfidf"
    assert index.vectors
    assert len(index.vectors[0]) > 10


def test_retrieve_with_explicit_tfidf() -> None:
    hits = retrieve(
        "promotions need manager approval when coverage below 14 days",
        top_k=3,
        docs_dir=DOCS,
        provider="tfidf",
    )
    assert hits
    assert hits[0].score > 0


def test_rag_status_endpoint_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "tfidf")
    build_index(DOCS, provider="tfidf")
    status = rag_status()
    assert status["provider"] == "tfidf"
    assert status["chunk_count"] > 0
    assert status["embedding_dim"] > 0
