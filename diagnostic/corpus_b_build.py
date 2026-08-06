"""corpus_b_build.py

Construct Corpus B: a second, independently-specified evaluation corpus used
to test whether the diagnostic's findings on Corpus A (P01--P40) replicate
outside the corpus they were developed on.

Corpus B differs from Corpus A on three axes chosen to make replication a
genuine test rather than a repetition:

1. Reference labels are RULE-DERIVED, not author-assigned. Each proposal is
   specified first as a feature vector (domain, affected population, data
   sensitivity, safeguards, deployment scale) and its reference risk level is
   computed from those features by an explicit, published scoring rule below.
   Corpus A's labels came from the author's judgement. Corpus B's therefore
   have different provenance, and a reader can audit them without trusting
   anyone's judgement.

2. Domain coverage is deliberately disjoint from Corpus A's centre of mass.
   Corpus A concentrates on public-sector, health, and criminal-justice
   deployment. Corpus B covers education technology, scientific research
   tooling, workplace systems, consumer products, and civic infrastructure.

3. Proposal prose is generated from the feature vector rather than written
   toward a target label, so the text cannot encode the label through
   authorial framing.

Usage:  python corpus_b_build.py            # build spec + prose
Writes: corpus_b.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAG = ROOT.parent / "rag-pipeline"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

from llm_caller import call_llm  # noqa: E402

OUT = ROOT / "corpus_b.json"

# ---------------------------------------------------------------------------
# Feature grid. Each proposal is one combination; risk is derived, not chosen.
# ---------------------------------------------------------------------------
# (id, domain, population, data_sensitivity, safeguards, scale)
SPECS = [
    ("B01", "education technology", "children under 13", "biometric", "none", "national"),
    ("B02", "education technology", "university students", "behavioural", "partial", "institutional"),
    ("B03", "education technology", "adult learners", "performance", "full", "single-site"),
    ("B04", "scientific research tooling", "researchers", "publication metadata", "full", "single-site"),
    ("B05", "scientific research tooling", "clinical trial participants", "health", "partial", "multi-site"),
    ("B06", "scientific research tooling", "researchers", "code and text", "full", "open release"),
    ("B07", "workplace systems", "warehouse workers", "location and productivity", "none", "national"),
    ("B08", "workplace systems", "office employees", "communication metadata", "partial", "institutional"),
    ("B09", "workplace systems", "job applicants", "video and speech", "none", "national"),
    ("B10", "workplace systems", "employees", "aggregate wellbeing", "full", "single-site"),
    ("B11", "consumer products", "general public", "purchase history", "partial", "national"),
    ("B12", "consumer products", "children under 13", "voice", "none", "international"),
    ("B13", "consumer products", "general public", "anonymised telemetry", "full", "national"),
    ("B14", "civic infrastructure", "residents", "location", "none", "municipal"),
    ("B15", "civic infrastructure", "residents", "aggregate utility usage", "full", "municipal"),
    ("B16", "civic infrastructure", "welfare applicants", "financial and household", "none", "national"),
    ("B17", "civic infrastructure", "public transport users", "anonymised counts", "full", "municipal"),
    ("B18", "education technology", "students with disabilities", "assistive-use data", "partial", "institutional"),
    ("B19", "consumer products", "older adults", "health and activity", "partial", "national"),
    ("B20", "workplace systems", "gig-economy drivers", "location and rating", "none", "international"),
]

# ---------------------------------------------------------------------------
# Published scoring rule. Reference risk level is a function of features only.
# ---------------------------------------------------------------------------
VULNERABLE = {
    "children under 13", "students with disabilities", "older adults",
    "welfare applicants", "clinical trial participants",
}
SENSITIVE = {
    "biometric", "health", "voice", "video and speech",
    "financial and household", "location", "location and productivity",
    "location and rating", "health and activity",
}
SAFEGUARD_SCORE = {"none": 2, "partial": 1, "full": 0}
SCALE_SCORE = {
    "single-site": 0, "institutional": 1, "municipal": 1,
    "multi-site": 1, "open release": 1, "national": 2, "international": 2,
}


def derive_risk(population: str, sensitivity: str, safeguards: str, scale: str):
    """Reference risk from features. Published so it can be audited."""
    score = 0
    reasons = []
    if population in VULNERABLE:
        score += 2
        reasons.append(f"vulnerable population ({population}) [+2]")
    if sensitivity in SENSITIVE:
        score += 2
        reasons.append(f"sensitive data ({sensitivity}) [+2]")
    s = SAFEGUARD_SCORE[safeguards]
    if s:
        score += s
        reasons.append(f"safeguards {safeguards} [+{s}]")
    sc = SCALE_SCORE[scale]
    if sc:
        score += sc
        reasons.append(f"scale {scale} [+{sc}]")
    level = "High" if score >= 5 else ("Medium" if score >= 3 else "Low")
    return level, score, reasons


PROMPT = """Write a short research/deployment proposal of 120-160 words for an AI system with EXACTLY these characteristics:

Domain: {domain}
Affected population: {population}
Data used: {sensitivity}
Safeguards in place: {safeguards}
Deployment scale: {scale}

Rules:
- Describe the system factually and neutrally, as a proposal author would.
- State plainly what data is collected and what safeguards exist or are absent.
- Do NOT state or imply an overall risk level, and do NOT use the words "high risk", "medium risk", "low risk", "ethical", or "compliant".
- Do NOT editorialise about whether the system is good or bad.
- Output the proposal text only, no title, no preamble."""


def main() -> None:
    out = []
    for pid, domain, pop, sens, safe, scale in SPECS:
        level, score, reasons = derive_risk(pop, sens, safe, scale)
        prompt = PROMPT.format(domain=domain, population=pop, sensitivity=sens,
                               safeguards=safe, scale=scale)
        text = ""
        for attempt in range(3):
            text = (call_llm(prompt, backend="ollama", model="llama3.1:8b",
                             temperature=0.7) or "").strip()
            if len(text.split()) >= 60:
                break
        out.append({
            "id": pid,
            "domain": domain,
            "population": pop,
            "data_sensitivity": sens,
            "safeguards": safe,
            "scale": scale,
            "risk_level": level,
            "risk_score": score,
            "score_rationale": reasons,
            "proposal_text": text,
        })
        print(f"  {pid} {level:<7} score={score} words={len(text.split()):<4} {domain}")
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    from collections import Counter
    print("\nrisk distribution:", dict(Counter(p["risk_level"] for p in out)))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
