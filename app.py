"""Streamlit interface for the conservation document intelligence prototype."""

from __future__ import annotations

import sys
import json
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from runtime_artifacts import (  # noqa: E402
    DATABASE_PATH,
    EVALUATION_PATH,
    METADATA_PATH,
    runtime_configuration_error,
)
from search_chunks import search_chunks  # noqa: E402
from ui_safety import (  # noqa: E402
    PRIVACY_NOTICE,
    RESEARCH_DISCLAIMER,
    answer_mode_label,
    fallback_status,
    safe_plain_text,
    safe_source_url,
)


st.set_page_config(
    page_title="Conservation Document Intelligence",
    page_icon="🌿",
    layout="wide",
)

configuration_error = runtime_configuration_error()
if configuration_error:
    st.error(configuration_error)
    st.stop()


@st.cache_data
def load_metadata() -> pd.DataFrame:
    """Load corpus metadata without converting empty status fields to NaN."""
    return pd.read_csv(METADATA_PATH, dtype=str, keep_default_na=False)


def corpus_tab() -> None:
    """Render corpus counts, filters, statuses, and source metadata."""
    if not METADATA_PATH.exists():
        st.error("Corpus metadata is unavailable. Restore the deployment artifacts.")
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
    display_metadata = filtered[
            ["doc_id", "title", "year", "agency", "topic", "download_status", "url"]
        ].copy()
    display_metadata["url"] = display_metadata["url"].map(
        lambda value: safe_source_url(value) or ""
    )
    st.dataframe(
        display_metadata,
        width="stretch",
        hide_index=True,
        column_config={"url": st.column_config.LinkColumn("Source URL")},
    )

    # Milestone 3A diagnostic only; a full Wiki UI is deliberately deferred.
    if DATABASE_PATH.exists():
        with st.expander("Entity extraction diagnostics"):
            try:
                from sqlite_readonly import connect_readonly

                with connect_readonly(DATABASE_PATH) as connection:
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
        st.subheader(str(title), divider=False)
        location = f"Page {page}" if str(page) != "Web" else "Location: Web page"
        details = f"**{doc_id}** · {location}"
        if semantic:
            details += (
                f" · Chunk {getattr(result, 'chunk_id')}"
                f" · Similarity {getattr(result, 'similarity'):.3f}"
            )
        st.write(details)
        st.text(str(getattr(result, "text_snippet")))
        source_url = safe_source_url(getattr(result, "source_url"))
        if source_url:
            st.link_button("Open source document", source_url)
        else:
            st.caption("Source link unavailable.")


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
        except VectorIndexNotFoundError:
            st.warning("Semantic search artifacts are unavailable.")
            return
        except Exception:
            st.error("Search could not be completed safely; please try again.")
            return
    else:
        try:
            results = search_chunks(query, DATABASE_PATH, limit=result_count)
        except Exception:
            st.error("Search could not be completed safely; please try again.")
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
    try:
        from sqlite_readonly import connect_readonly

        with connect_readonly(DATABASE_PATH) as connection:
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
        st.warning("The selected wiki page is unavailable.")
        return
    st.markdown(path.read_text(encoding="utf-8"))


def render_chat_response(response: dict[str, object]) -> None:
    """Display an answer and its inspectable source evidence."""
    st.caption(answer_mode_label(response))
    reason_status = fallback_status(response)
    if reason_status and response.get("fallback_reason") != "insufficient_evidence":
        st.caption(reason_status)
    diagnostics = response.get("diagnostics")
    if (
        response.get("fallback_reason") == "invalid_openai_response"
        and isinstance(diagnostics, dict)
        and diagnostics.get("validation_failure_category")
    ):
        detail = str(diagnostics["validation_failure_category"]).replace("_", " ")
        st.caption(f"Validation detail: {detail}.")
    if response.get("status_message"):
        st.info(str(response["status_message"]))
    if response.get("insufficient"):
        st.info(str(response["answer"]))
    else:
        st.markdown(safe_plain_text(response["answer"]))
    evidence = response.get("evidence", [])
    with st.expander(f"Sources ({len(evidence)})"):
        for item in evidence:
            location = "Web" if item["page"] == "Web" else f"page {item['page']}"
            st.markdown(f"**{item['title']}** — {item['doc_id']}, {location}")
            st.text(str(item["snippet"]))
            source_url = safe_source_url(item.get("source_url"))
            if source_url:
                st.link_button("Open source document", source_url)
            else:
                st.caption("Source link unavailable.")


