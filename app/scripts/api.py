import os
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from qdrant_client.models import Filter, FieldCondition, MatchValue
from config import COLLECTION_NAME, COMPANIES, embed, qdrant, rerank, generate

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fsight.fr", "https://www.fsight.fr"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=[],
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Daily limit reached (40 queries/day). Come back tomorrow."},
    )


class SearchRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    ticker: str | None = None

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v):
        valid = set(COMPANIES.keys())
        if v is not None and v not in valid:
            raise ValueError(f"ticker must be one of {sorted(valid)}")
        return v


@lru_cache(maxsize=1)
def _fetch_dates():
    result = {}
    for ticker in COMPANIES:
        years = set()
        offset = None
        while True:
            points, offset = qdrant.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=Filter(must=[FieldCondition(key="ticker", match=MatchValue(value=ticker))]),
                limit=1000,
                offset=offset,
                with_vectors=False,
                with_payload=["date"],
            )
            for p in points:
                years.add(int(p.payload["date"][:4]))
            if offset is None:
                break
        result[ticker] = sorted(years, reverse=True)
    return dict(result)


@app.get("/dates")
def get_dates():
    return _fetch_dates()


@app.post("/search")
@limiter.limit("40/day")
def search(request: Request, req: SearchRequest):
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
        limit=20,
    ).points

    if not candidates:
        raise HTTPException(status_code=404, detail="No results found")

    results = rerank(req.question, candidates, top_n=6)
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
