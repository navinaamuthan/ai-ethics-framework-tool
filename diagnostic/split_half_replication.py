"""split_half_replication.py

External-validity test: does the Stage-one reliability finding replicate when
the diagnostic is applied to two disjoint halves of the corpus that were
constructed separately?

Corpus A divides naturally at P20. P01--P20 were authored first, drawn
largely from documented North American and European deployments, and skewed
toward high-risk cases. P21--P40 were authored later, under different
selection criteria (geographic and institutional diversity, inter-source
tension, contested rights, and low-risk cases carrying superficial risk
markers), and are weighted toward the middle and lower strata. The two halves
therefore differ in provenance, in composition, and in risk distribution,
which makes agreement between them a test rather than a repetition.

The full Stage-one pipeline is recomputed independently on each half using
the identical statistic, estimator, and run design as the headline analysis,
so any difference is attributable to the corpus.

Usage:  python split_half_replication.py
Writes: results/split_half_replication.json
        results/tables/tab_split_half.tex
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

import reliability_analysis as ra  # noqa: E402
from synthetic_proposals_extended import PROPOSALS  # noqa: E402

RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
PERSONAS = ["technical", "legal", "ethics", "lay"]
RUNS = (1, 2, 3)


def stage_one(idx, pids, personas=PERSONAS):
    within = {}
    for p in personas:
        vals = []
        for r1, r2 in combinations(RUNS, 2):
            pairs = [
                (idx[(pid, p, r1)]["risk_level"], idx[(pid, p, r2)]["risk_level"])
                for pid in pids
                if (pid, p, r1) in idx and (pid, p, r2) in idx
            ]
            if pairs:
                vals.append(kappa(pairs))
        if vals:
            within[p] = statistics.mean(vals)

    cross = []
    for p1, p2 in combinations(personas, 2):
        pairs = [
            (idx[(pid, p1, 1)]["risk_level"], idx[(pid, p2, 1)]["risk_level"])
            for pid in pids
            if (pid, p1, 1) in idx and (pid, p2, 1) in idx
        ]
        if pairs:
            cross.append(kappa(pairs))

    ceiling = max(within.values())
    return {
        "n_proposals": len(pids),
        "within_by_perspective": {k: round(v, 4) for k, v in within.items()},
        "mean_within": round(statistics.mean(within.values()), 4),
        "mean_cross": round(statistics.mean(cross), 4),
        "ceiling": round(ceiling, 4),
        "noise_band": round(1 - ceiling, 4),
        "ceiling_perspective": max(within, key=within.get),
    }


def assessor_verdicts(pids, band):
    labels = ra.load_assessor_labels()
    gt = {p["id"]: p["risk_level"] for p in PROPOSALS if p["id"] in pids}
    scores = {}
    for name, lab in labels.items():
        pairs = [(gt[pid], v["risk"]) for pid, v in lab.items() if pid in gt]
        if pairs:
            scores[name] = kappa(pairs)
    rows, n_disc = [], 0
    for a, b in combinations(sorted(scores), 2):
        gap = abs(scores[a] - scores[b])
        d = gap >= band
        n_disc += d
        rows.append({"a": a, "b": b, "gap": round(gap, 4), "discriminable": d})
    return {
        "assessor_kappa": {k: round(v, 4) for k, v in scores.items()},
        "pairs": rows,
        "n_discriminable": n_disc,
        "n_pairs": len(rows),
    }


def main() -> None:
    recs = json.loads((ROOT / "frame_annotations.json").read_text(encoding="utf-8"))
    idx = {(r["proposal_id"], r["perspective"], r["run"]): r for r in recs}

    first = sorted(p["id"] for p in PROPOSALS if int(p["id"][1:]) <= 20)
    second = sorted(p["id"] for p in PROPOSALS if int(p["id"][1:]) > 20)

    halves = {}
    for name, pids in (("P01-P20", first), ("P21-P40", second)):
        s1 = stage_one(idx, pids)
        s1["risk_distribution"] = dict(
            Counter(p["risk_level"] for p in PROPOSALS if p["id"] in pids)
        )
        s1.update(assessor_verdicts(pids, s1["noise_band"]))
        halves[name] = s1

    full = stage_one(idx, sorted(p["id"] for p in PROPOSALS))
    full.update(assessor_verdicts(sorted(p["id"] for p in PROPOSALS),
                                  full["noise_band"]))

    a, b = halves["P01-P20"], halves["P21-P40"]
    out = {
        "full_corpus": full,
        "halves": halves,
        "replication": {
            "within_exceeds_cross_both_halves":
                a["mean_within"] > a["mean_cross"] and b["mean_within"] > b["mean_cross"],
            "zero_discriminable_both_halves":
                a["n_discriminable"] == 0 and b["n_discriminable"] == 0,
            "ceiling_difference_between_halves": round(abs(a["ceiling"] - b["ceiling"]), 4),
            "ceiling_perspective_agrees":
                a["ceiling_perspective"] == b["ceiling_perspective"],
        },
    }
    RESULTS.mkdir(exist_ok=True); TABLES.mkdir(exist_ok=True)
    (RESULTS / "split_half_replication.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    rows = [
        r"\begin{tabular}{lccc}", r"\toprule",
        r"Quantity & P01--P20 & P21--P40 & Full corpus \\", r"\midrule",
        f"Proposals & {a['n_proposals']} & {b['n_proposals']} & {full['n_proposals']} \\\\",
        f"Mean within-stratum $\\kappa$ & {a['mean_within']:.3f} & {b['mean_within']:.3f} & {full['mean_within']:.3f} \\\\",
        f"Mean cross-stratum $\\kappa$ & {a['mean_cross']:.3f} & {b['mean_cross']:.3f} & {full['mean_cross']:.3f} \\\\",
        f"Reliability ceiling & {a['ceiling']:.3f} & {b['ceiling']:.3f} & {full['ceiling']:.3f} \\\\",
        f"Noise band & {a['noise_band']:.3f} & {b['noise_band']:.3f} & {full['noise_band']:.3f} \\\\",
        f"Pairs discriminable & {a['n_discriminable']}/6 & {b['n_discriminable']}/6 & {full['n_discriminable']}/6 \\\\",
        r"\bottomrule", r"\end{tabular}",
    ]
    (TABLES / "tab_split_half.tex").write_text("\n".join(rows), encoding="utf-8")

    print("=== SPLIT-HALF REPLICATION ===")
    for name in ("P01-P20", "P21-P40"):
        h = halves[name]
        print(f"  {name}: n={h['n_proposals']} within={h['mean_within']:.3f} "
              f"cross={h['mean_cross']:.3f} ceiling={h['ceiling']:.3f} "
              f"band={h['noise_band']:.3f} disc={h['n_discriminable']}/6 "
              f"risk={h['risk_distribution']}")
    print(f"  FULL   : within={full['mean_within']:.3f} cross={full['mean_cross']:.3f} "
          f"ceiling={full['ceiling']:.3f} disc={full['n_discriminable']}/6")
    r = out["replication"]
    print(f"\n  within>cross in both halves : {r['within_exceeds_cross_both_halves']}")
    print(f"  zero discriminable in both  : {r['zero_discriminable_both_halves']}")
    print(f"  ceiling difference          : {r['ceiling_difference_between_halves']}")
    print(f"  same ceiling perspective    : {r['ceiling_perspective_agrees']} "
          f"({a['ceiling_perspective']} / {b['ceiling_perspective']})")


if __name__ == "__main__":
    main()
