"""Minimal Streamlit interface for the conservation document corpus."""

from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"


st.set_page_config(
    page_title="Conservation Document Intelligence",
    page_icon="🌿",
    layout="wide",
)

st.title("Conservation Document Intelligence Prototype")
st.write(
    "This first-stage prototype catalogs five public conservation documents "
    "and prepares them for local text extraction."
)
st.info(
    "Current scope: DOC001-DOC005. Entity extraction, embeddings, wiki pages, "
    "and chatbot functionality are not implemented yet."
)

st.subheader("Corpus")
if METADATA_PATH.exists():
    metadata = pd.read_csv(METADATA_PATH, dtype=str, keep_default_na=False)
    st.dataframe(metadata, use_container_width=True, hide_index=True)
else:
    st.error(f"Metadata file not found: {METADATA_PATH}")

