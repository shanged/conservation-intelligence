"""Add the Step 9.5 v1/v2 comparison without making API requests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "live_hybrid_evaluation.json"
V2_PATH = ROOT / "outputs" / "live_hybrid_evaluation_v2.json"
MOCK_V2_PATH = ROOT / "outputs" / "hybrid_evaluation_v2.json"
REPORT_PATH = ROOT / "outputs" / "live_hybrid_evaluation_v2.md"


def main() -> int:
    v1 = json.loads(V1_PATH.read_text(encoding="utf-8"))
    v2 = json.loads(V2_PATH.read_text(encoding="utf-8"))
    mocked = json.loads(MOCK_V2_PATH.read_text(encoding="utf-8"))
    before = {
        "useful_openai_answers": 2,
        "valid_insufficient_openai_answers": 5,
        "citation_validation_fallbacks": 3,
        "final_citation_integrity": "10/10",
        "total_tokens": v1["summary"]["tokens"]["total_tokens"],
        "average_latency_ms": v1["summary"]["latency_ms"]["average_hybrid"],
        "median_latency_ms": v1["summary"]["latency_ms"]["median_hybrid"],
    }
    summary = v2["summary"]
    after = {
        "useful_openai_answers": summary["useful_ai_answers"],
        "valid_insufficient_openai_answers": summary["valid_insufficient_ai_answers"],
        "intentional_deterministic_local_routes": summary["deterministic_local_routes"],
        "citation_validation_fallbacks": summary["failed_citation_validation"],
        "final_citation_integrity": f"{summary['citation_integrity_passes']}/10",
        "total_tokens": summary["tokens"]["total_tokens"],
        "average_latency_ms": summary["latency_ms"]["average_hybrid"],
        "median_latency_ms": summary["latency_ms"]["median_hybrid"],
        "repair_attempts": summary["citation_repair_attempts"],
        "repair_tokens": summary["repair_input_tokens"] + summary["repair_output_tokens"],
    }
    v2["before_after"] = {"v1": before, "v2": after}
    v2["security_evaluation"] = mocked["security_evaluation"]
    v2["deployment_recommendation"] = "RECOMMEND HYBRID MODE FOR DEPLOYMENT"
    v2["deployment_recommendation_reason"] = (
        "Use selective hybrid routing: seven exact inventory/aggregate questions stay local, two synthesis "
        "questions produced useful validated OpenAI answers, and the remaining synthesis failure returned a "
        "usable deterministic fallback. Final citation integrity stayed 10/10 and unnecessary insufficient-evidence "
        "answers fell from five to zero."
    )
    v2["file_search_necessary"] = False
    V2_PATH.write_text(json.dumps(v2, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Live Hybrid Evaluation V2 — Step 9.5", "",
        "Automated integrity and surface-form judgments in this report are not human expert factual validation.", "",
        "## Diagnostic and design result", "",
        "V1 failures came from applying synthesis to structured inventories/aggregates, an overly conservative partial-evidence policy, and inconsistent E-ID formatting. V2 keeps seven exact/list questions local and reserves OpenAI for relationship and summary synthesis.", "",
        "| Metric | V1 | V2 |", "|---|---:|---:|",
        f"| Useful OpenAI answers | {before['useful_openai_answers']} | {after['useful_openai_answers']} |",
        f"| Valid but unnecessary insufficient answers | {before['valid_insufficient_openai_answers']} | {after['valid_insufficient_openai_answers']} |",
        f"| Intentional local routes | 0 | {after['intentional_deterministic_local_routes']} |",
        f"| Citation-validation fallbacks | {before['citation_validation_fallbacks']} | {after['citation_validation_fallbacks']} |",
        f"| Final citation integrity | {before['final_citation_integrity']} | {after['final_citation_integrity']} |",
        f"| Total tokens | {before['total_tokens']} | {after['total_tokens']} |", "",
        "## Per-question comparison", "",
        "| # | Question | V1 mode | V2 mode | V2 result | V2 ms | V2 tokens | Repair |", "|---:|---|---|---|---|---:|---:|---|",
    ]
    for old, new in zip(v1["records"], v2["records"]):
        h = new["hybrid"]
        result = "useful answer" if not h["insufficient"] else "insufficient"
        if h["fallback"]:
            result = "usable fallback"
        lines.append(
            f"| {new['number']} | {new['question']} | {old['hybrid']['mode']} | {h['mode']} | {result} | "
            f"{h['latency_ms']} | {h['usage'].get('total_tokens') or 0} | {'yes' if h.get('citation_repair_attempted') else 'no'} |"
        )
    for record in v2["records"]:
        h = record["hybrid"]
        lines += [
            "", f"## {record['number']}. {record['question']}", "", h["answer"], "",
            f"Mode: `{h['mode']}`. Final citation validation: `{'PASS' if h['citation_valid'] else 'FAIL'}`. "
            f"Fallback reason: `{h.get('fallback_reason') or 'none'}`. Evidence IDs: "
            f"`{', '.join(h.get('evidence_supplied', [])) or 'none'}`.", "",
        ]
    lines += [
        "## Citation repair", "",
        f"Repair attempts: {after['repair_attempts']}. One repaired answer passed; one remained invalid and fell back. Repair overhead was {after['repair_tokens']} tokens ({summary['repair_input_tokens']} input and {summary['repair_output_tokens']} output). No DOC citation, URL, unknown E-ID, unsupported aggregate claim, or unsafe output is repair-eligible.", "",
        "## Latency and cost", "",
        f"V2 median final-response latency was {after['median_latency_ms']} ms and average was {after['average_latency_ms']} ms. Fastest: {summary['latency_ms']['fastest_hybrid']} ms; slowest: {summary['latency_ms']['slowest_hybrid']} ms. The slowest response included a repair attempt and is noticeable in an interactive demo.", "",
        f"V2 usage was {summary['tokens']['input_tokens']} input, {summary['tokens']['output_tokens']} output, and {summary['tokens']['total_tokens']} total tokens. Pricing variables were not configured, so monetary totals and projections are unavailable; pricing was not fetched dynamically.", "",
        "## Mocked and security results", "",
        f"Mocked v2: {mocked['summary']['useful_ai_answers']} useful syntheses, {mocked['summary']['deterministic_local_routes']} local routes, {mocked['summary']['deterministic_fallbacks']} fallbacks, and {mocked['summary']['citation_integrity_passes']}/10 citation integrity. Security: {sum(item['status'] == 'PASS' for item in mocked['security_evaluation'])}/{len(mocked['security_evaluation'])} PASS with no paid adversarial calls.", "",
        "## Recommendation", "", f"**{v2['deployment_recommendation']}**", "", v2["deployment_recommendation_reason"], "",
        "OpenAI File Search does not appear necessary. Local MiniLM/Chroma retrieval supplied adequate evidence; the remaining failure is response-contract compliance and is contained by deterministic fallback.", "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print("v2_comparison_finalized=true")
    print("additional_live_calls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
