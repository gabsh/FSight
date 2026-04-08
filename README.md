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

## Nginx configuration (production)

In production (`docker-compose.prod.yml`) nginx runs inside the `frontend` container, serving the compiled Vue app and acting as a reverse proxy in front of FastAPI.  The config lives in `nginx/nginx.conf` and is mounted into the container at `/etc/nginx/conf.d/fsight.conf`.

### HTTP → HTTPS redirect (port 80)

```
server {
    listen 80;
    server_name fsight.fr;
    return 301 https://$host$request_uri;
}
```

Any plain-HTTP request is permanently redirected (HTTP 301) to the same URL over HTTPS so that all traffic is always encrypted.

### HTTPS server (port 443)

#### TLS / SSL

```
ssl_certificate     /etc/letsencrypt/live/fsight.fr/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/fsight.fr/privkey.pem;
```

The TLS certificate is issued by Let's Encrypt (via Certbot) and stored on the host.  The `/etc/letsencrypt` directory is mounted read-only into the container by `docker-compose.prod.yml`.

#### Static SPA files

```
root  /usr/share/nginx/html;
index index.html;

location / {
    try_files $uri $uri/ /index.html;
}
```

The Vue 3 build output is copied into `/usr/share/nginx/html` during the Docker image build (multi-stage `Dockerfile.prod`).  The `try_files` directive is the standard SPA fallback: if the requested path is not a real file nginx returns `index.html`, which lets Vue Router handle client-side routing.  Without this, refreshing any non-root URL would return a 404.

#### Reverse proxy — `/search`

```
location /search {
    proxy_pass         http://api:8000/search;
    proxy_http_version 1.1;

    proxy_set_header   Host              $host;
    proxy_set_header   X-Real-IP         $remote_addr;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;

    proxy_pass_header  X-RateLimit-Remaining;

    proxy_read_timeout    60s;
    proxy_connect_timeout 10s;
}
```

Requests to `/search` are forwarded to the `api` Docker service (FastAPI) on port 8000.  The browser never talks directly to FastAPI; nginx is the only publicly exposed entry point.

- **`proxy_set_header` lines** — forward the original host, real client IP, forwarding chain, and the protocol (HTTPS) to the backend so it can log and reason about requests correctly.
- **`proxy_pass_header X-RateLimit-Remaining`** — the API sets this header; nginx passes it through to the browser so the frontend can display the remaining request quota.
- **Timeouts** — the RAG pipeline (embedding lookup + vector search + LLM call) can take several seconds, so `proxy_read_timeout` is set to 60 s and `proxy_connect_timeout` to 10 s.

#### Reverse proxy — `/dates`

```
location /dates {
    proxy_pass http://api:8000/dates;
    ...
}
```

Same forwarding pattern for the `/dates` endpoint, which returns the list of available 10-K filing years per ticker.

#### Security headers

| Header | Value | Purpose |
|---|---|---|
| `X-Frame-Options` | `SAMEORIGIN` | Blocks the page from being embedded in an `<iframe>` on a foreign origin (prevents clickjacking). |
| `X-Content-Type-Options` | `nosniff` | Stops browsers from sniffing the MIME type of responses (prevents MIME-confusion attacks). |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Sends the full `Referer` only for same-origin navigations; cross-origin requests receive only the origin. |

---

## Covered companies

AAPL · MSFT · GOOGL · AMZN · META

All 10-K filings from 2010 to the current year. Each report includes multi-year comparisons so you can often get data from earlier periods too.


