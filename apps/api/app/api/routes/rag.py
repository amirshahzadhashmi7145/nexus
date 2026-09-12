from fastapi import APIRouter

from app.rag.retriever import get_index, list_sources, retrieve
from app.schemas_rag import RagDocumentsOut, RagHit, RagQueryIn, RagQueryOut

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/documents", response_model=RagDocumentsOut)
def get_rag_documents() -> RagDocumentsOut:
    index = get_index()
    return RagDocumentsOut(documents=list_sources(), chunk_count=len(index.chunks))


@router.post("/query", response_model=RagQueryOut)
def post_rag_query(body: RagQueryIn) -> RagQueryOut:
    hits = retrieve(body.question, top_k=body.top_k)
    payload = [
        RagHit(source=h.source, chunk_id=h.chunk_id, score=round(h.score, 4), text=h.text)
        for h in hits
    ]
    context = "\n\n".join(f"[{h.source}] {h.text}" for h in hits)
    return RagQueryOut(question=body.question, hits=payload, context=context)
