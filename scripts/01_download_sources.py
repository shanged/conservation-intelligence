"""Download the initial DOC001-DOC005 public conservation sources.

The script treats ``data/metadata.csv`` as the source of truth. It downloads
only the five document IDs approved for the prototype's first phase, writes
each response to a temporary file first, and updates download status and notes
only after a successful validation and move.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"
INITIAL_DOC_IDS = {f"DOC{number:03d}" for number in range(1, 6)}
USER_AGENT = "conservation-document-intelligence-prototype/0.1"


def parse_args() -> argparse.Namespace:
    """Parse command-line options without performing any network activity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List planned downloads without requesting any URLs.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace local files that already exist.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds (default: 60).",
    )
    return parser.parse_args()


def read_metadata(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Return metadata rows and their original field order."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Metadata has no header: {path}")
        return list(reader), list(reader.fieldnames)


def write_metadata(
    path: Path, rows: list[dict[str, str]], fieldnames: list[str]
) -> None:
    """Rewrite metadata after statuses have been updated."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def resolve_local_path(value: str) -> Path:
    """Resolve a metadata path and ensure it stays inside the repository."""
    candidate = (PROJECT_ROOT / value).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"Local path escapes project root: {value}") from exc
    return candidate


def download_pdf(url: str, destination: Path, timeout: float) -> None:
    """Stream one PDF to disk and validate its signature before keeping it."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*"}

    with requests.get(
        url, headers=headers, stream=True, timeout=timeout, allow_redirects=True
    ) as response:
        response.raise_for_status()
        with NamedTemporaryFile(
            mode="w+b", dir=destination.parent, prefix=f".{destination.name}.", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            try:
                for chunk in response.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        temporary.write(chunk)
                temporary.flush()
                temporary.seek(0)
                if temporary.read(5) != b"%PDF-":
                    raise ValueError("response does not begin with a PDF signature")
            except Exception:
                temporary_path.unlink(missing_ok=True)
                raise

    shutil.move(str(temporary_path), destination)


def main() -> int:
    """Download approved rows and record a transparent status for each."""
    args = parse_args()
    rows, fieldnames = read_metadata(METADATA_PATH)

    unexpected = {row["doc_id"] for row in rows} - INITIAL_DOC_IDS
    if unexpected:
        raise ValueError(f"This phase does not allow document IDs: {sorted(unexpected)}")

    changed = False
    for row in rows:
        doc_id = row["doc_id"]
        destination = resolve_local_path(row["local_file"])

        if args.dry_run:
            print(f"PLAN {doc_id}: {row['url']} -> {destination}")
            continue

        if destination.exists() and not args.overwrite:
            print(f"SKIP {doc_id}: {destination} already exists")
            row["download_status"] = "downloaded"
            row["notes"] = "Existing local file retained."
            changed = True
            continue

        print(f"DOWNLOAD {doc_id}: {row['url']}")
        try:
            download_pdf(row["url"], destination, args.timeout)
        except (requests.RequestException, OSError, ValueError) as exc:
            row["download_status"] = "failed"
            row["notes"] = str(exc)
            changed = True
            print(f"FAILED {doc_id}: {exc}", file=sys.stderr)
        else:
            row["download_status"] = "downloaded"
            row["notes"] = ""
            changed = True
            print(f"SAVED {doc_id}: {destination}")

    if changed:
        write_metadata(METADATA_PATH, rows, fieldnames)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

