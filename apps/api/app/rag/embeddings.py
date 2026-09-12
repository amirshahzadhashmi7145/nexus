"""Embedding providers for RAG.

Mentor:
- An embedding turns text into a list of numbers so similar meaning ≈ nearby vectors.
- TF-IDF: fast, no download, word-overlap only (Phase 5 learning default).
- MiniLM: neural semantic similarity (optional; needs sentence-transformers).

Swap with EMBEDDING_PROVIDER=tfidf|minilm — retriever API stays the same.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Protocol


_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True))


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


class Embedder(Protocol):
    name: str

    def fit(self, corpus: list[str]) -> None: ...

    def embed(self, text: str) -> list[float]: ...


@dataclass
class TfidfEmbedder:
    name: str = "tfidf"
    vocabulary: dict[str, int] = field(default_factory=dict)
    idf: list[float] = field(default_factory=list)

    def fit(self, corpus: list[str]) -> None:
        docs_tokens = [tokenize(doc) for doc in corpus]
        vocab_tokens = sorted({tok for tokens in docs_tokens for tok in tokens})
        self.vocabulary = {tok: i for i, tok in enumerate(vocab_tokens)}
        n_docs = max(len(docs_tokens), 1)
        df = [0] * len(self.vocabulary)
        for tokens in docs_tokens:
            for tok in set(tokens):
                df[self.vocabulary[tok]] += 1
        self.idf = [math.log((1 + n_docs) / (1 + d)) + 1.0 for d in df]

    def embed(self, text: str) -> list[float]:
        if not self.vocabulary:
            self.fit([text or " "])
        counts = Counter(tokenize(text))
        if not counts:
            return [0.0] * len(self.vocabulary)
        vec = [0.0] * len(self.vocabulary)
        length = sum(counts.values())
        for token, count in counts.items():
            idx = self.vocabulary.get(token)
            if idx is None:
                continue
            vec[idx] = (count / length) * self.idf[idx]
        return _l2_normalize(vec)


class MiniLMEmbedder:
    """Neural embeddings via sentence-transformers (CPU-friendly MiniLM)."""

    name = "minilm"

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self._model = None

    def fit(self, corpus: list[str]) -> None:
        # Neural models are pretrained; fit is a no-op.
        return None

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "EMBEDDING_PROVIDER=minilm requires sentence-transformers. "
                "Install with: uv pip install sentence-transformers"
            ) from exc
        self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, text: str) -> list[float]:
        model = self._load()
        vector = model.encode(text or " ", normalize_embeddings=True)
        return [float(x) for x in vector.tolist()]


def get_embedder(provider: str | None = None) -> Embedder:
    chosen = (provider or os.getenv("EMBEDDING_PROVIDER", "tfidf")).strip().lower()
    if chosen in {"minilm", "neural", "sentence-transformers"}:
        return MiniLMEmbedder()
    if chosen in {"tfidf", "local"}:
        return TfidfEmbedder()
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {chosen}")


# Back-compat aliases used by older imports/tests
TfidfModel = TfidfEmbedder


def fit_tfidf(corpus: list[str]) -> TfidfEmbedder:
    model = TfidfEmbedder()
    model.fit(corpus or [""])
    return model
