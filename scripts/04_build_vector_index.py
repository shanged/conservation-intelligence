"""Build a persistent Chroma index from SQLite document chunks.

This Milestone 2B index uses a local Sentence Transformers model and cosine
distance. The collection is cleared before each build so repeated runs cannot
leave duplicates or stale vectors behind.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "db" / "conservation.db"
VECTOR_INDEX_DIR = PROJECT_ROOT / "db" / "vector_index"
MODEL_CACHE_DIR = VECTOR_INDEX_DIR / "model_cache"
COLLECTION_NAME = "conservation_chunks"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 16


def read_chunks(database_path: Path) -> list[tuple[str, str, str, str, str]]:
    """Return chunk ID, document ID, page, text, and source URL from SQLite."""
    if not database_path.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {database_path}. Run 03_build_chunks.py first."
        )
    with sqlite3.connect(database_path) as connection:
        return connection.execute(
            """
            SELECT chunk_id, doc_id, page, chunk_text, source_url
            FROM chunks
            ORDER BY chunk_id
            """
        ).fetchall()


def clear_collection(collection: chromadb.Collection) -> None:
    """Remove prior records so deleted SQLite chunks cannot remain indexed."""
    existing_ids = collection.get(include=[])["ids"]
    for start in range(0, len(existing_ids), 500):
        collection.delete(ids=existing_ids[start : start + 500])


def load_model() -> SentenceTransformer:
    """Prefer the cached model, downloading it only on the first build."""
    try:
        return SentenceTransformer(
            MODEL_NAME,
            cache_folder=str(MODEL_CACHE_DIR),
            local_files_only=True,
        )
    except OSError:
        return SentenceTransformer(MODEL_NAME, cache_folder=str(MODEL_CACHE_DIR))


def main() -> int:
    """Embed every SQLite chunk and rebuild the persistent Chroma collection."""
    rows = read_chunks(DATABASE_PATH)
    if not rows:
        raise RuntimeError("The chunks table is empty. Run 03_build_chunks.py first.")

    VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    model = load_model()
    client = chromadb.PersistentClient(path=str(VECTOR_INDEX_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "embedding_model": MODEL_NAME},
    )
    clear_collection(collection)

    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]
        texts = [row[3] for row in batch]
        embeddings = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        collection.upsert(
            ids=[row[0] for row in batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {"doc_id": row[1], "page": row[2], "source_url": row[4]}
                for row in batch
            ],
        )
        print(f"INDEXED {min(start + len(batch), len(rows))}/{len(rows)}")

    indexed_count = collection.count()
    if indexed_count != len(rows):
        raise RuntimeError(
            f"Index count mismatch: expected {len(rows)}, found {indexed_count}"
        )

    print(f"Embedding model: {MODEL_NAME}")
    print(f"Vector store: Chroma persistent collection '{COLLECTION_NAME}'")
    print(f"Chunks indexed: {indexed_count}")
    print(f"Index path: {VECTOR_INDEX_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
