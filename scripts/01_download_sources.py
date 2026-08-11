"""Download PDF sources and extract readable text from web sources.

Metadata is the source of truth.  A final/direct URL recorded in a row's notes
is used for transparent representative selections while the original ``url``
column remains unchanged.  Each source fails independently and writes through
a temporary file so partial downloads are never mistaken for usable sources.
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "data" / "metadata.csv"
USER_AGENT = "conservation-document-intelligence-prototype/0.2"
FINAL_URL = re.compile(r"final URL\s+(https?://\S+)", re.I)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=float, default=90)
    return parser.parse_args()


def load_rows() -> tuple[list[dict[str, str]], list[str]]:
    with METADATA.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def save_rows(rows: list[dict[str, str]], fields: list[str]) -> None:
    with METADATA.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def local_path(value: str) -> Path:
    path = (ROOT / value).resolve()
    path.relative_to(ROOT)  # Reject paths outside this repository.
    return path


def request_url(row: dict[str, str]) -> str:
    match = FINAL_URL.search(row.get("notes", ""))
    return match.group(1).rstrip(".;") if match else row["url"]


def readable_html(content: bytes) -> str:
    """Return main/article text while removing obvious web boilerplate."""
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "form", "nav", "footer", "header", "aside"]):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    lines = [" ".join(s.split()) for s in root.get_text("\n").splitlines()]
    lines = [line for line in lines if line and not re.search(r"^(accept|manage) (all )?cookies?$", line, re.I)]
    return "\n\n".join(lines).strip() + "\n"


def fetch(row: dict[str, str], destination: Path, timeout: float) -> None:
    url = request_url(row)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/pdf,text/html,*/*"}
    with requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        body = response.content
    if destination.suffix.lower() == ".pdf":
        if not body.startswith(b"%PDF-"):
            raise ValueError("response is not a PDF")
        payload = body
    else:
        text = readable_html(body)
        if len(text) < 200:
            raise ValueError(f"webpage extraction produced only {len(text)} characters")
        payload = text.encode("utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", delete=False) as tmp:
        tmp.write(payload)
        temporary = Path(tmp.name)
    shutil.move(str(temporary), destination)


def main() -> int:
    args = arguments()
    rows, fields = load_rows()
    failures = 0
    for row in rows:
        doc_id = row["doc_id"]
        destination = local_path(row["local_file"])
        if args.dry_run:
            print(f"PLAN {doc_id}: {request_url(row)} -> {destination.name}")
            continue
        if destination.exists() and not args.overwrite:
            print(f"SKIP {doc_id}: existing file retained")
            if row["notes"].startswith("Substituted"):
                row["download_status"] = "substituted"
            elif "Representative selected:" in row["notes"]:
                row["download_status"] = "representative document selected"
            elif destination.suffix.lower() == ".txt":
                row["download_status"] = "saved as webpage text"
            else:
                row["download_status"] = "downloaded"
            continue
        try:
            fetch(row, destination, args.timeout)
        except Exception as exc:  # One remote failure must not stop the corpus.
            failures += 1
            row["download_status"] = "failed"
            row["notes"] = f"{row['notes']} Failure: {type(exc).__name__}: {exc}".strip()
            print(f"FAILED {doc_id}: {exc}", file=sys.stderr)
        else:
            if row["notes"].startswith("Substituted"):
                row["download_status"] = "substituted"
            elif "Representative selected:" in row["notes"]:
                row["download_status"] = "representative document selected"
            elif destination.suffix.lower() == ".txt":
                row["download_status"] = "saved as webpage text"
            else:
                row["download_status"] = "downloaded"
            print(f"SAVED {doc_id}: {destination.name}")
    if not args.dry_run:
        save_rows(rows, fields)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
