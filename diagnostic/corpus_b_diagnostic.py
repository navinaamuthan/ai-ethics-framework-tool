"""corpus_b_diagnostic.py

Run the diagnostic's Stage-one machinery on Corpus B and compare with the
Corpus A result, testing whether the reliability finding replicates outside
the corpus the method was developed on.

Uses the identical persona prompts, temperature, run count, and kappa
implementation as the Corpus A study, so any difference in outcome is
attributable to the corpus rather than to the procedure.

Usage:  python corpus_b_diagnostic.py
Writes: corpus_b_annotations.json
        results/corpus_b_report.json
        results/tables/tab_corpus_b.tex
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAG = ROOT.parent / "rag-pipeline"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

_aa = RAG / "annotator_agreement.py"
_src = _aa.read_text(encoding="utf-8")
_cut = _src.find('\nprint("=== Annotator')
_ns: dict = {"__name__": "_aa_funcs", "__file__": str(_aa)}
exec((_src[:_cut] if _cut != -1 else _src), _ns)
kappa = _ns["kappa"]

from frame_annotation import PERSONAS  # noqa: E402  (identical persona prompts)
from llm_caller import call_llm, parse_json_response  # noqa: E402

CORPUS = ROOT / "corpus_b.json"
ANN_OUT = ROOT / "corpus_b_annotations.json"
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
RUNS = (1, 2, 3)
TEMP = 0.7

VOCAB = [
    "Art1_HumanDignity", "Art6_RightToLiberty", "Art7_PrivateLife",
    "Art8_DataProtection", "Art11_FreedomOfExpression", "Art14_RightToEducation",
    "Art15_FreedomOfOccupation", "Art21_NonDiscrimination", "Art24_RightsOfChild",
    "Art25_RightsOfElderly", "Art26_DisabilityIntegration", "Art31_WorkingConditions",
    "Art35_HealthCare", "Art38_ConsumerProtection", "Art41_GoodAdministration",
    "Art47_RightToEffectiveRemedy",
]


def user_prompt(text: str) -> str:
    return f"""Task: Annotate the research proposal below.

Return a single JSON object with exactly these keys:
  "risk_level": one of "High", "Medium", "Low"
  "charter_articles": a JSON array of zero or more strings, each MUST be drawn
      from this vocabulary (copy spelling exactly): [{", ".join(VOCAB)}]
  "info_sufficiency": an integer from 1 to 5 meaning how much information you
      needed versus how much you were given (5 = fully sufficient to judge
      confidently; 1 = genuinely under-specified)

Do not invent article names outside the vocabulary. Do not include commentary
outside the JSON object.

