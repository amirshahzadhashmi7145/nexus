"""In-memory vector store + retriever.

Postgres remains source of truth for business facts.
This store only holds document chunks for knowledge retrieval.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.rag.chunking import Chunk, chunk_documents, load_markdown_documents
from app.rag.embeddings import Embedder, cosine_similarity, get_embedder


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
    embedder: Embedder
    provider: str

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievedChunk]:
        q = self.embedder.embed(query)
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
        return [item for item in scored[:top_k] if item.score > 0.05]


_INDEX: VectorIndex | None = None


def build_index(
    docs_dir: Path | None = None,
    *,
    provider: str | None = None,
) -> VectorIndex:
    directory = docs_dir or DEFAULT_DOCS_DIR
    docs = load_markdown_documents(directory)
    chunks = chunk_documents(docs)
    embedder = get_embedder(provider)
    corpus = [c.text for c in chunks] or [""]
    embedder.fit(corpus)
    vectors = [embedder.embed(c.text) for c in chunks]
    return VectorIndex(
        chunks=chunks,
        vectors=vectors,
        embedder=embedder,
        provider=embedder.name,
    )


def get_index(
    *,
    refresh: bool = False,
    docs_dir: Path | None = None,
    provider: str | None = None,
) -> VectorIndex:
    global _INDEX
    wanted = get_embedder(provider).name
    if _INDEX is None or refresh or docs_dir is not None or _INDEX.provider != wanted:
        _INDEX = build_index(docs_dir, provider=provider)
    return _INDEX


def retrieve(
    question: str,
    *,
    top_k: int = 3,
    docs_dir: Path | None = None,
    provider: str | None = None,
) -> list[RetrievedChunk]:
    index = get_index(
        docs_dir=docs_dir,
        provider=provider,
        refresh=docs_dir is not None or provider is not None,
    )
    return index.search(question, top_k=top_k)


def list_sources(docs_dir: Path | None = None) -> list[str]:
    directory = docs_dir or DEFAULT_DOCS_DIR
    return sorted(path.name for path in directory.glob("*.md"))


def rag_status() -> dict[str, Any]:
    index = get_index()
    return {
        "provider": index.provider,
        "chunk_count": len(index.chunks),
        "embedding_dim": len(index.vectors[0]) if index.vectors else 0,
        "documents": list_sources(),
        "env_provider": os.getenv("EMBEDDING_PROVIDER", "tfidf"),
    }
