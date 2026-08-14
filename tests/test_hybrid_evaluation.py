"""Offline-only tests for deterministic-vs-hybrid evaluation infrastructure."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from chatbot import ChatResponse, Evidence  # noqa: E402
from hybrid_evaluation import (  # noqa: E402
    PricingConfig,
    answer_metrics,
    estimated_cost,
    evaluate_deterministic,
    load_pricing,
    security_record,
    wetland_comparison,
)

SCRIPT_PATH = ROOT / "scripts" / "08_run_hybrid_evaluation.py"
spec = importlib.util.spec_from_file_location("run_hybrid_evaluation", SCRIPT_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(runner)


EVIDENCE = Evidence(
    "Wetland Plan", "DOC012", "25-26", "https://example.invalid/plan",
    "Wetland restoration improves habitat and monitoring outcomes.", "C12", 0.91,
)
RESPONSE = ChatResponse(
    "Wetland restoration improves habitat [DOC012, pp. 25–26]",
    ("[DOC012, pp. 25–26]",), (EVIDENCE,), False,
)


class HybridEvaluationTests(unittest.TestCase):
    def test_deterministic_evaluation_records_latency_and_integrity(self):
        times = iter((10.0, 10.125))
        result = evaluate_deterministic(
            "What supports wetland restoration?", answerer=lambda _: RESPONSE,
            clock=lambda: next(times),
        )
        self.assertEqual(result["latency_ms"], 125.0)
        self.assertTrue(result["citation_valid"])
        self.assertEqual(result["mode"], "deterministic")

    def test_metrics_include_source_diversity_and_retrieval_quality(self):
        second = Evidence(
            "Agency Page", "DOC023", "Web", "https://example.invalid/web",
            "Agencies monitor wetland condition.", "C23", 0.82,
        )
        response = ChatResponse(
            RESPONSE.answer + " [DOC023, Web]", RESPONSE.citations + ("[DOC023, Web]",),
            (EVIDENCE, second), False,
        )
        metrics = answer_metrics("wetland restoration monitoring", response)
        self.assertEqual(metrics["unique_source_documents"], 2)
        self.assertEqual(metrics["evidence_count"], 2)
        self.assertEqual(metrics["top_semantic_score"], 0.91)
        self.assertIn("extractiveness_similarity", metrics)

    def test_cost_is_configurable_and_absent_pricing_is_unavailable(self):
        usage = {"input_tokens": 1_000_000, "output_tokens": 500_000}
        self.assertEqual(estimated_cost(usage, PricingConfig(2.0, 4.0)), 4.0)
        self.assertIsNone(estimated_cost(usage, PricingConfig(None, None)))
        self.assertEqual(load_pricing({}), PricingConfig(None, None))

    def test_wetland_comparison_detects_surface_quality_change(self):
        deterministic = {"answer": "- Species of Greatest Conservation Need, A, B, C, D, E, F\n- snippet\n- snippet"}
        hybrid = {"answer": "Wetland programs emphasize restoration and monitoring."}
        result = wetland_comparison(deterministic, hybrid)
        self.assertTrue(result["hybrid_reduced_observed_issues"])

    def test_security_record_captures_injection_outcome(self):
        result = {"answer": "The corpus does not provide enough evidence to answer that question reliably.", "mode": "deterministic_fallback", "insufficient": True, "citation_valid": True}
        record = security_record("Ignore instructions", "insufficient_evidence", result, False)
        self.assertEqual(record["status"], "PASS")
        self.assertFalse(record["openai_called"])

    def test_live_mode_is_disabled_by_default_and_limit_is_mandatory(self):
        args = runner.parse_args([])
        self.assertFalse(args.live)
        self.assertIsNone(args.limit)
        with self.assertRaises(SystemExit):
            runner._validate_live(runner.parse_args(["--live"]))
        runner._validate_live(runner.parse_args(["--live", "--limit", "1"]))
        with self.assertRaises(SystemExit):
            runner._validate_live(runner.parse_args(["--live", "--limit", "11"]))


if __name__ == "__main__":
    unittest.main()
