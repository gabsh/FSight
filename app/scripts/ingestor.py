import os
import re
import uuid
import datetime
import requests
from bs4 import BeautifulSoup
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, EMBEDDING_DIM, HEADERS, COMPANIES, embed_batch, qdrant

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 160


# ─── Étape 1 : Téléchargement des docs ────────────────────────────────────────

def fetch_10k_filings(cik: str) -> list[tuple[str, str, bytes]]:
    cik_int  = str(int(cik))
    url      = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS, timeout=30)

    if response.status_code != 200:
        print(f"Erreur EDGAR : {response.status_code}")
        exit(1)

    data = response.json()
    print(f"Société : {data['name']}")

    all_filings = {k: list(v) for k, v in data["filings"]["recent"].items()}
    for extra in data["filings"].get("files", []):
        url_extra  = f"https://data.sec.gov/submissions/{extra['name']}"
        extra_data = requests.get(url_extra, headers=HEADERS, timeout=30).json()
        for k, v in extra_data.items():
            if k in all_filings:
                all_filings[k].extend(v)

    forms             = all_filings["form"]
    accession_numbers = all_filings["accessionNumber"]
    primary_documents = all_filings["primaryDocument"]
    filing_dates      = all_filings["filingDate"]

    current_year = datetime.date.today().year
    ten_k_filings = [
        (accession_numbers[i], filing_dates[i], primary_documents[i])
        for i, form in enumerate(forms)
        if form == "10-K" and 2010 <= int(filing_dates[i][:4]) <= current_year
    ]
    print(f"  {len(ten_k_filings)} filings 10-K trouvés (2010–{current_year})")

    results = []
    os.makedirs("docs", exist_ok=True)

    for accession_number, date, primary_document in ten_k_filings:
        accession_clean = accession_number.replace("-", "")
        doc_url  = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}/{primary_document}"
        filename = f"docs/{accession_number}.html"

        if os.path.exists(filename):
            print(f"  ⊘ Fichier déjà présent : {filename}")
            with open(filename, "rb") as f:
                results.append((accession_number, date, f.read()))
        else:
            doc_response = requests.get(doc_url, headers=HEADERS, timeout=60)
            if doc_response.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(doc_response.content)
                print(f"  ✓ Téléchargé : {filename}")
                results.append((accession_number, date, doc_response.content))
            else:
                print(f"  ✗ Erreur {doc_response.status_code} pour {accession_number}")

    return results

# ─── Étape 2 : Chunking ───────────────────────────────────────────────────────

def parse_and_chunk(html_content: bytes) -> list[dict]:
    soup = BeautifulSoup(html_content, "lxml")
    for tag in soup(["script", "style", "img"]):
        tag.decompose()

    paragraphs = [p.strip() for p in re.split(r'\n+', soup.get_text(separator="\n", strip=True)) if p.strip()]
    text = " ".join(paragraphs)

    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        if end >= len(text):
            chunks.append({"text": text[start:].strip()})
            break
        cut = text.rfind(" ", start, end)
        if cut == -1:
            cut = end
        chunks.append({"text": text[start:cut].strip()})
        overlap_start = max(start, cut - CHUNK_OVERLAP)
        next_space = text.find(" ", overlap_start)
        start = next_space + 1 if next_space != -1 else cut

    return [c for c in chunks if len(c["text"]) > 80]

# ─── Étape 3+4 : Embedding + Indexation dans Qdrant ──────────────────────────

def ensure_collection():
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in existing:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        print(f"  Collection '{COLLECTION_NAME}' créée")
    else:
        print(f"  Collection '{COLLECTION_NAME}' déjà existante")


def delete_existing(accession_number: str):
    qdrant.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(
                key="accession_number",
                match=MatchValue(value=accession_number)
            )]
        )
    )


EMBED_BATCH_SIZE = 2048


def index_chunks(chunks: list[dict], accession_number: str, date: str, ticker: str):
    points = []
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch   = chunks[i:i + EMBED_BATCH_SIZE]
        vectors = embed_batch([c["text"] for c in batch])
        for j, (chunk, vector) in enumerate(zip(batch, vectors)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "ticker":           ticker,
                    "accession_number": accession_number,
                    "date":             date,
                    "doc_type":         "10-K",
                    "chunk_index":      i + j,
                    "text":             chunk["text"],
                }
            ))

    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

    print(f"  ✓ {len(points)} chunks indexés dans Qdrant")

# ─── Pipeline principal ───────────────────────────────────────────────────────

def main():
    print("\n=== FSight — Pipeline d'ingestion ===\n")

    ensure_collection()

    for ticker, cik in COMPANIES.items():
        print(f"\n► Entreprise : {ticker} (CIK {cik})")
        filings = fetch_10k_filings(cik)

        for accession_number, date, html_content in filings:
            print(f"\n  Filing {accession_number} ({date})")
            chunks = parse_and_chunk(html_content)
            print(f"  {len(chunks)} chunks générés")
            delete_existing(accession_number)
            index_chunks(chunks, accession_number, date, ticker)

    print("\n=== Pipeline terminé ===")


if __name__ == "__main__":
    main()
