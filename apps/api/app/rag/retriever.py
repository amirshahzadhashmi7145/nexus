"""In-memory vector store + retriever.

Postgres remains source of truth for business facts.
This store only holds document chunks for knowledge retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.rag.chunking import Chunk, chunk_documents, load_markdown_documents
from app.rag.embeddings import TfidfModel, cosine_similarity, fit_tfidf


DEFAULT_DOCS_DIR = Path(__file__).resolve().parents[2] / "data" / "company"


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    source: str
    text: str
    score: float


@dataclass
class VectorIndex:
    chunks: list[Chunk]
    vectors: list[list[float]]
    model: TfidfModel

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievedChunk]:
        q = self.model.embed(query)
        scored = [
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                source=chunk.source,
                text=chunk.text,
                score=cosine_similarity(q, vec),
            )
            for chunk, vec in zip(self.chunks, self.vectors, strict=True)
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return [item for item in scored[:top_k] if item.score > 0]


_INDEX: VectorIndex | None = None


def build_index(docs_dir: Path | None = None) -> VectorIndex:
    directory = docs_dir or DEFAULT_DOCS_DIR
    docs = load_markdown_documents(directory)
    chunks = chunk_documents(docs)
    model = fit_tfidf([c.text for c in chunks] or [""])
    vectors = [model.embed(c.text) for c in chunks]
    return VectorIndex(chunks=chunks, vectors=vectors, model=model)


def get_index(*, refresh: bool = False, docs_dir: Path | None = None) -> VectorIndex:
    global _INDEX
    if _INDEX is None or refresh or docs_dir is not None:
        _INDEX = build_index(docs_dir)
    return _INDEX


def retrieve(question: str, *, top_k: int = 3, docs_dir: Path | None = None) -> list[RetrievedChunk]:
    index = get_index(docs_dir=docs_dir) if docs_dir else get_index()
    return index.search(question, top_k=top_k)


def list_sources(docs_dir: Path | None = None) -> list[str]:
    directory = docs_dir or DEFAULT_DOCS_DIR
    return sorted(path.name for path in directory.glob("*.md"))
