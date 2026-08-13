"""Open immutable runtime SQLite artifacts without permitting writes."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_readonly(path: str | Path) -> sqlite3.Connection:
    """Return a read-only immutable SQLite connection for a precomputed file."""
    database = Path(path).resolve()
    uri = f"{database.as_uri()}?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)
