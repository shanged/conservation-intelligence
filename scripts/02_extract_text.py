"""Extract page-marked text from every downloaded PDF in ``data/raw``.

The Milestone 1 corpus is limited to DOC001-DOC005. Each PDF is handled
independently so one missing, damaged, or otherwise unreadable document does
not prevent extraction of the remaining sources. This script does not do OCR.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INITIAL_DOC_IDS = {f"DOC{number:03d}" for number in range(1, 6)}


def parse_args() -> argparse.Namespace:
    """Parse extraction options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace extracted text files that already exist.",
    )
    return parser.parse_args()


def extract_pdf(path: Path) -> str:
    """Extract every PDF page and label it for later citation work."""
    reader = PdfReader(path)
    sections: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        sections.append(f"--- Page {page_number} ---\n{text}")
    return "\n\n".join(sections).rstrip() + "\n"


def main() -> int:
    """Extract each available initial source into a DOCxxx text file."""
    args = parse_args()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0
    sources = sorted(RAW_DIR.glob("DOC*.pdf"))

    for source in sources:
        doc_id = source.stem.upper()
        if doc_id not in INITIAL_DOC_IDS:
            print(f"SKIP {source.name}: outside Milestone 1 scope")
            continue
        destination = PROCESSED_DIR / f"{doc_id}.txt"

        if destination.exists() and not args.overwrite:
            print(f"SKIP {doc_id}: extracted text already exists: {destination}")
            continue

        try:
            text = extract_pdf(source)
            destination.write_text(text, encoding="utf-8")
        except Exception as exc:
            failures += 1
            print(f"FAILED {doc_id}: {exc}", file=sys.stderr)
        else:
            print(f"SAVED {doc_id}: {destination}")

    if not sources:
        print(f"No PDFs found in {RAW_DIR}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
