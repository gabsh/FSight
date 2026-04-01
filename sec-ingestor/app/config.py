import os
from openai import OpenAI
from qdrant_client import QdrantClient
import voyageai

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

COLLECTION_NAME = "financial_docs"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM   = 1536

COMPANIES = {
    "AAPL":  "0000320193",
    "MSFT":  "0000789019",
    "GOOGL": "0001652044",
    "AMZN":  "0001018724",
    "META":  "0001326801",
}

HEADERS      = {"User-Agent": "FSight fs@gmail.com"}
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

_clientOpenAI = OpenAI()
_clientVoyage  = voyageai.Client(api_key=VOYAGE_API_KEY)

qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def embed(text: str) -> list[float]:
    return _clientOpenAI.embeddings.create(model=EMBEDDING_MODEL, input=text).data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    response = _clientOpenAI.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


LLM_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are a financial analyst assistant specializing in SEC 10-K filings. "
    "Always respond in the same language as the user's question. "
    "Answer the user's question using ONLY the information present in the provided excerpts."
    "If the excerpts do not contain enough information to answer the question, "
    "answer in the language of the question by translating : 'I could not find any relevant information in the available documents. Please check if the company symbol matches the one you provide in your query or try another question.' "
    "Do NOT infer, speculate, or use any knowledge outside of the provided excerpts. "
    "Be concise, factual, and cite the source (ticker, date, section) when relevant."
)


def generate(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[{c['ticker']}] [{c['date']}]\n{c['text']}"
        for c in chunks
    )
    response = _clientOpenAI.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return response.choices[0].message.content


VOYAGE_RERANK_MODEL = "rerank-2.5"


def rerank(question: str, candidates: list, top_n: int) -> list:
    docs = [c.payload["text"] for c in candidates]
    result = _clientVoyage.rerank(question, docs, model=VOYAGE_RERANK_MODEL, top_k=top_n)
    return [candidates[r.index] for r in result.results]
