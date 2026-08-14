"""Resolve immutable runtime artifacts without invoking the build pipeline."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_ARTIFACT_ROOT = PROJECT_ROOT / "deployment_artifacts"
LOCAL_ARTIFACT_ROOT = PROJECT_ROOT
ARTIFACT_ROOT_ENV = "CONSERVATION_ARTIFACT_ROOT"
_runtime_index_lock = threading.Lock()
_runtime_index_temp: tempfile.TemporaryDirectory[str] | None = None
_runtime_index_path: Path | None = None
_runtime_index_metrics: dict[str, float | int] | None = None


class RuntimeArtifactPreparationError(RuntimeError):
    """Raised when an immutable artifact cannot be isolated for runtime use."""


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
    return (
        "Required precomputed runtime artifacts are missing. The application "
        "will not rebuild them automatically. Configure "
        f"{ARTIFACT_ROOT_ENV} to a complete artifact package or restore the "
        "deployment artifact set."
    )


def _create_disposable_vector_index(
    source: Path,
) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    """Copy Chroma data to process-scoped writable storage, excluding caches."""
    temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        started = time.perf_counter()
        temporary = tempfile.TemporaryDirectory(prefix="conservation-chroma-")
        destination = Path(temporary.name) / "vector_index"
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns(
                "model_cache",
                "*.lock",
                "*.db-wal",
                "*.db-shm",
                "*.sqlite3-wal",
                "*.sqlite3-shm",
            ),
        )
        if not (destination / "chroma.sqlite3").is_file():
            raise FileNotFoundError("copied Chroma database is missing")
        size_bytes = sum(path.stat().st_size for path in destination.rglob("*") if path.is_file())
        global _runtime_index_metrics
        _runtime_index_metrics = {
            "copy_time_ms": round((time.perf_counter() - started) * 1000, 1),
            "size_bytes": size_bytes,
        }
        return temporary, destination
    except Exception:
        if temporary is not None:
            temporary.cleanup()
        raise RuntimeArtifactPreparationError(
            "Unable to prepare the disposable semantic-index runtime copy. "
            "The packaged index was not modified and will not be rebuilt automatically."
        ) from None


def runtime_vector_index_dir() -> Path:
    """Return a cached writable copy used for Chroma's query-time bookkeeping."""
    global _runtime_index_path, _runtime_index_temp
    if _runtime_index_path is not None:
        return _runtime_index_path
    with _runtime_index_lock:
        if _runtime_index_path is None:
            temporary, destination = _create_disposable_vector_index(VECTOR_INDEX_DIR)
            _runtime_index_temp = temporary
            _runtime_index_path = destination
    return _runtime_index_path


def runtime_vector_index_metrics() -> dict[str, float | int] | None:
    """Return non-sensitive measurements for the current disposable index copy."""
    return dict(_runtime_index_metrics) if _runtime_index_metrics is not None else None
