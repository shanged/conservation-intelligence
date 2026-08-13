"""Resolve immutable runtime artifacts without invoking the build pipeline."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_ARTIFACT_ROOT = PROJECT_ROOT / "deployment_artifacts"
LOCAL_ARTIFACT_ROOT = PROJECT_ROOT
ARTIFACT_ROOT_ENV = "CONSERVATION_ARTIFACT_ROOT"


def _local_model_path() -> Path:
    snapshots = (
        LOCAL_ARTIFACT_ROOT
        / "db"
        / "vector_index"
        / "model_cache"
        / "models--sentence-transformers--all-MiniLM-L6-v2"
        / "snapshots"
    )
    if snapshots.exists():
        candidates = sorted(path for path in snapshots.iterdir() if path.is_dir())
        if candidates:
            return candidates[-1]
    return snapshots / "MISSING_MODEL_SNAPSHOT"


def _has_core_artifacts(root: Path) -> bool:
    return (
        (root / "db" / "conservation.db").is_file()
        and (root / "db" / "vector_index" / "chroma.sqlite3").is_file()
    )


def select_artifact_root() -> Path:
    """Prefer an explicit root, then local build outputs, then packaged assets."""
    configured = os.getenv(ARTIFACT_ROOT_ENV, "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    if _has_core_artifacts(LOCAL_ARTIFACT_ROOT):
        return LOCAL_ARTIFACT_ROOT
    return DEPLOYMENT_ARTIFACT_ROOT


ARTIFACT_ROOT = select_artifact_root()
DATABASE_PATH = ARTIFACT_ROOT / "db" / "conservation.db"
VECTOR_INDEX_DIR = ARTIFACT_ROOT / "db" / "vector_index"
MODEL_PATH = (
    _local_model_path()
    if ARTIFACT_ROOT == LOCAL_ARTIFACT_ROOT
    else ARTIFACT_ROOT / "model" / "all-MiniLM-L6-v2"
)
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"
WIKI_ROOT = PROJECT_ROOT / "wiki"
EVALUATION_PATH = PROJECT_ROOT / "outputs" / "demo_answers.json"


def missing_runtime_artifacts() -> list[Path]:
    """Return required runtime paths that are absent or incomplete."""
    required_files = (
        METADATA_PATH,
        DATABASE_PATH,
        VECTOR_INDEX_DIR / "chroma.sqlite3",
        MODEL_PATH / "modules.json",
        MODEL_PATH / "model.safetensors",
        EVALUATION_PATH,
    )
    missing = [path for path in required_files if not path.is_file()]
    if not WIKI_ROOT.is_dir() or not any(WIKI_ROOT.rglob("*.md")):
        missing.append(WIKI_ROOT)
    return missing


def runtime_configuration_error() -> str | None:
    """Describe missing precomputed artifacts without suggesting a rebuild."""
    missing = missing_runtime_artifacts()
    if not missing:
        return None
    paths = "\n".join(f"- {path}" for path in missing)
    return (
        "Required precomputed runtime artifacts are missing. The application "
        "will not rebuild them automatically. Configure "
        f"{ARTIFACT_ROOT_ENV} to a complete artifact package or restore:\n{paths}"
    )
