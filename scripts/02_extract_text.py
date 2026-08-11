"""Create processed text from every downloaded PDF or saved webpage text.

PDFs retain exact ``--- Page N ---`` boundaries.  Web text is copied without
invented page numbers; downstream chunking labels it consistently as ``Web``.
Each source is independent so one malformed input does not stop the run.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


def extract_pdf(path: Path) -> str:
    sections = []
    for number, page in enumerate(PdfReader(path).pages, 1):
        sections.append(f"--- Page {number} ---\n{(page.extract_text() or '').strip()}")
    return "\n\n".join(sections).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    failures = 0
    sources = sorted(list(RAW.glob("DOC*.pdf")) + list(RAW.glob("DOC*.txt")))
    for source in sources:
        target = PROCESSED / f"{source.stem.upper()}.txt"
        if target.exists() and not args.overwrite:
            print(f"SKIP {source.stem}: processed file exists")
            continue
        try:
            text = extract_pdf(source) if source.suffix.lower() == ".pdf" else source.read_text(encoding="utf-8")
            if not text.strip():
                raise ValueError("no readable text")
            target.write_text(text, encoding="utf-8")
        except Exception as exc:
            failures += 1
            print(f"FAILED {source.name}: {exc}", file=sys.stderr)
        else:
            print(f"SAVED {target.name}: {len(text):,} characters")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
