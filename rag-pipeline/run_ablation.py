"""
run_ablation.py
Ablation study: compares three conditions on 5 proposals.

Condition A: LLM only (no KG context)
Condition B: KG only (no LLM interpretation)
Condition C: Full pipeline (KG + LLM)

Proposals: P01 (high), P03 (high), P07 (medium), P13 (low), P17 (edge)

Author: Navina Ganapathy Amuthan
Trinity College Dublin — MSc Dissertation 2026
"""

import json
import os
from datetime import datetime

from sparql_retrieval import test_connection as test_sparql
from llm_caller import test_connection as test_llm
from ethics_rag import assess_proposal
from synthetic_proposals import PROPOSALS

OUTPUT_DIR = "outputs/ablation"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ABLATION_IDS = ["P01", "P03", "P07", "P13", "P17"]


def run_ablation():
    print("=" * 60)
    print("ABLATION STUDY")
    print("Conditions: A (LLM only) | B (KG only) | C (Full pipeline)")
    print(f"Proposals: {ABLATION_IDS}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Preflight
    print("\n[PREFLIGHT] Checking systems...")
    sparql_ok = test_sparql()
    llm_ok = test_llm()

    if not sparql_ok or not llm_ok:
        print("[ABORT] Both GraphDB and Ollama must be running.")
        return

    selected = [p for p in PROPOSALS if p["id"] in ABLATION_IDS]
    all_results = []

    for proposal in selected:
        print(f"\n\n{'#' * 60}")
        print(f"ABLATION: {proposal['id']} — {proposal['title']}")
        print(f"Expected risk: {proposal['risk_level']}")
        print(f"{'#' * 60}")

        proposal_results = {
            "id": proposal["id"],
            "title": proposal["title"],
            "expected_risk": proposal["risk_level"],
            "conditions": {}
        }

        # ── Condition A: LLM Only ──
        print(f"\n── CONDITION A: LLM ONLY ──")
        result_a = assess_proposal(
            proposal["proposal_text"],
            proposal_id=f"{proposal['id']}_ablation",
            mode="llm_only"
        )
        a = result_a.get("assessment", {})
        proposal_results["conditions"]["A_llm_only"] = {
            "risk_level": a.get("overall_risk_level", "N/A"),
            "risks_count": len(a.get("identified_risks", [])),
            "requirements_count": len(a.get("applicable_requirements", [])),
            "rights_count": len(a.get("charter_rights_at_risk", [])),
            "precedents_count": len(a.get("historical_precedents", [])),
            "has_specific_req_ids": any(
                r.get("requirement_id", "").startswith(("R", "AI", "HE", "ACM"))
                for r in a.get("applicable_requirements", [])
            ),
        }

        # ── Condition B: KG Only ──
        print(f"\n── CONDITION B: KG ONLY ──")
        result_b = assess_proposal(
            proposal["proposal_text"],
            proposal_id=f"{proposal['id']}_ablation",
            mode="kg_only"
        )
        b = result_b.get("assessment", {})
        proposal_results["conditions"]["B_kg_only"] = {
            "requirements_retrieved": b.get("requirements_count", 0),
            "incidents_retrieved": b.get("incidents_count", 0),
            "rights_matched": b.get("rights_count", 0),
        }

        # ── Condition C: Full Pipeline ──
        print(f"\n── CONDITION C: FULL PIPELINE (KG + LLM) ──")
        result_c = assess_proposal(
            proposal["proposal_text"],
            proposal_id=f"{proposal['id']}_ablation",
            mode="full"
        )
        c = result_c.get("assessment", {})
        proposal_results["conditions"]["C_full_pipeline"] = {
            "risk_level": c.get("overall_risk_level", "N/A"),
            "risks_count": len(c.get("identified_risks", [])),
            "requirements_count": len(c.get("applicable_requirements", [])),
            "rights_count": len(c.get("charter_rights_at_risk", [])),
            "precedents_count": len(c.get("historical_precedents", [])),
            "has_specific_req_ids": any(
                r.get("requirement_id", "").startswith(("R", "AI", "HE", "ACM"))
                for r in c.get("applicable_requirements", [])
            ),
            "kg_requirements_retrieved": c.get("_retrieval_metadata", {}).get("requirements_retrieved", 0),
            "kg_incidents_retrieved": c.get("_retrieval_metadata", {}).get("incidents_retrieved", 0),
        }

        all_results.append(proposal_results)

    # Save full ablation results
    ablation_path = os.path.join(OUTPUT_DIR, "ablation_results.json")
    with open(ablation_path, "w") as f:
        json.dump({
            "run_timestamp": datetime.now().isoformat(),
            "results": all_results
        }, f, indent=2)

    # Print comparison table
    print(f"\n\n{'=' * 90}")
    print("ABLATION STUDY — COMPARISON TABLE")
    print(f"{'=' * 90}")
    print(f"\n{'ID':<6} {'Risk':<8} {'Condition':<20} {'Risk Level':<12} {'Reqs':<6} {'Rights':<8} {'Incidents':<10} {'Specific IDs':<12}")
    print("-" * 90)

    for r in all_results:
        pid = r["id"]
        expected = r["expected_risk"]

        a = r["conditions"]["A_llm_only"]
        print(f"{pid:<6} {expected:<8} {'A: LLM Only':<20} {a.get('risk_level','N/A'):<12} {a['requirements_count']:<6} {a['rights_count']:<8} {a['precedents_count']:<10} {'Yes' if a['has_specific_req_ids'] else 'No':<12}")

        b = r["conditions"]["B_kg_only"]
        print(f"{'':6} {'':8} {'B: KG Only':<20} {'N/A':<12} {b['requirements_retrieved']:<6} {b['rights_matched']:<8} {b['incidents_retrieved']:<10} {'Yes':<12}")

        c = r["conditions"]["C_full_pipeline"]
        print(f"{'':6} {'':8} {'C: Full Pipeline':<20} {c.get('risk_level','N/A'):<12} {c['requirements_count']:<6} {c['rights_count']:<8} {c['precedents_count']:<10} {'Yes' if c['has_specific_req_ids'] else 'No':<12}")

        print()

    print(f"\nFull results saved to {ablation_path}")
    print(f"Individual outputs in {OUTPUT_DIR}/")


if __name__ == "__main__":
    run_ablation()
