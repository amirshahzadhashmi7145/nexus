"""Local text embeddings for Phase 5.

Mentor note:
- Production RAG usually uses neural embeddings (e.g. MiniLM) + a vector DB.
- Here we use TF-IDF vectors so you learn retrieval without downloading a GPU model.
- The Retriever API stays the same when you later swap the embedder.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


@dataclass
class TfidfModel:
    vocabulary: dict[str, int]
    idf: list[float]

    def embed(self, text: str) -> list[float]:
        counts = Counter(tokenize(text))
        if not counts:
            return [0.0] * len(self.vocabulary)
        vec = [0.0] * len(self.vocabulary)
        length = sum(counts.values())
        for token, count in counts.items():
            idx = self.vocabulary.get(token)
            if idx is None:
                continue
            tf = count / length
            vec[idx] = tf * self.idf[idx]
        return _l2_normalize(vec)


def fit_tfidf(corpus: list[str]) -> TfidfModel:
    docs_tokens = [tokenize(doc) for doc in corpus]
    vocab_tokens = sorted({tok for tokens in docs_tokens for tok in tokens})
    vocabulary = {tok: i for i, tok in enumerate(vocab_tokens)}
    n_docs = max(len(docs_tokens), 1)
    df = [0] * len(vocabulary)
    for tokens in docs_tokens:
        for tok in set(tokens):
            df[vocabulary[tok]] += 1
    idf = [math.log((1 + n_docs) / (1 + d)) + 1.0 for d in df]
    return TfidfModel(vocabulary=vocabulary, idf=idf)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]
