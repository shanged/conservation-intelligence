"""Streamlit Corpus and Search interface for the expanded Milestone 2D corpus."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"
DATABASE_PATH = PROJECT_ROOT / "db" / "conservation.db"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from search_chunks import search_chunks  # noqa: E402
from semantic_search import (  # noqa: E402
    VectorIndexNotFoundError,
    semantic_search,
)


st.set_page_config(
    page_title="Conservation Document Intelligence",
    page_icon="🌿",
    layout="wide",
)


@st.cache_data
def load_metadata() -> pd.DataFrame:
    """Load corpus metadata without converting empty status fields to NaN."""
    return pd.read_csv(METADATA_PATH, dtype=str, keep_default_na=False)


def corpus_tab() -> None:
    """Render corpus counts, filters, statuses, and source metadata."""
    if not METADATA_PATH.exists():
        st.error(f"Metadata file not found: {METADATA_PATH}")
        return

    metadata = load_metadata()
    st.metric("Documents", len(metadata))

    filter_col1, filter_col2 = st.columns(2)
    agencies = sorted(value for value in metadata["agency"].unique() if value)
    topics = sorted(value for value in metadata["topic"].unique() if value)
    agency = filter_col1.selectbox("Agency", ["All agencies", *agencies])
    topic = filter_col2.selectbox("Topic", ["All topics", *topics])

    filtered = metadata
    if agency != "All agencies":
        filtered = filtered[filtered["agency"] == agency]
    if topic != "All topics":
        filtered = filtered[filtered["topic"] == topic]

    status_counts = metadata["download_status"].replace("", "unknown").value_counts()
    st.caption(
        "Download status: "
        + ", ".join(f"{status}: {count}" for status, count in status_counts.items())
    )
    st.dataframe(
        filtered[
            ["doc_id", "title", "year", "agency", "topic", "download_status", "url"]
        ],
        width="stretch",
        hide_index=True,
        column_config={"url": st.column_config.LinkColumn("Source URL")},
    )

    # Milestone 3A diagnostic only; a full Wiki UI is deliberately deferred.
    if DATABASE_PATH.exists():
        import sqlite3
        with st.expander("Entity extraction diagnostics"):
            try:
                with sqlite3.connect(DATABASE_PATH) as connection:
                    entity_counts = pd.read_sql_query(
                        "SELECT entity_type, COUNT(*) AS count FROM entities GROUP BY entity_type ORDER BY entity_type",
                        connection,
                    )
                    relation_counts = pd.read_sql_query(
                        "SELECT relation, COUNT(*) AS count FROM relations GROUP BY relation ORDER BY relation",
                        connection,
                    )
                left, right = st.columns(2)
                left.dataframe(entity_counts, hide_index=True, width="stretch")
                right.dataframe(relation_counts, hide_index=True, width="stretch")
            except Exception:
                st.info("Run scripts/05_extract_entities.py to build extraction diagnostics.")


def display_result(result: object, semantic: bool) -> None:
    """Render one keyword or semantic result consistently."""
    title = getattr(result, "title")
    doc_id = getattr(result, "doc_id")
    page = getattr(result, "page")
    with st.container(border=True):
        st.markdown(f"#### {title}")
        location = f"Page {page}" if str(page) != "Web" else "Location: Web page"
        details = f"**{doc_id}** · {location}"
        if semantic:
            details += (
                f" · Chunk {getattr(result, 'chunk_id')}"
                f" · Similarity {getattr(result, 'similarity'):.3f}"
            )
        st.markdown(details)
        st.write(getattr(result, "text_snippet"))
        st.markdown(f"[Open source document]({getattr(result, 'source_url')})")


def search_tab() -> None:
    """Render keyword and semantic retrieval with friendly empty/error states."""
    query = st.text_input("Search the conservation corpus")
    control_col1, control_col2 = st.columns(2)
    search_mode = control_col1.selectbox(
        "Search method", ["Keyword Search", "Semantic Search"]
    )
    result_count = control_col2.selectbox("Number of results", [3, 5, 10], index=1)

    if not query.strip():
        st.info("Enter a query to search the conservation corpus.")
        return

    semantic = search_mode == "Semantic Search"
    try:
        if semantic:
            results = semantic_search(query, top_k=result_count)
        else:
            results = search_chunks(query, DATABASE_PATH, limit=result_count)
    except VectorIndexNotFoundError as exc:
        st.warning(str(exc))
        return
    except Exception as exc:
        st.error(f"Search could not be completed: {exc}")
        return

    if not results:
        st.info("No matching chunks were found.")
        return
    for result in results:
        display_result(result, semantic)


st.title("Conservation Document Intelligence Prototype")
st.caption("Milestone 2D · DOC001–DOC035 · Local retrieval prototype")

corpus, search = st.tabs(["Corpus", "Search"])
with corpus:
    corpus_tab()
with search:
    search_tab()
