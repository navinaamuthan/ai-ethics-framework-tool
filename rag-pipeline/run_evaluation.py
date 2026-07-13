"""
run_evaluation.py
Runs all 20 synthetic proposals through the RAG pipeline.
Saves all outputs to a configurable output directory.

Usage:
  python3 run_evaluation.py
  python3 run_evaluation.py P01 P03 P07
  python3 run_evaluation.py --quick
  python3 run_evaluation.py --backend groq --model llama-3.3-70b-versatile --output-dir outputs_llama70b
  python3 run_evaluation.py --backend groq --model qwen/qwen3-32b --output-dir outputs_qwen27b P01

Author: Navina Ganapathy Amuthan
Trinity College Dublin — MSc Dissertation 2026
"""

import argparse
import json
import os
import time
from datetime import datetime

from sparql_retrieval import test_connection as test_sparql
from llm_caller import test_connection as test_ollama, test_groq_connection
from ethics_rag import assess_proposal
from synthetic_proposals import PROPOSALS


def run_evaluation(
    proposal_ids: list = None,
    backend: str = "ollama",
    model: str = None,
    output_dir: str = "outputs",
    max_requirements: int = None,
):
    """Run evaluation on selected or all proposals."""
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("AI ETHICS ASSESSMENT FRAMEWORK — EVALUATION RUN")
    print(f"Backend: {backend}" + (f" | Model: {model}" if model else ""))
    if max_requirements is not None:
        print(f"Max requirements in context: {max_requirements}")
    print(f"Output dir: {output_dir}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    print("\n[PREFLIGHT] Checking systems...")
    if not test_sparql():
        print("[ABORT] GraphDB not running. Start it first.")
        return

    if backend == "groq":
        if not test_groq_connection(model):
            print("[ABORT] Groq API not available. Check GROQ_API_KEY.")
            return
    elif not test_ollama(model):
        print("[ABORT] Ollama not running. Run: ollama serve")
        return

    if proposal_ids:
        selected = [p for p in PROPOSALS if p["id"] in proposal_ids]
    else:
        selected = PROPOSALS

    print(f"\n[INFO] Running {len(selected)} proposals through full pipeline...")
    print(f"[INFO] Outputs will be saved to {output_dir}/\n")

    results_summary = []
    for i, proposal in enumerate(selected):
        print(f"\n{'#' * 60}")
        print(f"PROPOSAL {i + 1}/{len(selected)}: {proposal['id']} — {proposal['title']}")
        print(f"Expected risk level: {proposal['risk_level']}")
        print(f"{'#' * 60}")

        result = assess_proposal(
            proposal=proposal["proposal_text"],
            proposal_id=proposal["id"],
            mode="full",
            backend=backend,
            model=model,
            max_requirements=max_requirements,
            output_dir=output_dir,
        )

        if backend == "groq" and i < len(selected) - 1:
            time.sleep(15)

        assessment = result.get("assessment", {})
        if "parse_error" not in assessment:
            predicted_risk = assessment.get("overall_risk_level", "N/A")
            match = (
                "MATCH"
                if predicted_risk.lower() == proposal["risk_level"].lower()
                else "MISMATCH"
            )
            results_summary.append({
                "id": proposal["id"],
                "title": proposal["title"],
                "expected_risk": proposal["risk_level"],
                "predicted_risk": predicted_risk,
                "risk_match": match,
                "confidence_flag": assessment.get("confidence_flag", "N/A"),
                "requirements_cited": len(assessment.get("applicable_requirements", [])),
                "rights_flagged": len(assessment.get("charter_rights_at_risk", [])),
                "precedents_cited": len(assessment.get("historical_precedents", [])),
                "mitigations": len(assessment.get("recommended_mitigations", [])),
            })
            print(f"\n  Expected: {proposal['risk_level']} | Predicted: {predicted_risk} | {match}")
        else:
            results_summary.append({
                "id": proposal["id"],
                "title": proposal["title"],
                "expected_risk": proposal["risk_level"],
                "predicted_risk": "PARSE_ERROR",
                "risk_match": "ERROR",
                "confidence_flag": "N/A",
                "requirements_cited": 0,
                "rights_flagged": 0,
                "precedents_cited": 0,
                "mitigations": 0,
            })

    summary_path = os.path.join(output_dir, "evaluation_summary.json")
    with open(summary_path, "w") as f:
        json.dump({
            "run_timestamp": datetime.now().isoformat(),
            "llm_backend": backend,
            "llm_model": model,
            "max_requirements": max_requirements,
            "output_dir": output_dir,
            "total_proposals": len(selected),
            "results": results_summary,
        }, f, indent=2)

    print(f"\n\n{'=' * 60}")
    print("EVALUATION COMPLETE")
    print(f"{'=' * 60}")

    print(f"\n{'ID':<6} {'Title':<45} {'Expected':<10} {'Predicted':<10} {'Match':<10}")
    print("-" * 85)
    for r in results_summary:
        print(
            f"{r['id']:<6} {r['title'][:44]:<45} {r['expected_risk']:<10} "
            f"{r['predicted_risk']:<10} {r['risk_match']:<10}"
        )

    matches = sum(1 for r in results_summary if r["risk_match"] == "MATCH")
    errors = sum(1 for r in results_summary if r["risk_match"] == "ERROR")
    total = len(results_summary)
    print(f"\nRisk Level Accuracy: {matches}/{total} ({100 * matches / total:.0f}%)")
    if errors:
        print(f"Parse Errors: {errors}/{total}")
    print(f"\nAll outputs saved to {output_dir}/")
    print(f"Summary saved to {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Run ethics RAG evaluation")
    parser.add_argument(
        "proposals",
        nargs="*",
        help="Proposal IDs to run (e.g. P01 P07). Omit to run all 20.",
    )
    parser.add_argument(
        "--backend",
        default="ollama",
        choices=["ollama", "groq"],
        help="LLM backend (default: ollama)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name override (e.g. llama-3.3-70b-versatile, qwen/qwen3-32b)",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory for JSON results (default: outputs)",
    )
    parser.add_argument(
        "--max-requirements",
        type=int,
        default=None,
        help="Cap requirements included in LLM context (default: 25)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run P01, P07, P13 only (one per risk level)",
    )
    args = parser.parse_args()

    proposal_ids = ["P01", "P07", "P13"] if args.quick else args.proposals or None
    run_evaluation(
        proposal_ids=proposal_ids,
        backend=args.backend,
        model=args.model,
        output_dir=args.output_dir,
        max_requirements=args.max_requirements,
    )


if __name__ == "__main__":
    main()
