FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    TOKENIZERS_PARALLELISM=false \
    HOME=/tmp/app-home

WORKDIR /app

COPY requirements.runtime.txt ./
RUN python -m pip install --upgrade pip && \
    python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.13.0 && \
    python -m pip install -r requirements.runtime.txt

RUN groupadd --system app && useradd --system --gid app --home-dir /tmp/app-home app && \
    mkdir -p /tmp/app-home && chown app:app /tmp/app-home

COPY app.py ./
COPY .streamlit/config.toml ./.streamlit/config.toml
COPY scripts/chatbot.py scripts/citation_validation.py scripts/openai_chatbot.py scripts/openai_config.py scripts/request_controls.py scripts/runtime_artifacts.py scripts/search_chunks.py scripts/semantic_search.py scripts/sqlite_readonly.py scripts/ui_safety.py ./scripts/
COPY data/metadata.csv ./data/metadata.csv
COPY wiki/ ./wiki/
COPY outputs/demo_answers.json outputs/hybrid_evaluation.json ./outputs/
COPY deployment_artifacts/ ./deployment_artifacts/

USER app

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/_stcore/health', timeout=4).read()"

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true"]
