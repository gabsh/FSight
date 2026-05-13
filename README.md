# FSight

A RAG pipeline that lets you ask questions about SEC 10-K annual filings for Apple, Microsoft, Google, Amazon, and Meta. Type a question, pick a company, get an answer with sources.

## Limitations

Personal learning project — not financial advice. Answers are AI-generated from SEC filings and can be wrong, incomplete, or miss context. Don't use this for anything investment-related.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          VPS (k3s)                              │
│                                                                 │
│   Internet ──► Traefik :443 ──► TLS termination                 │
│                    │            cert-manager (Let's Encrypt)    │
│                    │                                            │
│          ┌─────────┼──────────┐                                 │
│          │         │          │                                 │
│         /        /search   /dates                               │
│          │         │          │                                 │
│          ▼         └────┬─────┘                                 │
│  ┌───────────────┐      ▼                                       │
│  │  Frontend ×1  │  ┌────────────────┐                          │
│  │  nginx        │  │   API ×3       │                          │
│  │  Vue 3 SPA    │  │   FastAPI      │                          │
│  └───────────────┘  │   slowapi      │                          │
│                     └───────┬────────┘                          │
│                             │                                   │
│                             ▼                                   │
│                    ┌─────────────────┐                          │
│                    │   Qdrant ×1     │                          │
│                    │   StatefulSet   │                          │
│                    │   PVC 5Gi       │                          │
│                    └─────────────────┘                          │
│                                                                 │
│   ┌───────────────────────────────────┐                         │
│   │  Ingestor (Job — run once)        │                         │
│   │  SEC EDGAR → chunk → embed        │──► Qdrant               │
│   │  PVC 2Gi (HTML cache)             │                         │
│   └───────────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

**Query pipeline (per request):**
```
Question
  │
  ├─► OpenAI text-embedding-3-small ──► vector
  │
  ├─► Qdrant ANN search ──► top 20 candidates
  │
  ├─► Voyage AI rerank-2.5 ──► top 6 chunks
  │
  └─► GPT-4o-mini ──► Answer + sources
```

**Ingestion pipeline (run once):**
```
SEC EDGAR HTML
  │
  ├─► BeautifulSoup parse
  ├─► Chunk (800 chars, 160 overlap)
  ├─► OpenAI embed (batches of 2048)
  └─► Qdrant upsert → collection "financial_docs"
```

---

## Stack

| Layer | Technology |
|---|---|
| **Embeddings** | OpenAI `text-embedding-3-small` |
| **Reranker** | Voyage AI `rerank-2.5` |
| **LLM** | GPT-4o-mini |
| **Vector DB** | Qdrant |
| **Backend** | FastAPI + slowapi (rate limiting 40 req/day) |
| **Frontend** | Vue 3 + Vite, served by nginx |
| **Orchestration** | Kubernetes — kind (local dev), k3s (prod) |
| **Ingress** | Traefik + cert-manager (Let's Encrypt) |
| **Image registry** | Docker Hub (`gabinn/fsight-*`) |
| **CI/CD** | GitHub Actions → Docker Hub → k3s rollout |

---

## Evolution

**v1 — Docker Compose**
Single-server setup with docker-compose.prod.yml. An external nginx-edge-proxy container handled SSL termination and hostname routing for fsight.fr and mlens.fr via a shared Docker network (`proxy-network`).

**v2 — Kubernetes (current)**
Migrated to k3s on the same VPS. Traefik replaces nginx-edge-proxy as the cluster-wide ingress controller. cert-manager replaces Certbot for TLS. Images are built and pushed to Docker Hub via GitHub Actions, then pulled by k3s on deploy. The ingestor became a Kubernetes Job instead of a long-running container with `sleep infinity`.

Key architectural change: the frontend nginx no longer proxies API calls — the Ingress routes `/search` and `/dates` directly to the API service, making each service responsible for a single concern.

---

## Covered companies

AAPL · MSFT · GOOGL · AMZN · META

All 10-K filings from 2010 to the current year.

---

## Docs

- [KUBERNETES.md](KUBERNETES.md) — concepts, commands, and workflows for local dev and production
