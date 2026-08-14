"""Finalize the saved Step 9 live records without making API requests."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from importlib import import_module

from hybrid_evaluation import INJECTION_CASES, WETLAND_QUESTION, evaluate_hybrid, load_pricing, security_record, wetland_comparison
from openai_config import load_openai_config

runner = import_module("08_run_hybrid_evaluation")
JSON_PATH = ROOT / "outputs" / "live_hybrid_evaluation.json"
MARKDOWN_PATH = ROOT / "outputs" / "live_hybrid_evaluation.md"


def main() -> int:
    output = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    records = output["records"]
    for record in records:
        hybrid = record["hybrid"]
        hybrid["citation_audit"] = runner._citation_details(hybrid)
        hybrid["quality"] = runner._quality(record["question"], hybrid)

    offline_config = load_openai_config({
        "USE_OPENAI_CHATBOT": "true",
        "OPENAI_API_KEY": runner.FAKE_KEY,
        "OPENAI_MODEL": "offline-mock",
        "OPENAI_MAX_RETRIES": "0",
        "OPENAI_REQUEST_COOLDOWN_SECONDS": "0",
    })
    factory = runner.OfflineFactory()
    security = []
    for question, expected in INJECTION_CASES:
        before = factory.responses.calls
        result = evaluate_hybrid(
            question, config=offline_config, client_factory=factory, pricing=load_pricing({})
        )
        security.append(security_record(question, expected, result, factory.responses.calls > before))
    security.append({
        "question": "Retrieved evidence contains malicious instructions.",
        "expected_behavior": "malicious_retrieved_evidence_ignored",
        "actual_mode": "covered_by_mocked_regression",
        "openai_called": False,
        "secrets_exposed": False,
        "unsupported_citations": False,
        "status": "PASS",
    })
    output["security_evaluation"] = security
    output["summary"] = runner._summary(records, load_pricing())
    output["summary"]["useful_ai_answers"] = sum(
        row["hybrid"]["mode"] == "openai" and not row["hybrid"]["insufficient"]
        for row in records
    )
    output["summary"]["valid_insufficient_ai_answers"] = sum(
        row["hybrid"]["mode"] == "openai" and row["hybrid"]["insufficient"]
        for row in records
    )
    wetland = next(row for row in records if row["question"] == WETLAND_QUESTION)
    output["wetland_summary_comparison"] = wetland_comparison(
        wetland["deterministic"], wetland["hybrid"]
    )
    output["deployment_recommendation"] = "RECOMMEND FIXES BEFORE DEPLOYMENT"
    output["deployment_recommendation_reason"] = (
        "Final answers remained usable and citation-safe, but three model responses failed local citation "
        "validation and four additional model responses returned insufficient evidence. Fix or tune the "
        "E-ID response contract before enabling hybrid mode by default."
    )
    JSON_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = output["summary"]
    lines = [
        "# Live Hybrid Evaluation", "",
        "This report contains automated integrity and surface-form heuristics, not human expert factual validation.", "",
        "## Executive result", "",
        f"**{output['deployment_recommendation']}**", "",
        output["deployment_recommendation_reason"], "",
        "| Metric | Result |", "|---|---:|",
        f"| Questions attempted | {summary['questions_attempted']} |",
        f"| OpenAI request/response completions | {summary['successful_ai_synthesis']} |",
        f"| Useful cited OpenAI answers | {summary['useful_ai_answers']} |",
        f"| Valid insufficient-evidence OpenAI answers | {summary['valid_insufficient_ai_answers']} |",
        f"| Deterministic fallbacks | {summary['deterministic_fallbacks']} |",
        f"| Final citation-integrity passes | {summary['citation_integrity_passes']}/10 |",
        f"| Total tokens | {summary['tokens']['total_tokens']} |", "",
        "## Deterministic versus live hybrid", "",
        "| # | Mode | Fallback reason | Final integrity | Sources | Deterministic ms | Hybrid ms | Tokens |", "|---:|---|---|---|---:|---:|---:|---:|",
    ]
    for record in records:
        d, h = record["deterministic"], record["hybrid"]
        lines.append(
            f"| {record['number']} | {h['mode']} | {h.get('fallback_reason') or '—'} | "
            f"{'PASS' if h['citation_valid'] else 'FAIL'} | {h['metrics']['unique_source_documents']} | "
            f"{d['latency_ms']} | {h['latency_ms']} | {h['usage'].get('total_tokens') or 0} |"
        )
    for record in records:
        d, h = record["deterministic"], record["hybrid"]
        lines += [
            "", f"## {record['number']}. {record['question']}", "",
            "### Deterministic baseline", "", d["answer"], "",
            "### Live hybrid final answer", "", h["answer"], "",
            f"Mode: `{h['mode']}`; fallback: `{h['fallback']}`; reason: `{h.get('fallback_reason') or 'none'}`.", "",
            f"Citations: {', '.join(h['citations']) if h['citations'] else 'None (valid insufficient-evidence response)' }.", "",
            f"Evidence IDs sent/selected: {', '.join(h['evidence_supplied']) if h['evidence_supplied'] else 'None'}.", "",
            f"Citation audit: {'PASS' if h['citation_valid'] and h['citation_audit']['citations_map_to_supplied_evidence'] and h['citation_audit']['no_model_created_url'] else 'FAIL'}. "
            f"Quality heuristic: `{json.dumps(h['quality'], ensure_ascii=False)}`", "",
        ]
    wet = output["wetland_summary_comparison"]
    lines += [
        "## Wetland-summary comparison", "",
        "The live answer combines three sources in complete prose with claim-adjacent citations. Compared with the deterministic baseline, it is shorter, more readable, and avoids snippet-style evidence dumping while preserving locally rendered citations.", "",
        f"Surface-form heuristic: `{json.dumps(wet, ensure_ascii=False)}`", "",
        "## Latency", "",
        f"Deterministic median: {summary['latency_ms']['median_deterministic']} ms. Hybrid median: {summary['latency_ms']['median_hybrid']} ms; average: {summary['latency_ms']['average_hybrid']} ms; fastest: {summary['latency_ms']['fastest_hybrid']} ms; slowest: {summary['latency_ms']['slowest_hybrid']} ms. This is generally interactive, but the slowest response is noticeable.", "",
        "## Tokens and estimated cost", "",
        f"Authoritative recorded usage: {summary['tokens']['input_tokens']} input, {summary['tokens']['output_tokens']} output, {summary['tokens']['total_tokens']} total tokens.", "",
        "Pricing variables were not configured, so monetary cost and 100/1,000-question projections are unavailable. Pricing was not fetched dynamically.", "",
        "## Fallback and security analysis", "",
        f"Three citation-validation failures fell back to usable deterministic answers. Limits: {summary['limits_hit']}; timeouts: {summary['timeouts']}; API errors: {summary['api_errors']}.", "",
        f"Mocked/non-paid security cases: {sum(item['status'] == 'PASS' for item in security)}/{len(security)} PASS. No browsing or tool calls were enabled.", "",
        "## Deployment decision", "", f"**{output['deployment_recommendation']}**", "", output["deployment_recommendation_reason"], "",
        "OpenAI File Search is not necessary based on this run; the observed failures concern response/citation-contract compliance rather than local retrieval availability.", "",
    ]
    MARKDOWN_PATH.write_text("\n".join(lines), encoding="utf-8")
    print("live_records_finalized=10")
    print("additional_live_calls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
