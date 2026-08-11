"""Streamlit interface for the conservation document intelligence prototype."""

from __future__ import annotations

import sys
import json
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
    if semantic:
        # Importing SentenceTransformers also imports Transformers and Torch.
        # Keep that dependency chain out of Streamlit's initial script run so
        # the app shell renders before any model/index resources are touched.
        try:
            from semantic_search import VectorIndexNotFoundError, semantic_search

            results = semantic_search(query, top_k=result_count)
        except VectorIndexNotFoundError as exc:
            st.warning(str(exc))
            return
        except Exception as exc:
            st.error(f"Search could not be completed: {exc}")
            return
    else:
        try:
            results = search_chunks(query, DATABASE_PATH, limit=result_count)
        except Exception as exc:
            st.error(f"Search could not be completed: {exc}")
            return

    if not results:
        st.info("No matching chunks were found.")
        return
    for result in results:
        display_result(result, semantic)


def wiki_tab() -> None:
    """Browse persistent, evidence-backed Markdown wiki pages."""
    if not DATABASE_PATH.exists():
        st.info("Build the project database before browsing wiki pages.")
        return
    import sqlite3
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            pages = pd.read_sql_query(
                "SELECT title, entity_type, file_path FROM wiki_pages ORDER BY entity_type, title",
                connection,
            )
    except Exception:
        st.info("Run scripts/06_generate_wiki.py to generate wiki pages.")
        return
    if pages.empty:
        st.info("No wiki pages have been generated yet.")
        return
    kinds = sorted(pages["entity_type"].unique())
    kind = st.selectbox("Entity type", kinds, key="wiki_entity_type")
    choices = pages[pages["entity_type"] == kind]
    title = st.selectbox("Entity", choices["title"].tolist(), key="wiki_entity")
    relative = choices.loc[choices["title"] == title, "file_path"].iloc[0]
    path = PROJECT_ROOT / relative
    if not path.exists():
        st.warning(f"Wiki file is missing: {relative}")
        return
    st.markdown(path.read_text(encoding="utf-8"))


def render_chat_response(response: dict[str, object]) -> None:
    """Display an answer and its inspectable source evidence."""
    st.markdown(str(response["answer"]))
    evidence = response.get("evidence", [])
    with st.expander(f"Sources ({len(evidence)})"):
        for item in evidence:
            location = "Web" if item["page"] == "Web" else f"page {item['page']}"
            st.markdown(f"**{item['title']}** — {item['doc_id']}, {location}")
            st.write(item["snippet"])
            st.markdown(f"[Open source document]({item['source_url']})")


def chatbot_tab() -> None:
    """Run the no-API citation chatbot with session-local history."""
    st.caption("Answers are composed only from retrieved corpus evidence. No API key is required.")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_chat_response(message["response"])
            else:
                st.markdown(message["content"])
    prompt = st.chat_input("Ask a question about the conservation corpus")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                # The chatbot uses semantic retrieval, so load it only after a
                # question is submitted rather than during the initial render.
                from semantic_search import VectorIndexNotFoundError
                from chatbot import answer_question

                response = answer_question(prompt).to_dict()
                render_chat_response(response)
            except VectorIndexNotFoundError as exc:
                response = {"answer": str(exc), "evidence": [], "citations": [], "insufficient": True}
                st.warning(str(exc))
            except Exception as exc:
                response = {"answer": f"The question could not be processed: {exc}", "evidence": [], "citations": [], "insufficient": True}
                st.error(response["answer"])
        st.session_state.chat_history.append({"role": "assistant", "response": response})


def evaluation_tab() -> None:
    """Display deterministic automated evaluation results."""
    path = PROJECT_ROOT / "outputs" / "demo_answers.json"
    if not path.exists():
        st.info("Run scripts/07_run_evaluation.py to generate evaluation results.")
        return
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        st.error(f"Evaluation output could not be read: {exc}")
        return
    passed = sum(record["status"] == "PASS" for record in records)
    st.metric("Automated heuristic checks", f"{passed}/{len(records)} passed")
    st.caption("These are integrity checks, not human judgments of answer quality.")
    for record in records:
        with st.expander(f"{record['number']}. {record['status']} — {record['question']}"):
            st.markdown(record["answer"])
            st.markdown("**Notes**")
            for note in record["notes"]:
                st.write(f"- {note}")


st.title("Conservation Document Intelligence Prototype")
st.caption("DOC001–DOC035 · Local, citation-grounded document intelligence")

corpus, search, wiki, chatbot, evaluation = st.tabs(
    ["Corpus", "Search", "Wiki", "Chatbot", "Evaluation"]
)
with corpus:
    corpus_tab()
with search:
    search_tab()
with wiki:
    wiki_tab()
with chatbot:
    chatbot_tab()
with evaluation:
    evaluation_tab()
