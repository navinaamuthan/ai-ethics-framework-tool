"""Post-hoc filter: keep only LLM citations that exist in the retrieved set.
Reports hallucinated-citation rate and corrected P/R/F1 vs expected requirements."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from synthetic_proposals import PROPOSALS
from sparql_retrieval import retrieve_all_for_proposal

SRC = Path(__file__).parent.parent / "evaluation/results/llama-3.3-70b"

import re

def norm_id(rid: str) -> str:
    rid = str(rid).strip().strip("[]")
    rid = re.sub(r"EUAIAct[\s\-]*", "AI", rid, flags=re.I)
    rid = re.sub(r"HorizonEurope[\s\-]*", "HE", rid, flags=re.I)
    m = re.search(r"((?:R|AI|HE|ACM)\d+)", rid, re.I)
    return m.group(1).upper() if m else rid

def prf(cited, expected):
    tp = len(cited & expected)
    p = tp / len(cited) if cited else 0
    r = tp / len(expected) if expected else 1
    f = 2 * p * r / (p + r) if p + r else 0
    return p, r, f

before, after, halluc = [], [], 0
total_cites = 0
for gt in sorted(PROPOSALS, key=lambda p: p["id"]):
    pid = gt["id"]
    f = SRC / f"{pid}_full.json"
    if not f.exists(): continue
    d = json.load(open(f))
    cited = {norm_id(r.get("requirement_id", "")) for r in d["assessment"]["applicable_requirements"]} - {""}
    # Prefer IDs already recorded in the evaluation JSON; fall back to live retrieval
    meta = d.get("_retrieval_metadata") or d.get("assessment", {}).get("_retrieval_metadata") or {}
    retrieved = {norm_id(x) for x in (meta.get("requirements_retrieved_ids") or [])} - {""}
    if not retrieved:
        reqs, _, _, _ = retrieve_all_for_proposal(d["proposal_text"])
        retrieved = {norm_id(r["id"]) for r in reqs} - {""}
    kept = cited & retrieved
    halluc += len(cited - retrieved)
    total_cites += len(cited)
    exp = {norm_id(x) for x in gt["expected_requirements"]}
    before.append(prf(cited, exp))
    after.append(prf(kept, exp))
    if cited - retrieved:
        print(f"  {pid} hallucinated cites: {sorted(cited - retrieved)}")

n = len(before)
for name, arr in [("unfiltered", before), ("post-filtered", after)]:
    print(f"{name}: P={sum(a[0] for a in arr)/n:.3f} R={sum(a[1] for a in arr)/n:.3f} F1={sum(a[2] for a in arr)/n:.3f}")
print(f"Citations outside retrieved set (hallucination-rate proxy): {halluc}/{total_cites} = {100*halluc/max(total_cites,1):.1f}%")
