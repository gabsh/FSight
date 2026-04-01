import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from qdrant_client.models import Filter, FieldCondition, MatchValue
from config import COLLECTION_NAME, COMPANIES, embed, qdrant, rerank, generate

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    question: str
    ticker: str | None = None


@app.post("/search")
def search(req: SearchRequest):
    vector = embed(req.question)
    query_filter = (
        Filter(must=[FieldCondition(key="ticker", match=MatchValue(value=req.ticker))])
        if req.ticker
        else None
    )
    candidates = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        query_filter=query_filter,
        limit=18,
    ).points

    if not candidates:
        raise HTTPException(status_code=404, detail="No results found")

    results = rerank(req.question, candidates, top_n=5)
    chunks = [
        {
            "ticker": r.payload["ticker"],
            "date":   r.payload["date"],
            "text":   r.payload["text"],
        }
        for r in results
    ]
    answer = generate(req.question, chunks)
    return {"answer": answer, "sources": chunks}


if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")
