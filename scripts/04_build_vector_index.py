"""Build a persistent Chroma index from smaller embedding windows.

The original 600-900 word SQLite chunks remain unchanged. Each chunk is split
into deterministic, overlapping windows sized for MiniLM before embedding. The
collection is cleared before each build so repeated runs cannot leave stale or
duplicate vectors behind.
"""

from __future__ import annotations

import sqlite3
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import chromadb
from sentence_transformers import SentenceTransformer
from transformers.utils import logging as transformers_logging


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "db" / "conservation.db"
VECTOR_INDEX_DIR = PROJECT_ROOT / "db" / "vector_index"
MODEL_CACHE_DIR = VECTOR_INDEX_DIR / "model_cache"
COLLECTION_NAME = "conservation_chunks"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 16
WINDOW_WORDS = 180
WINDOW_OVERLAP_WORDS = 40
MAX_WINDOW_TOKENS = 240


class Tokenizer(Protocol):
    """Minimal tokenizer interface used to enforce MiniLM's input limit."""

    def tokenize(self, text: str) -> list[str]: ...

    def num_special_tokens_to_add(self, pair: bool = False) -> int: ...


@dataclass(frozen=True)
class EmbeddingWindow:
    """A MiniLM-sized window tied to its original citation-bearing chunk."""

    window_id: str
    original_chunk_id: str
    doc_id: str
    page: str
    source_url: str
    text: str


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


def token_count(text: str, tokenizer: Tokenizer) -> int:
    """Count model tokens without invoking truncation or warning side effects."""
    return len(tokenizer.tokenize(text)) + tokenizer.num_special_tokens_to_add(False)


def embedding_words(text: str) -> list[str]:
    """Normalize OCR punctuation noise while preserving readable word content."""
    words: list[str] = []
    for raw_word in text.split():
        word = re.sub(r"([^\w\s])\1{3,}", r"\1\1\1", raw_word)
        if any(character.isalnum() for character in word):
            words.append(word)
    return words


def split_into_windows(text: str, tokenizer: Tokenizer) -> list[str]:
    """Create deterministic word windows that never exceed the model limit.

    Windows aim for 180 words and 40 words of overlap. OCR dot leaders and
    similar punctuation-only units are omitted because they carry no semantic
    content but can consume most of MiniLM's token budget. A binary search
    shortens token-dense windows to a safe 240-token ceiling without splitting
    any word.
    """
    words = embedding_words(text)
    if not words:
        return []

    windows: list[str] = []
    start = 0
    while start < len(words):
        current_start = start
        low = start + 1
        high = min(start + WINDOW_WORDS, len(words))
        end = low
        while low <= high:
            candidate_end = (low + high) // 2
            candidate = " ".join(words[start:candidate_end])
            if token_count(candidate, tokenizer) <= MAX_WINDOW_TOKENS:
                end = candidate_end
                low = candidate_end + 1
            else:
                high = candidate_end - 1
        windows.append(" ".join(words[start:end]))
        if end == len(words):
            break
        next_start = end - WINDOW_OVERLAP_WORDS
        start = next_start if next_start > current_start else end
    return windows


def build_windows(
    rows: list[tuple[str, str, str, str, str]],
    tokenizer: Tokenizer,
) -> list[EmbeddingWindow]:
    """Expand all SQLite chunks into uniquely identified embedding windows."""
    windows: list[EmbeddingWindow] = []
    previous_verbosity = transformers_logging.get_verbosity()
    transformers_logging.set_verbosity_error()
    try:
        for chunk_id, doc_id, page, chunk_text, source_url in rows:
            for number, window_text in enumerate(
                split_into_windows(chunk_text, tokenizer), start=1
            ):
                windows.append(
                    EmbeddingWindow(
                        window_id=f"{chunk_id}_WIN_{number:02d}",
                        original_chunk_id=chunk_id,
                        doc_id=doc_id,
                        page=page,
                        source_url=source_url,
                        text=window_text,
                    )
                )
    finally:
        transformers_logging.set_verbosity(previous_verbosity)
    return windows


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
    """Embed every chunk window and rebuild the persistent collection."""
    rows = read_chunks(DATABASE_PATH)
    if not rows:
        raise RuntimeError("The chunks table is empty. Run 03_build_chunks.py first.")
    VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    model = load_model()
    windows = build_windows(rows, model.tokenizer)
    client = chromadb.PersistentClient(path=str(VECTOR_INDEX_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": MODEL_NAME,
            "index_unit": "embedding_window",
        },
    )
    clear_collection(collection)

    for start in range(0, len(windows), BATCH_SIZE):
        batch = windows[start : start + BATCH_SIZE]
        texts = [window.text for window in batch]
        embeddings = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        collection.upsert(
            ids=[window.window_id for window in batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {
                    "embedding_window_id": window.window_id,
                    "original_chunk_id": window.original_chunk_id,
                    "doc_id": window.doc_id,
                    "page": window.page,
                    "source_url": window.source_url,
                }
                for window in batch
            ],
        )
        print(f"INDEXED {min(start + len(batch), len(windows))}/{len(windows)}")

    indexed_count = collection.count()
    if indexed_count != len(windows):
        raise RuntimeError(
            f"Index count mismatch: expected {len(windows)}, found {indexed_count}"
        )

    print(f"Embedding model: {MODEL_NAME}")
    print(f"Vector store: Chroma persistent collection '{COLLECTION_NAME}'")
    print(f"Original chunks represented: {len(rows)}")
    print(
        f"Embedding windows: {indexed_count} "
        f"(target {WINDOW_WORDS} words, overlap {WINDOW_OVERLAP_WORDS}, "
        f"maximum {MAX_WINDOW_TOKENS} model tokens)"
    )
    print(f"Index path: {VECTOR_INDEX_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