def chatbot_tab() -> None:
    """Run optional synthesis with deterministic fallback and local history."""
    st.caption("Answers use retrieved corpus evidence; local deterministic fallback requires no API key.")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "openai_request_controls" not in st.session_state:
        from request_controls import OpenAISessionState

        st.session_state.openai_request_controls = OpenAISessionState()
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_chat_response(message["response"])
            else:
                st.text(str(message["content"]))
    prompt = st.chat_input("Ask a question about the conservation corpus")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.text(prompt)
        with st.chat_message("assistant"):
            try:
                # The chatbot uses semantic retrieval, so load it only after a
                # question is submitted rather than during the initial render.
                from semantic_search import VectorIndexNotFoundError
                from openai_chatbot import answer_question_hybrid
                from request_controls import stable_request_id

                response = answer_question_hybrid(
                    prompt,
                    session_state=st.session_state.openai_request_controls,
                    request_id=stable_request_id(
                        f"{len(st.session_state.chat_history)}:{prompt}"
                    ),
                ).to_dict()
                diagnostics = response.get("diagnostics")
                if diagnostics:
                    usage = st.session_state.openai_request_controls.usage_diagnostics
                    usage.append(diagnostics)
                    del usage[:-50]
                render_chat_response(response)
            except VectorIndexNotFoundError:
                response = {"answer": "Semantic retrieval is temporarily unavailable.", "evidence": [], "citations": [], "insufficient": True, "mode": "deterministic_fallback", "fallback_reason": "retrieval_failure"}
                st.warning(response["answer"])
            except Exception:
                response = {"answer": "The question could not be processed safely; please try again.", "evidence": [], "citations": [], "insufficient": True}
                st.error(response["answer"])
        st.session_state.chat_history.append({"role": "assistant", "response": response})


def evaluation_tab() -> None:
    """Display deterministic automated evaluation results."""
    path = EVALUATION_PATH
    if not path.exists():
        st.info("Run scripts/07_run_evaluation.py to generate evaluation results.")
        return
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        st.error("Evaluation output could not be read safely.")
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

    hybrid_path = PROJECT_ROOT / "outputs" / "hybrid_evaluation.json"
    st.divider()
    st.subheader("Deterministic vs hybrid comparison")
    if not hybrid_path.exists():
        st.info("Run the offline hybrid evaluation to generate comparison results.")
        return
    try:
        comparison = json.loads(hybrid_path.read_text(encoding="utf-8"))
    except Exception:
        st.error("Hybrid evaluation output could not be read safely.")
        return
    st.caption(str(comparison.get("integrity_check_notice", "Automated comparison.")))
    for record in comparison.get("records", []):
        deterministic = record["deterministic"]
        hybrid = record["hybrid"]
        with st.expander(f"{record['number']}. {record['question']}"):
            left, right = st.columns(2)
            for column, label, item in (
                (left, "Deterministic", deterministic),
                (right, "Hybrid OpenAI", hybrid),
            ):
                column.markdown(f"**{label}**")
                column.write(f"Integrity: {'PASS' if item['citation_valid'] else 'FAIL'}")
                column.write(f"Latency: {item['latency_ms']} ms")
                column.write(f"Sources: {item['metrics']['unique_source_documents']}")
                column.write(f"Fallback: {item.get('fallback', False)}")
                usage = item.get("usage") or {}
                if usage.get("total_tokens") is not None:
                    column.write(f"Tokens: {usage['total_tokens']}")
                cost = item.get("estimated_cost_usd")
                column.write(f"Estimated cost: {'unavailable' if cost is None else f'${cost:.6f}'}")


st.title("Conservation Document Intelligence Prototype")
st.warning(RESEARCH_DISCLAIMER)
with st.expander("Privacy and safe use"):
    st.write(PRIVACY_NOTICE)
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
