"""
ethics_rag.py
Main RAG pipeline for AI Ethics Assessment Framework.

Flow:
  Research proposal text
       ↓
  Extract risk keywords
       ↓
  Map keywords → Charter articles
       ↓
  SPARQL queries → GraphDB (local)
       ↓
  Build grounded prompt
       ↓
  Ollama LLM → structured assessment
       ↓
  Save JSON output

Author: Navina Ganapathy Amuthan
Trinity College Dublin — MSc Dissertation 2026
"""

import json
import os
from datetime import datetime

from sparql_retrieval import (
    test_connection as test_sparql,
    retrieve_all_for_proposal,
)
from llm_caller import (
    test_connection as test_llm,
    call_llm,
    parse_json_response,
)
from prompt_builder import (
    build_context,
    build_assessment_prompt,
    build_llm_only_prompt,
    DEFAULT_MAX_REQUIREMENTS,
    requirement_text_char_limit,
)

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOW_KEYWORD_THRESHOLD = 3
LOW_REQUIREMENT_THRESHOLD = 50


def _confidence_flag(keywords: list, reqs: list) -> str:
    """Flag retrieval confidence based on keyword and requirement counts."""
    if len(keywords) < LOW_KEYWORD_THRESHOLD or len(reqs) < LOW_REQUIREMENT_THRESHOLD:
        return "LOW"
    return "HIGH"


def _enrich_assessment_metadata(
    assessment: dict,
    keywords: list,
    reqs: list,
    incidents: list,
    rights: list,
) -> dict:
    """Add confidence flag and retrieval/citation metadata to assessment."""
    if "parse_error" in assessment:
        return assessment

    assessment["confidence_flag"] = _confidence_flag(keywords, reqs)

    cited_ids = [
        r.get("requirement_id", "")
        for r in assessment.get("applicable_requirements", [])
    ]

    assessment["_retrieval_metadata"] = {
        "keywords": keywords,
        "rights_matched": len(rights),
        "requirements_retrieved": len(reqs),
        "incidents_retrieved": len(incidents),
        "requirements_sample": [r["id"] for r in reqs[:10]],
        "requirements_retrieved_ids": [r["id"] for r in reqs],
        "requirements_cited": cited_ids,
        "incidents_sample": [i["id"] for i in incidents[:5]],
    }
    return assessment