PROPOSAL:
{text}"""


def annotate() -> list[dict]:
    if ANN_OUT.exists():
        recs = json.loads(ANN_OUT.read_text(encoding="utf-8"))
        print(f"reusing {len(recs)} cached annotations")
        return recs
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    recs, skips = [], 0
    for p in corpus:
        for persp, sysmsg in PERSONAS.items():
            for run in RUNS:
                prompt = (f"SYSTEM PERSONA (stay in role):\n{sysmsg}\n\n"
                          f"USER TASK:\n{user_prompt(p['proposal_text'])}")
                parsed = None
                for _ in range(3):
                    raw = call_llm(prompt, backend="ollama",
                                   model="llama3.1:8b", temperature=TEMP)
                    parsed = parse_json_response(raw or "")
                    if parsed and parsed.get("risk_level") in ("High", "Medium", "Low"):
                        break
                    parsed = None
                if not parsed:
                    skips += 1
                    continue
                arts = [a for a in (parsed.get("charter_articles") or []) if a in VOCAB]
                recs.append({
                    "proposal_id": p["id"], "perspective": persp, "run": run,
                    "risk_level": parsed["risk_level"],
                    "charter_articles": arts,
                    "info_sufficiency": parsed.get("info_sufficiency", 3),
                })
        print(f"  {p['id']} done ({len(recs)} records)")
    ANN_OUT.write_text(json.dumps(recs, indent=2), encoding="utf-8")
    print(f"annotations: {len(recs)}  skips: {skips}")
    return recs


def analyse(recs: list[dict], corpus: list[dict]) -> dict:
    idx = {(r["proposal_id"], r["perspective"], r["run"]): r for r in recs}
    pids = sorted({r["proposal_id"] for r in recs})
    personas = list(PERSONAS)

    within = {}
    for p in personas:
        vals = []
        for r1, r2 in combinations(RUNS, 2):
            pairs = [(idx[(pid, p, r1)]["risk_level"], idx[(pid, p, r2)]["risk_level"])
                     for pid in pids if (pid, p, r1) in idx and (pid, p, r2) in idx]
            if pairs:
                vals.append(kappa(pairs))
        if vals:
            within[p] = statistics.mean(vals)

    cross_vals = []
    for p1, p2 in combinations(personas, 2):
        pairs = [(idx[(pid, p1, 1)]["risk_level"], idx[(pid, p2, 1)]["risk_level"])
                 for pid in pids if (pid, p1, 1) in idx and (pid, p2, 1) in idx]
        if pairs:
            cross_vals.append(kappa(pairs))

    mean_within = statistics.mean(within.values())
    mean_cross = statistics.mean(cross_vals)
    ceiling = max(within.values())
    band = 1.0 - ceiling

    # Agreement of each perspective with the rule-derived reference labels.
    gt = {p["id"]: p["risk_level"] for p in corpus}
    vs_ref = {}
    for p in personas:
        pairs = [(gt[pid], idx[(pid, p, 1)]["risk_level"])
                 for pid in pids if (pid, p, 1) in idx]
        vs_ref[p] = kappa(pairs) if pairs else float("nan")

    return {
        "n_proposals": len(pids),
        "n_annotations": len(recs),
        "within_by_perspective": {k: round(v, 4) for k, v in within.items()},
        "mean_within": round(mean_within, 4),
        "mean_cross": round(mean_cross, 4),
        "ceiling": round(ceiling, 4),
        "noise_band": round(band, 4),
        "within_exceeds_cross": mean_within > mean_cross,
        "perspective_vs_reference_kappa": {k: round(v, 4) for k, v in vs_ref.items()},
        "reference_label_provenance": "rule-derived from published feature scoring",
    }


def main() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    recs = annotate()
    b = analyse(recs, corpus)

    a = json.loads((RESULTS / "reliability_report.json").read_text(encoding="utf-8"))
    a_sum = {
        "n_proposals": a["n_proposals"],
        "n_annotations": a["n_annotations"],
        "mean_within": round(a["within_stratum"]["mean_within_risk"], 4),
        "mean_cross": round(a["cross_stratum"]["mean_cross_risk"], 4),
        "ceiling": round(a["ceiling_risk"], 4),
        "noise_band": round(1 - a["ceiling_risk"], 4),
    }

    out = {
        "corpus_a": a_sum,
        "corpus_b": b,
        "replication": {
            "within_exceeds_cross_in_both":
                a_sum["mean_within"] > a_sum["mean_cross"] and b["within_exceeds_cross"],
            "ceiling_difference": round(b["ceiling"] - a_sum["ceiling"], 4),
            "band_difference": round(b["noise_band"] - a_sum["noise_band"], 4),
        },
    }
    RESULTS.mkdir(exist_ok=True); TABLES.mkdir(exist_ok=True)
    (RESULTS / "corpus_b_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    rows = [
        r"\begin{tabular}{lcc}", r"\toprule",
        r"Quantity & Corpus A & Corpus B \\", r"\midrule",
        f"Proposals & {a_sum['n_proposals']} & {b['n_proposals']} \\\\",
        f"Annotations & {a_sum['n_annotations']} & {b['n_annotations']} \\\\",
        r"Reference labels & author-assigned & rule-derived \\",
        f"Mean within-stratum $\\kappa$ & {a_sum['mean_within']:.3f} & {b['mean_within']:.3f} \\\\",
        f"Mean cross-stratum $\\kappa$ & {a_sum['mean_cross']:.3f} & {b['mean_cross']:.3f} \\\\",
        f"Reliability ceiling & {a_sum['ceiling']:.3f} & {b['ceiling']:.3f} \\\\",
        f"Noise band & {a_sum['noise_band']:.3f} & {b['noise_band']:.3f} \\\\",
        r"\bottomrule", r"\end{tabular}",
    ]
    (TABLES / "tab_corpus_b.tex").write_text("\n".join(rows), encoding="utf-8")

    print("\n=== CORPUS A vs CORPUS B ===")
    print(f"  within : {a_sum['mean_within']:.3f}  vs  {b['mean_within']:.3f}")
    print(f"  cross  : {a_sum['mean_cross']:.3f}  vs  {b['mean_cross']:.3f}")
    print(f"  ceiling: {a_sum['ceiling']:.3f}  vs  {b['ceiling']:.3f}")
    print(f"  band   : {a_sum['noise_band']:.3f}  vs  {b['noise_band']:.3f}")
    print(f"  within>cross in both: {out['replication']['within_exceeds_cross_in_both']}")
    print(f"  per-perspective within (B): {b['within_by_perspective']}")
    print(f"  perspective vs reference (B): {b['perspective_vs_reference_kappa']}")


if __name__ == "__main__":
    main()
