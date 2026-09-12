"""Document chunking for RAG.

Learn: models have limited context windows. We split long docs into overlapping
chunks so retrieval can return the relevant paragraph, not the whole file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source: str
    text: str


def load_markdown_documents(directory: Path) -> list[tuple[str, str]]:
    docs: list[tuple[str, str]] = []
    for path in sorted(directory.glob("*.md")):
        docs.append((path.name, path.read_text(encoding="utf-8")))
    return docs


def chunk_text(source: str, text: str, *, size: int = 400, overlap: int = 80) -> list[Chunk]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + size)
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(
                Chunk(chunk_id=f"{source}::{index}", source=source, text=piece)
            )
            index += 1
        if end >= len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def chunk_documents(docs: list[tuple[str, str]], *, size: int = 400, overlap: int = 80) -> list[Chunk]:
    out: list[Chunk] = []
    for source, text in docs:
        out.extend(chunk_text(source, text, size=size, overlap=overlap))
    return out
