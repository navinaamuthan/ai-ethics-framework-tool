"""
AIEF — RAGAS-Style Metrics for RAG Evaluation
===============================================
Computes four standard RAG metrics without the ragas library dependency
(which requires OpenAI API keys for its internal LLM judge).

Instead, this implements the metrics directly using your existing
Groq/Ollama backend, so you stay within your existing infrastructure.

Metrics computed:
  1. Context Precision  — Are the retrieved KG results relevant to the question?
  2. Context Recall     — Does the retrieved context cover all ground truth requirements?
  3. Faithfulness       — Does the generated answer only use info from the context?
  4. Answer Relevancy   — Is the generated answer relevant to the input proposal?

Usage:
  python ragas_metrics.py --output-dir outputs_llama70b --backend groq
  python ragas_metrics.py --output-dir outputs_llama8b --backend ollama

Requires:
  - Your evaluation output JSONs in the output directory
  - ground_truth.json (generated below if missing)
  - Either Ollama running locally OR GROQ_API_KEY env var

Author: Navina Ganapathy Amuthan
Trinity College Dublin — MSc Dissertation 2026
"""

import json
import os
import sys
import re
import argparse
from pathlib import Path

# ─── CONFIGURATION ───────────────────────────────────────────

GROUND_TRUTH_FILE = "ground_truth.json"

# Ground truth: proposal ID -> expected requirements, rights, risk
# UPDATE THESE to match your actual ground truth from synthetic_proposals.json
GROUND_TRUTH_DATA = {
    "P01": {
        "risk_level": "High",
        "expected_requirements": ["R001", "R003", "R009", "R027", "R042", "R085", "AI001", "AI005", "AI012", "HE003", "HE015", "ACM001", "ACM012"],
        "expected_rights": ["Article7", "Article8", "Article21"],
        "domain": "Facial recognition in education"
    },
    "P02": {
        "risk_level": "High",
        "expected_requirements": ["R003", "R009", "R010", "R027", "R085", "AI001", "AI005", "AI012", "AI020", "HE003", "ACM001"],
        "expected_rights": ["Article6", "Article8", "Article21", "Article47"],
        "domain": "Predictive policing"
    },
    "P03": {
        "risk_level": "High",
        "expected_requirements": ["R001", "R003", "R009", "R027", "AI001", "AI005", "HE003", "HE015", "ACM001"],
        "expected_rights": ["Article2", "Article8", "Article21", "Article35"],
        "domain": "Healthcare diagnosis"
    },
    "P04": {
        "risk_level": "High",
        "expected_requirements": ["R003", "R027", "R085", "AI001", "AI005", "AI012", "HE003", "ACM001", "ACM012"],
        "expected_rights": ["Article15", "Article21", "Article23"],
        "domain": "Automated hiring"
    },
    "P05": {
        "risk_level": "High",
        "expected_requirements": ["R003", "R009", "R010", "R027", "AI001", "AI005", "AI020", "HE003", "ACM001"],
        "expected_rights": ["Article1", "Article7", "Article8", "Article21"],
        "domain": "Social credit scoring"
    },
    "P06": {
        "risk_level": "High",
        "expected_requirements": ["R003", "R009", "R027", "R042", "AI001", "AI005", "HE003", "HE015", "ACM001"],
        "expected_rights": ["Article7", "Article8", "Article24"],
        "domain": "Child behaviour monitoring"
    },
    "P07": {
        "risk_level": "High",
        "expected_requirements": ["R003", "R010", "AI001", "AI020", "HE003", "HE041", "ACM001"],
        "expected_rights": ["Article2", "Article6"],
        "domain": "Autonomous weapons"
    },
    "P08": {
        "risk_level": "High",
        "expected_requirements": ["R003", "R009", "R010", "R027", "AI001", "AI005", "AI012", "HE003", "ACM001"],
        "expected_rights": ["Article18", "Article19", "Article21", "Article47"],
        "domain": "Immigration decision automation"
    },
    "P09": {
        "risk_level": "High",
        "expected_requirements": ["R003", "R009", "R027", "R042", "AI001", "AI005", "HE003", "HE015", "ACM001"],
        "expected_rights": ["Article7", "Article8", "Article35"],
        "domain": "Mental health prediction"
    },
    "P10": {
        "risk_level": "Medium",
        "expected_requirements": ["R003", "R009", "R027", "AI005", "HE003", "ACM001"],
        "expected_rights": ["Article8", "Article11"],
        "domain": "Sentiment analysis on tweets"
    },
    "P11": {
        "risk_level": "Medium",
        "expected_requirements": ["R003", "R009", "AI005", "HE003", "ACM001"],
        "expected_rights": ["Article6", "Article8"],
        "domain": "Traffic flow optimisation"
    },
    "P12": {
        "risk_level": "Medium",
        "expected_requirements": ["R003", "HE003", "ACM001"],
        "expected_rights": ["Article8"],
        "domain": "Agricultural crop prediction"
    },
    "P13": {
        "risk_level": "Medium",
        "expected_requirements": ["R003", "R009", "R027", "AI005", "HE003", "ACM001", "ACM012"],
        "expected_rights": ["Article8", "Article38"],
        "domain": "Customer service chatbot"
    },
    "P14": {
        "risk_level": "Medium",
        "expected_requirements": ["R003", "AI005", "HE003", "ACM001"],
        "expected_rights": ["Article8"],
        "domain": "Energy consumption forecasting"
    },
    "P15": {
        "risk_level": "Medium",
        "expected_requirements": ["R003", "HE003", "ACM001", "ACM012"],
        "expected_rights": ["Article11", "Article22"],
        "domain": "Language translation"
    },
    "P16": {
        "risk_level": "Medium",
        "expected_requirements": ["R003", "R009", "R027", "AI005", "HE003", "ACM001"],
        "expected_rights": ["Article8", "Article14"],
        "domain": "Plagiarism detection"
    },
    "P17": {
        "risk_level": "Low",
        "expected_requirements": ["R003", "HE003", "ACM001"],
        "expected_rights": ["Article8"],
        "domain": "Weather pattern analysis"
    },
    "P18": {
        "risk_level": "Low",
        "expected_requirements": ["R003", "HE003", "ACM001"],
        "expected_rights": ["Article22"],
        "domain": "Historical document digitisation"
    },
    "P19": {
        "risk_level": "Low",
        "expected_requirements": ["ACM001"],
        "expected_rights": [],
        "domain": "Mathematical theorem proving"
    },
    "P20": {
        "risk_level": "Low",
        "expected_requirements": ["ACM001"],
        "expected_rights": [],
        "domain": "Open-source code linting"
    },
}


