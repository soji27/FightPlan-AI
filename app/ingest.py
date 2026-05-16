"""
Ingestion script: Loads ufc_data.csv and stores it in ChromaDB.
Run this once before starting the application to populate the vector database.
"""

import math
import os
import sys
from urllib.parse import urlparse

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.getenv("CSV_PATH", "./data/fighters/ufc_data.csv")
CHROMA_HOST = os.getenv("CHROMA_HOST", "http://localhost:8000")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "mma_fighters")
BATCH_SIZE = 100


def _safe(value, fmt: str = "", default="N/A") -> str:
    """Safely format a value, returning default for NaN/None."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    if fmt:
        try:
            return format(float(value), fmt)
        except (TypeError, ValueError):
            return str(value)
    return str(value).strip() or default


def build_chunk(row: pd.Series) -> str:
    """Build a text chunk from a fight row."""
    return (
        f"Combat: {_safe(row.get('R_fighter'))} vs {_safe(row.get('B_fighter'))} | "
        f"Date: {_safe(row.get('date'))} | "
        f"Catégorie: {_safe(row.get('weight_class'))} | "
        f"Gagnant: {_safe(row.get('Winner'))} | "
        f"KD Rouge: {_safe(row.get('R_avg_KD'), '.2f')} | "
        f"KD Bleu: {_safe(row.get('B_avg_KD'), '.2f')} | "
        f"Précision frappes Rouge: {_safe(row.get('R_avg_SIG_STR_pct'), '.1%')} | "
        f"Précision frappes Bleu: {_safe(row.get('B_avg_SIG_STR_pct'), '.1%')} | "
        f"Takedowns Rouge: {_safe(row.get('R_avg_TD_pct'), '.1%')} | "
        f"Takedowns Bleu: {_safe(row.get('B_avg_TD_pct'), '.1%')} | "
        f"Victoires Rouge: {_safe(row.get('R_wins'))} | "
        f"Défaites Rouge: {_safe(row.get('R_losses'))} | "
        f"Victoires Bleu: {_safe(row.get('B_wins'))} | "
        f"Défaites Bleu: {_safe(row.get('B_losses'))}"
    )


def embed_texts(texts: list, ollama_client) -> list:
    """Embed a list of texts using Ollama nomic-embed-text."""
    embeddings = []
    for text in texts:
        response = ollama_client.embeddings(model=EMBED_MODEL, prompt=text)
        embeddings.append(response["embedding"])
    return embeddings


def main():
    print("=" * 60)
    print("FightPlan AI - ChromaDB Ingestion")
    print("=" * 60)

    # --- Load CSV ---
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV not found at {CSV_PATH}")
        sys.exit(1)

    print(f"Loading CSV from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    total = len(df)
    print(f"Loaded {total} rows.")

    # --- Connect to ChromaDB ---
    print(f"Connecting to ChromaDB at {CHROMA_HOST}...")
    import chromadb

    parsed = urlparse(CHROMA_HOST)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8000

    try:
        client = chromadb.HttpClient(host=host, port=port)
        client.heartbeat()
        print("ChromaDB connection OK.")
    except Exception as exc:
        print(f"ERROR: Cannot connect to ChromaDB: {exc}")
        sys.exit(1)

    # Delete and recreate collection for fresh ingestion
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"Created collection '{COLLECTION_NAME}'.")

    # --- Connect to Ollama ---
    print(f"Connecting to Ollama at {OLLAMA_HOST}...")
    import ollama

    parsed_ollama = urlparse(OLLAMA_HOST)
    ollama_url = f"{parsed_ollama.scheme}://{parsed_ollama.hostname}:{parsed_ollama.port or 11434}"
    ollama_client = ollama.Client(host=ollama_url)

    try:
        ollama_client.list()
        print("Ollama connection OK.")
    except Exception as exc:
        print(f"ERROR: Cannot connect to Ollama: {exc}")
        sys.exit(1)

    # --- Ingest in batches ---
    print(f"\nStarting ingestion in batches of {BATCH_SIZE}...")
    processed = 0
    errors = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch = df.iloc[batch_start: batch_start + BATCH_SIZE]

        ids = []
        documents = []
        metadatas = []

        for idx, row in batch.iterrows():
            chunk = build_chunk(row)
            row_number = int(idx) + 2  # +2: header is row 1

            ids.append(f"fight_{row_number}")
            documents.append(chunk)
            metadatas.append({
                "source": "ufc_data.csv",
                "row": row_number,
                "r_fighter": str(row.get("R_fighter", "Unknown")).strip(),
                "b_fighter": str(row.get("B_fighter", "Unknown")).strip(),
                "date": str(row.get("date", "Unknown")).strip(),
                "weight_class": str(row.get("weight_class", "Unknown")).strip(),
            })

        # Embed batch
        try:
            embeddings = embed_texts(documents, ollama_client)
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            processed += len(batch)
        except Exception as exc:
            print(f"  WARNING: Batch {batch_start}-{batch_start + BATCH_SIZE} failed: {exc}")
            errors += len(batch)
            continue

        print(f"Ingestion: {processed}/{total} chunks traités")

    print(f"\n✓ Ingestion terminée: {processed} documents dans ChromaDB")
    if errors:
        print(f"  WARNING: {errors} documents failed to ingest.")


if __name__ == "__main__":
    main()
