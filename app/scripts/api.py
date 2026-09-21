import os
import time
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
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
    allow_origins=["https://www.fsight.fr"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=[],
)

# HTTP-level metrics (latency, request count, status codes by route) exposed on /metrics
Instrumentator().instrument(app).expose(app)

# Business metrics. Labels are kept to low-cardinality values (ticker, outcome) —
# never raw user input (e.g. the question text) as a label.
SEARCH_REQUESTS = Counter(
    "fsight_search_requests_total",
    "Search requests by ticker and outcome",
    ["ticker", "outcome"],
)
SEARCH_DURATION = Histogram(
    "fsight_search_duration_seconds",
    "End-to-end /search latency (embed + qdrant + rerank + generate)",
    ["ticker"],
)
RATE_LIMIT_HITS = Counter(
    "fsight_rate_limit_exceeded_total",
    "Requests rejected by the daily rate limiter",
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    RATE_LIMIT_HITS.inc()
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
    ticker_label = req.ticker or "ALL"
    start = time.perf_counter()
    try:
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
            SEARCH_REQUESTS.labels(ticker=ticker_label, outcome="no_results").inc()
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
        SEARCH_REQUESTS.labels(ticker=ticker_label, outcome="success").inc()
        return {"answer": answer, "sources": chunks}
    except HTTPException:
        raise
    except Exception:
        SEARCH_REQUESTS.labels(ticker=ticker_label, outcome="error").inc()
        raise
    finally:
        SEARCH_DURATION.labels(ticker=ticker_label).observe(time.perf_counter() - start)


if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")
