"""Run the ten specification questions through the production chatbot path."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from chatbot import answer_question, validate_response  # noqa: E402

QUESTIONS = ROOT / "tests" / "demo_questions.txt"
MARKDOWN = ROOT / "outputs" / "demo_answers.md"
JSON_OUTPUT = ROOT / "outputs" / "demo_answers.json"


def main() -> int:
    questions = [line.strip() for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(questions) != 10:
        raise ValueError(f"Expected exactly 10 demo questions, found {len(questions)}")
    records = []; lines = ["# Automated Heuristic Evaluation", "", "These checks validate retrieval, answer presence, and citation integrity. They are not human quality ratings.", ""]
    for number, question in enumerate(questions, 1):
        response = answer_question(question); passed, notes = validate_response(response)
        status = "PASS" if passed else "FAIL"
        record = {"number": number, "question": question, **response.to_dict(), "status": status,
                  "notes": notes or ["Answer, evidence, and citations passed automated integrity checks."]}
        records.append(record)
        lines += [f"## {number}. {question}", "", f"**Heuristic status:** {status}", "", "### Generated answer", "", response.answer, "", "### Citations", ""]
        lines.append(", ".join(response.citations) if response.citations else "None (insufficient-evidence response).")
        lines += ["", "### Retrieved evidence", ""]
        for item in response.evidence:
            lines.append(f"- **{item.title}** — {item.doc_id}, {item.page}; similarity {item.similarity:.3f}. {item.snippet}  \n  {item.source_url}")
        lines += ["", "### Notes", ""] + [f"- {note}" for note in record["notes"]] + [""]
        print(f"{number:02}. {status} | {question}")
    MARKDOWN.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    JSON_OUTPUT.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    passed_count = sum(r["status"] == "PASS" for r in records)
    print(f"Heuristic result: {passed_count}/{len(records)} passed")
    return 0 if passed_count == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
