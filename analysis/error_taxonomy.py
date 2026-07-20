"""Error taxonomy + per-framework breakdown over the 20-proposal evaluation.
Categories:
  E1 risk over-classification (predicted > expected tier)
  E2 risk under-classification (predicted < expected tier)
  E3 requirement retrieval miss   (expected req never retrieved)
  E4 requirement generation miss  (retrieved but not cited)
  E5 rights generation miss       (right matched at retrieval, not cited)
  E6 rights retrieval miss        (right never matched)
  E7 extra citation               (cited requirement outside expected set;
                                   not necessarily wrong -- reported separately)
  E8 risk-category miss           (expected RiskCategory not surfaced in
                                   identified_risks[].risk_category)
All computed against synthetic_proposals.PROPOSALS (the corrected ground truth).
"""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "rag-pipeline"))
from synthetic_proposals import PROPOSALS
from sparql_retrieval import retrieve_all_for_proposal, set_retrieval_backend

# Prefer local TTL so taxonomy scoring works without GraphDB
set_retrieval_backend("auto")

SRC = Path(__file__).parent.parent / "evaluation/results/llama-3.3-70b"
TIER = {"Low": 0, "Medium": 1, "High": 2}
FW = lambda rid: ("EUAIAct" if rid.startswith("AI") else "HorizonEurope" if rid.startswith("HE")
                  else "ACMConference" if rid.startswith("ACM") else "REAMS")


def norm_right(s):
    m = re.search(r"Art(?:icle)?\s*(\d+)", str(s)); return f"Art{m.group(1)}" if m else None


def expected_risk_categories(p: dict) -> set:
    """Ground-truth risk categories: expected_risk_categories or expected_risks."""
    cats = p.get("expected_risk_categories") or p.get("expected_risks") or []
    return {str(c).strip() for c in cats if c}


def surfaced_risk_categories(assessment: dict) -> set:
    """Categories the LLM (or post-process) actually emitted."""
    out = set()
    for r in assessment.get("identified_risks", []) or []:
        cat = r.get("risk_category") or r.get("category")
        if cat:
            out.add(str(cat).strip())
    return out


tax = Counter(); detail = defaultdict(list)
fw_exp, fw_ret, fw_cit = Counter(), Counter(), Counter()

for p in PROPOSALS:
    pid = p["id"]
    f = SRC / f"{pid}_full.json"
    if not f.exists(): continue
    d = json.load(open(f)); a = d["assessment"]

    # risk tier
    pred, exp = a.get("overall_risk_level", ""), p["risk_level"]
    if TIER.get(pred, -1) > TIER[exp]: tax["E1 over-classification"] += 1; detail["E1"].append(pid)
    elif TIER.get(pred, -1) < TIER[exp] and pred in TIER: tax["E2 under-classification"] += 1; detail["E2"].append(pid)

    # requirements
    retrieved = {r["id"] for r in retrieve_all_for_proposal(p["proposal_text"])[0]}
    cited = {str(r.get("requirement_id", "")).strip("[]") for r in a.get("applicable_requirements", [])}
    expected = set(p["expected_requirements"])
    for rid in expected:
        fw_exp[FW(rid)] += 1
        if rid in retrieved: fw_ret[FW(rid)] += 1
        if rid in cited: fw_cit[FW(rid)] += 1
        if rid not in retrieved: tax["E3 req retrieval miss"] += 1; detail["E3"].append(f"{pid}:{rid}")
        elif rid not in cited: tax["E4 req generation miss"] += 1; detail["E4"].append(f"{pid}:{rid}")
    tax["E7 extra citations"] += len(cited - expected)

    # rights
    matched = {norm_right(r) for r in d.get("matched_rights", [])} - {None}
    cited_rights = {norm_right(r.get("article")) for r in a.get("charter_rights_at_risk", [])} - {None}
    exp_rights = {norm_right(r) for r in p.get("expected_rights", p.get("expected_charter_articles", []))} - {None}
    for rt in exp_rights - cited_rights:
        if rt in matched: tax["E5 rights generation miss"] += 1; detail["E5"].append(f"{pid}:{rt}")
        else: tax["E6 rights retrieval miss"] += 1; detail["E6"].append(f"{pid}:{rt}")

    # E8: risk-category miss
    exp_cats = expected_risk_categories(p)
    got_cats = surfaced_risk_categories(a)
    for cat in exp_cats - got_cats:
        tax["E8 risk-category miss"] += 1
        detail["E8"].append(f"{pid}:{cat}")

print("=== ERROR TAXONOMY (20 proposals, Llama 3.3 70B) ===")
for k in sorted(tax): print(f"  {k}: {tax[k]}")
print("\n=== PER-FRAMEWORK REQUIREMENT PERFORMANCE ===")
print(f"{'framework':14s} {'expected':>8s} {'retrieved':>9s} {'ret.recall':>10s} {'cited':>6s} {'cite.recall':>11s}")
for fw in ("REAMS", "EUAIAct", "HorizonEurope", "ACMConference"):
    e, r, c = fw_exp[fw], fw_ret[fw], fw_cit[fw]
    print(f"{fw:14s} {e:8d} {r:9d} {r/e if e else 0:10.3f} {c:6d} {c/e if e else 0:11.3f}")

out = {"taxonomy": dict(tax), "detail": {k: v for k, v in detail.items()},
       "per_framework": {fw: {"expected": fw_exp[fw], "retrieved": fw_ret[fw], "cited": fw_cit[fw]}
                         for fw in ("REAMS", "EUAIAct", "HorizonEurope", "ACMConference")}}
Path(__file__).parent.joinpath("results").mkdir(exist_ok=True)
json.dump(out, open(Path(__file__).parent / "results/error_taxonomy.json", "w"), indent=2)
print("\nSaved analysis/results/error_taxonomy.json")
