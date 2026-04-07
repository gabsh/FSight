# FSight · [github.com/gabsh/FSight](https://github.com/gabsh/FSight)

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

## Covered companies

AAPL · MSFT · GOOGL · AMZN · META

All 10-K filings from 2010 to the current year. Each report includes multi-year comparisons so you can often get data from earlier periods too.