def assess_proposal(
    proposal: str,
    proposal_id: str = None,
    mode: str = "full",
    backend: str = "ollama",
    model: str = None,
    max_requirements: int = None,
    llm_call=None,
    output_dir: str = None,
) -> dict:
    """
    Run the full ethics assessment pipeline on a proposal.

    Args:
        proposal: Plain text research proposal
        proposal_id: Optional ID for filename (e.g. "P01")
        mode: "full" (KG + LLM), "llm_only" (no KG), "kg_only" (no LLM)
        backend: LLM backend — "ollama" or "groq"
        model: Optional model override for the selected backend
        max_requirements: Cap requirements included in LLM context (default: 25)
        llm_call: Optional callable override (default: call_llm with backend/model)
        output_dir: Directory for JSON output (default: outputs/)

    Returns:
        dict with assessment results + metadata
    """
    if llm_call is None:
        llm_call = lambda prompt: call_llm(prompt, backend=backend, model=model)
    save_dir = output_dir or OUTPUT_DIR
    os.makedirs(save_dir, exist_ok=True)
    print(f"\n{'=' * 60}")
    print(f"ASSESSING PROPOSAL: {proposal_id or 'unnamed'}")
    context_max_requirements = (
        max_requirements if max_requirements is not None else DEFAULT_MAX_REQUIREMENTS
    )
    print(
        f"Mode: {mode} | Backend: {backend}"
        + (f" | Model: {model}" if model else "")
        + f" | Context reqs: {context_max_requirements}"
    )
    print(f"{'=' * 60}")

    result_metadata = {
        "proposal_id": proposal_id,
        "mode": mode,
        "llm_backend": backend,
        "timestamp": datetime.now().isoformat(),
        "proposal_text": proposal,
        "context_max_requirements": context_max_requirements,
    }
    if model:
        result_metadata["llm_model"] = model

    # ── MODE: KG ONLY ──
    if mode == "kg_only":
        print("\n[Step 1] Extracting keywords...")
        reqs, incidents, rights, keywords = retrieve_all_for_proposal(proposal)
        print(f"  Keywords: {keywords}")
        print(f"  Rights matched: {len(rights)}")
        print(f"  Requirements retrieved: {len(reqs)}")
        print(f"  Incidents retrieved: {len(incidents)}")

        result_metadata["keywords"] = keywords
        result_metadata["matched_rights"] = rights
        result_metadata["retrieved_requirements"] = reqs
        result_metadata["retrieved_incidents"] = incidents
        result_metadata["assessment"] = {
            "note": "KG-only mode — no LLM interpretation",
            "requirements_count": len(reqs),
            "incidents_count": len(incidents),
            "rights_count": len(rights),
            "confidence_flag": _confidence_flag(keywords, reqs),
            "_retrieval_metadata": {
                "keywords": keywords,
                "rights_matched": len(rights),
                "requirements_retrieved": len(reqs),
                "incidents_retrieved": len(incidents),
                "requirements_sample": [r["id"] for r in reqs[:10]],
                "requirements_retrieved_ids": [r["id"] for r in reqs],
                "requirements_cited": [],
                "incidents_sample": [i["id"] for i in incidents[:5]],
            },
        }

        _save_output(result_metadata, proposal_id, mode, save_dir)
        return result_metadata

    # ── MODE: LLM ONLY ──
    if mode == "llm_only":
        print("\n[Step 1] Building LLM-only prompt (no KG context)...")
        prompt = build_llm_only_prompt(proposal)

        print("\n[Step 2] Calling LLM...")
        raw_response = llm_call(prompt)

        if not raw_response:
            print("  [ERROR] LLM returned empty response.")
            result_metadata["assessment"] = {"error": "LLM returned empty response"}
            _save_output(result_metadata, proposal_id, mode, save_dir)
            return result_metadata

        print("\n[Step 3] Parsing JSON response...")
        assessment = parse_json_response(raw_response)
        if "parse_error" not in assessment:
            assessment["confidence_flag"] = "LOW"

        result_metadata["keywords"] = []
        result_metadata["matched_rights"] = []
        result_metadata["retrieved_requirements"] = []
        result_metadata["retrieved_incidents"] = []
        result_metadata["assessment"] = assessment

        _save_output(result_metadata, proposal_id, mode, save_dir)
        return result_metadata

    # ── MODE: FULL PIPELINE (KG + LLM) ──
    print("\n[Step 1] Extracting keywords from proposal...")
    reqs, incidents, rights, keywords = retrieve_all_for_proposal(proposal)
    print(f"  Keywords found: {keywords}")
    print(f"  Charter rights matched: {len(rights)}")
    print(f"  Requirements retrieved: {len(reqs)}")
    print(f"  Incidents retrieved: {len(incidents)}")

    result_metadata["keywords"] = keywords
    result_metadata["matched_rights"] = rights
    result_metadata["retrieved_requirements_count"] = len(reqs)
    result_metadata["retrieved_incidents_count"] = len(incidents)

    if not reqs and not incidents:
        print("  [WARNING] No KG results retrieved. LLM will operate without grounding.")

    print("\n[Step 2] Building context from KG retrieval...")
    context = build_context(
        reqs,
        incidents,
        rights,
        max_requirements=context_max_requirements,
        total_requirements=len(reqs),
        max_requirement_text_chars=requirement_text_char_limit(context_max_requirements),
    )

    print("\n[Step 3] Building assessment prompt...")
    prompt = build_assessment_prompt(proposal, context)
    print(f"  Prompt length: {len(prompt)} characters")

    print("\n[Step 4] Calling LLM (this may take 30-60 seconds)...")
    raw_response = llm_call(prompt)

    if not raw_response:
        print("  [ERROR] LLM returned empty response.")
        result_metadata["assessment"] = {"error": "LLM returned empty response"}
        _save_output(result_metadata, proposal_id, mode, save_dir)
        return result_metadata

    print(f"  Response received: {len(raw_response)} characters")

    print("\n[Step 5] Parsing JSON response...")
    assessment = parse_json_response(raw_response)
    assessment = _enrich_assessment_metadata(
        assessment, keywords, reqs, incidents, rights
    )

    result_metadata["assessment"] = assessment

    _save_output(result_metadata, proposal_id, mode, save_dir)

    # Print summary
    print(f"\n{'─' * 60}")
    print(f"ASSESSMENT COMPLETE")
    if "parse_error" not in assessment:
        print(f"  Risk Level: {assessment.get('overall_risk_level', 'N/A')}")
        print(f"  Confidence Flag: {assessment.get('confidence_flag', 'N/A')}")
        print(f"  Risks Identified: {len(assessment.get('identified_risks', []))}")
        print(f"  Requirements Cited: {len(assessment.get('applicable_requirements', []))}")
        print(f"  Rights at Risk: {len(assessment.get('charter_rights_at_risk', []))}")
        print(f"  Precedents Cited: {len(assessment.get('historical_precedents', []))}")
        print(f"  Mitigations: {len(assessment.get('recommended_mitigations', []))}")
    else:
        print(f"  [WARNING] JSON parsing failed — raw output saved")
    print(f"{'─' * 60}")

    return result_metadata


def _save_output(
    data: dict,
    proposal_id: str = None,
    mode: str = "full",
    output_dir: str = None,
):
    """Save assessment output to JSON file."""
    save_dir = output_dir or OUTPUT_DIR
    os.makedirs(save_dir, exist_ok=True)

    if proposal_id:
        filename = f"{proposal_id}_{mode}.json"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"assessment_{timestamp}_{mode}.json"

    filepath = os.path.join(save_dir, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [SAVED] {filepath}")


# ── SELF-TEST ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("AI ETHICS ASSESSMENT FRAMEWORK — RAG PIPELINE")
    print("Navina Ganapathy Amuthan | TCD Dissertation 2026")
    print("=" * 60)

    print("\n[PREFLIGHT] Checking GraphDB connection...")
    sparql_ok = test_sparql()

    print("\n[PREFLIGHT] Checking Ollama connection...")
    llm_ok = test_llm()

    if not sparql_ok:
        print("\n[ABORT] GraphDB is not running. Start GraphDB Desktop first.")
        exit(1)

    if not llm_ok:
        print("\n[ABORT] Ollama is not running. Run: ollama serve")
        exit(1)

    print("\n[PREFLIGHT] All systems OK. Running test assessment...\n")

    test_proposal = """
    This research proposes to develop a facial recognition system for
    automated attendance tracking in university lecture halls. The system
    will capture and process biometric facial data of students without
    explicit opt-in consent, relying on implied consent through university
    enrollment terms. The system will store facial embeddings indefinitely
    and may share anonymised aggregate data with third-party education
    analytics providers. The research team has not conducted a Data
    Protection Impact Assessment.
    """

    result = assess_proposal(test_proposal, proposal_id="TEST_001", mode="full")
    print("\n\nFull assessment saved to outputs/TEST_001_full.json")
