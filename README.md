# FSight 

A RAG pipeline that lets you ask questions about SEC 10-K annual filings for Apple, Microsoft, Google, Amazon, and Meta. Type a question, pick a company, get an answer with sources.

## Limitations

This project is for my personal learning purposes only, there's no vocation to give real financial information & advice:

Answers are AI-generated from SEC filings. They can be wrong, incomplete, or miss context. Don't use this for anything financial or investment-related — go read the actual filings for that.

## What it does

It pulls 10-K filings from SEC EDGAR (2010 to now), chunks and embeds them with OpenAI, stores the vectors in Qdrant, and at query time retrieves the most relevant chunks, reranks them with Voyage AI, then feeds them to GPT-4o-mini to generate the answer. Standard RAG, nothing fancy.

The UI is a split terminal — left side to write your question and pick the ticker, right side shows the answer and where it came from.

## Stack

- **Embeddings** — OpenAI `text-embedding-3-small`
- **Reranker** — Voyage AI `rerank-2.5`
- **LLM** — GPT-4o-mini
- **Vector DB** — Qdrant
- **Backend** — FastAPI
- **Frontend** — Vue 3 + Vite, served by nginx in production (OVH)

## Running it

You need Docker and two API keys in a `.env` at the root:

```
OPENAI_API_KEY=...
VOYAGE_API_KEY=...
```

Then:

```bash
docker compose up --build
```

Run `ingestor.py` in the Docker exec section (fetches and embeds all data), then stop the ingestor container (not obligatory) and FSight is ready to use at `http://localhost:5173/`


Qdrant dashboard is at `http://localhost:6333/dashboard`.

## Nginx

In production (`docker-compose.prod.yml`) the Vue frontend is packaged into an nginx container.  
The configuration lives in `nginx/nginx.conf` and is mounted read-only into the container.

```
Browser
  │
  │ HTTP :80
  ▼
nginx ──── 301 redirect ──▶ HTTPS :443
  │
  ├─ /          → serve pre-built Vue SPA from /usr/share/nginx/html
  │               (SPA fallback: unknown paths return index.html so
  │                Vue Router handles them client-side)
  │
  ├─ /search    → reverse proxy → FastAPI container (api:8000/search)
  │               60 s read timeout to accommodate the full RAG pipeline
  │               (embed → retrieve → rerank → GPT-4o-mini)
  │               X-RateLimit-Remaining header is passed through to the
  │               browser so the UI can display remaining quota
  │
  └─ /dates     → reverse proxy → FastAPI container (api:8000/dates)
                  lightweight metadata call, no extended timeout needed
```

**TLS** certificates are issued by Let's Encrypt (Certbot) and mounted from the host at  
`/etc/letsencrypt`.  The HTTP block simply redirects every plain-text request to HTTPS.

**Security headers** added to every response:

| Header | Value | Purpose |
|---|---|---|
| `X-Frame-Options` | `SAMEORIGIN` | Prevents clickjacking via `<iframe>` embeds |
| `X-Content-Type-Options` | `nosniff` | Stops MIME-type sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits URL leakage in the `Referer` header |

## Covered companies

AAPL · MSFT · GOOGL · AMZN · META

All 10-K filings from 2010 to the current year. Each report includes multi-year comparisons so you can often get data from earlier periods too.