# ─── LLM BACKEND ─────────────────────────────────────────────

def call_llm(prompt, backend="ollama"):
    """Call LLM for judge-based metrics. Returns string response."""
    if backend == "ollama":
        import urllib.request
        data = json.dumps({
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 200}
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")

    elif backend == "groq":
        import urllib.request
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        data = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 200
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    else:
        raise ValueError(f"Unknown backend: {backend}")


# ─── METRIC 1: CONTEXT RECALL (no LLM needed) ───────────────

def context_recall(retrieved_req_ids, ground_truth_req_ids):
    """
    What fraction of ground truth requirements were retrieved?
    This is your existing retrieval recall metric, reframed in RAGAS terms.

    context_recall = |retrieved ∩ ground_truth| / |ground_truth|
    """
    if not ground_truth_req_ids:
        return 1.0  # no requirements expected, trivially satisfied
    retrieved = set(retrieved_req_ids)
    expected = set(ground_truth_req_ids)
    return len(retrieved & expected) / len(expected)


# ─── METRIC 2: CONTEXT PRECISION (no LLM needed) ────────────

def context_precision(retrieved_req_ids, ground_truth_req_ids):
    """
    What fraction of retrieved requirements are actually relevant?

    context_precision = |retrieved ∩ ground_truth| / |retrieved|
    """
    if not retrieved_req_ids:
        return 0.0
    retrieved = set(retrieved_req_ids)
    expected = set(ground_truth_req_ids)
    return len(retrieved & expected) / len(retrieved)


# ─── METRIC 3: FAITHFULNESS (LLM judge) ─────────────────────

def faithfulness(generated_text, context_text, backend="ollama"):
    """
    Does the generated answer only make claims supported by the context?
    Uses LLM as judge to score 0.0-1.0.
    """
    prompt = f"""You are evaluating whether an AI-generated ethics assessment is faithful to the provided context.

CONTEXT (retrieved from knowledge graph):
{context_text[:3000]}

GENERATED ASSESSMENT:
{generated_text[:3000]}

Score the faithfulness from 0.0 to 1.0:
- 1.0 = every claim in the assessment is supported by the context
- 0.5 = some claims are supported, some are not
- 0.0 = the assessment contradicts or fabricates information not in context

Respond with ONLY a JSON object: {{"score": 0.XX, "reason": "brief explanation"}}"""

    try:
        response = call_llm(prompt, backend)
        # Extract score from response
        match = re.search(r'"score"\s*:\s*([\d.]+)', response)
        if match:
            return min(1.0, max(0.0, float(match.group(1))))
        return 0.5  # default if parsing fails
    except Exception as e:
        print(f"  [WARN] Faithfulness LLM call failed: {e}")
        return None


# ─── METRIC 4: ANSWER RELEVANCY (LLM judge) ─────────────────

def answer_relevancy(proposal_text, generated_text, backend="ollama"):
    """
    Is the generated assessment relevant to the input proposal?
    Uses LLM as judge to score 0.0-1.0.
    """
    prompt = f"""You are evaluating whether an AI-generated ethics assessment is relevant to the research proposal it was asked to assess.

RESEARCH PROPOSAL:
{proposal_text[:2000]}

GENERATED ASSESSMENT:
{generated_text[:3000]}

Score the relevancy from 0.0 to 1.0:
- 1.0 = the assessment directly addresses the ethical issues in this specific proposal
- 0.5 = the assessment is partially relevant but includes generic content
- 0.0 = the assessment is about something entirely different

Respond with ONLY a JSON object: {{"score": 0.XX, "reason": "brief explanation"}}"""

    try:
        response = call_llm(prompt, backend)
        match = re.search(r'"score"\s*:\s*([\d.]+)', response)
        if match:
            return min(1.0, max(0.0, float(match.group(1))))
        return 0.5
    except Exception as e:
        print(f"  [WARN] Relevancy LLM call failed: {e}")
        return None


# ─── OUTPUT LOADER ────────────────────────────────────────────

def load_evaluation_output(output_dir, proposal_id):
    """Load a single evaluation output JSON."""
    # Try common filename patterns
    for pattern in [
        f"{proposal_id}.json",
        f"{proposal_id}_output.json",
        f"{proposal_id.lower()}.json",
        f"{proposal_id.lower()}_output.json",
    ]:
        fpath = os.path.join(output_dir, pattern)
        if os.path.exists(fpath):
            with open(fpath) as f:
                return json.load(f)
    return None


def extract_fields(output_data):
    """
    Extract relevant fields from evaluation output JSON.
    Adapt these keys to match YOUR actual output structure.
    """
    assessment = output_data.get("assessment", output_data)

    # Retrieved requirement IDs (from KG retrieval, before LLM processing)
    retrieved_reqs = []
    kg_metadata = output_data.get("kg_metadata", output_data.get("retrieval", {}))
    if isinstance(kg_metadata, dict):
        retrieved_reqs = kg_metadata.get("retrieved_requirement_ids", [])
    # Fallback: scan for requirement ID patterns in full output
    if not retrieved_reqs:
        text = json.dumps(output_data)
        retrieved_reqs = list(set(re.findall(r'\b(R\d{3}|AI\d{3}|HE\d{3}|ACM\d{3})\b', text)))

    # Generated text (the full LLM assessment output)
    generated_text = ""
    if isinstance(assessment, dict):
        for key in ["risk_summary", "assessment_text", "summary", "full_text"]:
            if key in assessment:
                generated_text += str(assessment[key]) + "\n"
        # Also grab requirements section
        reqs = assessment.get("requirements", assessment.get("applicable_requirements", []))
        if isinstance(reqs, list):
            for r in reqs:
                if isinstance(r, dict):
                    generated_text += f"{r.get('id', '')} {r.get('description', '')}\n"
                else:
                    generated_text += str(r) + "\n"
    if not generated_text:
        generated_text = json.dumps(assessment, indent=2)

    # Context text (what was retrieved from KG and passed to LLM)
    context_text = ""
    if isinstance(kg_metadata, dict):
        context_text = json.dumps(kg_metadata, indent=2)
    if not context_text:
        context_text = generated_text  # fallback

    # Proposal text
    proposal_text = output_data.get("proposal_text", output_data.get("input", ""))

    return {
        "retrieved_reqs": retrieved_reqs,
        "generated_text": generated_text,
        "context_text": context_text,
        "proposal_text": proposal_text,
    }


# ─── MAIN EVALUATION ─────────────────────────────────────────

def run_ragas_evaluation(output_dir, backend="ollama", skip_llm=False):
    """Run all four RAGAS metrics across all proposals in output_dir."""

    print(f"\n{'='*70}")
    print(f"RAGAS METRICS — {output_dir}")
    print(f"Backend: {backend} | LLM-judge metrics: {'SKIPPED' if skip_llm else 'ENABLED'}")
    print(f"{'='*70}\n")

    results = []

    for pid, gt in sorted(GROUND_TRUTH_DATA.items()):
        output_data = load_evaluation_output(output_dir, pid)
        if output_data is None:
            print(f"  [{pid}] Output file not found, skipping")
            continue

        fields = extract_fields(output_data)
        print(f"  [{pid}] {gt['domain']}")
        print(f"    Retrieved {len(fields['retrieved_reqs'])} req IDs, "
              f"expected {len(gt['expected_requirements'])}")

        # Metric 1: Context Recall
        cr = context_recall(fields["retrieved_reqs"], gt["expected_requirements"])

        # Metric 2: Context Precision
        cp = context_precision(fields["retrieved_reqs"], gt["expected_requirements"])

        # Metric 3: Faithfulness (LLM judge)
        faith = None
        if not skip_llm and fields["context_text"] and fields["generated_text"]:
            faith = faithfulness(fields["generated_text"], fields["context_text"], backend)

        # Metric 4: Answer Relevancy (LLM judge)
        relevancy = None
        if not skip_llm and fields["proposal_text"] and fields["generated_text"]:
            relevancy = answer_relevancy(fields["proposal_text"], fields["generated_text"], backend)

        row = {
            "proposal_id": pid,
            "context_recall": cr,
            "context_precision": cp,
            "faithfulness": faith,
            "answer_relevancy": relevancy,
        }
        results.append(row)
        print(f"    CR={cr:.3f}  CP={cp:.3f}  "
              f"Faith={'N/A' if faith is None else f'{faith:.3f}'}  "
              f"Rel={'N/A' if relevancy is None else f'{relevancy:.3f}'}")

    # ─── AGGREGATE ────────────────────────────────────────────
    if not results:
        print("\nNo results to aggregate.")
        return

    print(f"\n{'─'*70}")
    print("AGGREGATE RAGAS METRICS")
    print(f"{'─'*70}")

    for metric in ["context_recall", "context_precision", "faithfulness", "answer_relevancy"]:
        values = [r[metric] for r in results if r[metric] is not None]
        if values:
            avg = sum(values) / len(values)
            minimum = min(values)
            maximum = max(values)
            print(f"  {metric:25s}  mean={avg:.4f}  min={minimum:.4f}  max={maximum:.4f}  n={len(values)}")
        else:
            print(f"  {metric:25s}  N/A (no valid scores)")

    # Save results
    results_file = os.path.join(output_dir, "ragas_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_file}")

    return results


# ─── CLI ──────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAGAS metrics for AIEF evaluation")
    parser.add_argument("--output-dir", required=True, help="Directory containing evaluation output JSONs")
    parser.add_argument("--backend", default="ollama", choices=["ollama", "groq"],
                        help="LLM backend for judge-based metrics")
    parser.add_argument("--skip-llm", action="store_true",
                        help="Skip faithfulness and answer_relevancy (no LLM calls)")
    args = parser.parse_args()

    run_ragas_evaluation(args.output_dir, args.backend, args.skip_llm)
