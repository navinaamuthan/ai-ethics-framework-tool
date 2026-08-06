"""sensitivity_analysis.py

Specification-curve analysis of the diagnostic's headline result.

The decision rule reported in reliability_analysis.py rests on four
methodological choices that were each defensible but none of which was
forced: Cohen's kappa as the agreement statistic, the maximum within-stratum
value as the reliability-ceiling estimator, all four perspectives included,
and run 1 as the representative pass for cross-stratum comparison. A reader
is entitled to ask whether the conclusion, that none of the six assessor
pairs is discriminable by accuracy, is a property of the data or an artefact
of that particular combination.

This script answers that by recomputing the entire pipeline under every
combination of reasonable alternatives:

    agreement statistic  : Cohen's kappa | Krippendorff's alpha | raw agreement
    ceiling estimator    : max | mean | median of within-stratum values
    perspectives included: all four | each leave-one-out
    cross-stratum run    : 1 | 2 | 3

giving 3 x 3 x 5 x 3 = 135 specifications. For each, the number of assessor
pairs certified as discriminable is recorded. If the headline result holds
across the curve, it does not depend on the choices made.

Usage:  python sensitivity_analysis.py
Writes: results/sensitivity_analysis.json
        results/tables/tab_sensitivity.tex
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAG = ROOT.parent / "rag-pipeline"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

_aa_path = RAG / "annotator_agreement.py"
_src = _aa_path.read_text(encoding="utf-8")
_cut = _src.find('\nprint("=== Annotator')
_ns: dict = {"__name__": "_aa_funcs", "__file__": str(_aa_path)}
exec((_src[:_cut] if _cut != -1 else _src), _ns)
cohen_kappa = _ns["kappa"]

import reliability_analysis as ra  # noqa: E402
from synthetic_proposals_extended import PROPOSALS  # noqa: E402

RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
PERSONAS = ["technical", "legal", "ethics", "lay"]


# ---------------------------------------------------------------------------
# Agreement statistics
# ---------------------------------------------------------------------------
def raw_agreement(pairs: list[tuple]) -> float:
    if not pairs:
        return float("nan")
    return sum(1 for a, b in pairs if a == b) / len(pairs)


def krippendorff_alpha(pairs: list[tuple]) -> float:
    """Krippendorff's alpha, nominal metric, via the coincidence matrix.

    Each element of `pairs` is one unit rated by exactly two coders, which is
    the shape every comparison in this pipeline takes. For two coders per unit
    the coincidence contribution per pair is 2/(m-1) = 2.
    """
    if not pairs:
        return float("nan")
    coincidence: dict = defaultdict(float)
    for a, b in pairs:
        # m_u = 2 ratings for this unit -> each ordered pair contributes 1/(m-1)=1
        coincidence[(a, b)] += 1.0
        coincidence[(b, a)] += 1.0
    n_c: dict = defaultdict(float)
    for (c, k), v in coincidence.items():
        n_c[c] += v
    n = sum(n_c.values())
    if n <= 1:
        return float("nan")
    do = sum(v for (c, k), v in coincidence.items() if c != k)
    de = 0.0
    for c in n_c:
        for k in n_c:
            if c != k:
                de += n_c[c] * n_c[k]
    de /= (n - 1)
    if de == 0:
        return float("nan")
    return 1.0 - (do / de)


STATS = {
    "cohen_kappa": cohen_kappa,
    "krippendorff_alpha": krippendorff_alpha,
    "raw_agreement": raw_agreement,
}
CEILINGS = {"max": max, "mean": statistics.mean, "median": statistics.median}


# ---------------------------------------------------------------------------
# Pipeline under one specification
# ---------------------------------------------------------------------------
def run_spec(idx, stat_name, ceil_name, personas, cross_run, assessor_labels, gt):
    stat = STATS[stat_name]
    ceil_fn = CEILINGS[ceil_name]

    # Within-stratum: mean pairwise agreement across the 3 runs, per persona.
    within = {}
    for p in personas:
        vals = []
        for r1, r2 in combinations([1, 2, 3], 2):
            pairs = []
            for pid in idx["pids"]:
                a = idx["ann"].get((pid, p, r1))
                b = idx["ann"].get((pid, p, r2))
                if a and b:
                    pairs.append((a["risk_level"], b["risk_level"]))
            if pairs:
                vals.append(stat(pairs))
        if vals:
            within[p] = statistics.mean(vals)
    if not within:
        return None
    ceiling = ceil_fn(list(within.values()))

    # Cross-stratum on the chosen representative run (reported for context).
    cross_vals = []
    for p1, p2 in combinations(personas, 2):
        pairs = []
        for pid in idx["pids"]:
            a = idx["ann"].get((pid, p1, cross_run))
            b = idx["ann"].get((pid, p2, cross_run))
            if a and b:
                pairs.append((a["risk_level"], b["risk_level"]))
        if pairs:
            cross_vals.append(stat(pairs))
    cross = statistics.mean(cross_vals) if cross_vals else float("nan")

    band = 1.0 - ceiling

    # Assessor agreement with the reference labels, under the same statistic.
    a_scores = {}
    for name, labels in assessor_labels.items():
        pairs = [
            (gt[pid], lab["risk"]) for pid, lab in labels.items() if pid in gt
        ]
        if pairs:
            a_scores[name] = stat(pairs)

    n_disc = 0
    pair_rows = []
    for a, b in combinations(sorted(a_scores), 2):
        gap = abs(a_scores[a] - a_scores[b])
        disc = gap >= band
        n_disc += disc
        pair_rows.append({"a": a, "b": b, "gap": round(gap, 4), "discriminable": disc})

    return {
        "statistic": stat_name,
        "ceiling_estimator": ceil_name,
        "perspectives": "all" if len(personas) == 4 else f"drop-{set(PERSONAS)-set(personas)}".replace("drop-{'", "drop-").replace("'}", ""),
        "n_perspectives": len(personas),
        "cross_run": cross_run,
        "within": round(statistics.mean(list(within.values())), 4),
        "cross": round(cross, 4) if cross == cross else None,
        "ceiling": round(ceiling, 4),
        "noise_band": round(band, 4),
        "n_discriminable": n_disc,
        "n_pairs": len(pair_rows),
    }


def main() -> None:
    records = json.loads((ROOT / "frame_annotations.json").read_text(encoding="utf-8"))
    idx = {
        "ann": {(r["proposal_id"], r["perspective"], r["run"]): r for r in records},
        "pids": sorted({r["proposal_id"] for r in records}),
    }
    assessor_labels = ra.load_assessor_labels()
    gt = {p["id"]: p["risk_level"] for p in PROPOSALS}

    persona_sets = [("all", PERSONAS)] + [
        (f"drop-{p}", [q for q in PERSONAS if q != p]) for p in PERSONAS
    ]

    specs = []
    for stat_name in STATS:
        for ceil_name in CEILINGS:
            for label, ps in persona_sets:
                for cross_run in (1, 2, 3):
                    row = run_spec(idx, stat_name, ceil_name, ps, cross_run,
                                   assessor_labels, gt)
                    if row:
                        row["perspectives"] = label
                        specs.append(row)

    dist = Counter(s["n_discriminable"] for s in specs)
    n_zero = dist.get(0, 0)
    bands = [s["noise_band"] for s in specs]
    ceilings = [s["ceiling"] for s in specs]

    # Which specifications, if any, produce a non-zero verdict?
    nonzero = [s for s in specs if s["n_discriminable"] > 0]

    out = {
        "n_specifications": len(specs),
        "grid": {
            "statistic": list(STATS),
            "ceiling_estimator": list(CEILINGS),
            "perspectives": [l for l, _ in persona_sets],
            "cross_run": [1, 2, 3],
        },
        "n_discriminable_distribution": {str(k): v for k, v in sorted(dist.items())},
        "n_specs_with_zero_discriminable": n_zero,
        "pct_specs_with_zero_discriminable": round(100 * n_zero / len(specs), 1),
        "ceiling_range": [round(min(ceilings), 3), round(max(ceilings), 3)],
        "noise_band_range": [round(min(bands), 3), round(max(bands), 3)],
        "nonzero_specifications": nonzero,
        "by_statistic": {
            s: {
                "n": sum(1 for x in specs if x["statistic"] == s),
                "n_zero": sum(1 for x in specs
                              if x["statistic"] == s and x["n_discriminable"] == 0),
                "ceiling_range": [
                    round(min(x["ceiling"] for x in specs if x["statistic"] == s), 3),
                    round(max(x["ceiling"] for x in specs if x["statistic"] == s), 3),
                ],
            }
            for s in STATS
        },
        "specifications": specs,
    }
    RESULTS.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    (RESULTS / "sensitivity_analysis.json").write_text(json.dumps(out, indent=2),
                                                       encoding="utf-8")

    lines = [
        r"\begin{tabular}{lccc}",
        r"\toprule",
        r"Agreement statistic & Specifications & Ceiling range & Pairs discriminable \\",
        r"\midrule",
    ]
    pretty = {"cohen_kappa": r"Cohen's $\kappa$",
              "krippendorff_alpha": r"Krippendorff's $\alpha$",
              "raw_agreement": "Raw agreement"}
    for s in STATS:
        d = out["by_statistic"][s]
        lines.append(
            f"{pretty[s]} & {d['n']} & "
            f"{d['ceiling_range'][0]}--{d['ceiling_range'][1]} & "
            f"{'0 in all' if d['n_zero']==d['n'] else str(d['n']-d['n_zero'])+' non-zero'} \\\\"
        )
    lines += [r"\midrule",
              f"All & {out['n_specifications']} & "
              f"{out['ceiling_range'][0]}--{out['ceiling_range'][1]} & "
              f"{out['pct_specs_with_zero_discriminable']}\\% return zero \\\\",
              r"\bottomrule", r"\end{tabular}"]
    (TABLES / "tab_sensitivity.tex").write_text("\n".join(lines), encoding="utf-8")

    print(f"specifications run: {len(specs)}")
    print(f"n_discriminable distribution: {dict(sorted(dist.items()))}")
    print(f"zero-discriminable in {n_zero}/{len(specs)} "
          f"({out['pct_specs_with_zero_discriminable']}%)")
    print(f"ceiling range: {out['ceiling_range']}  band range: {out['noise_band_range']}")
    for s in STATS:
        d = out["by_statistic"][s]
        print(f"  {s:<20} n={d['n']:<4} zero={d['n_zero']:<4} ceiling={d['ceiling_range']}")
    if nonzero:
        print(f"\nNON-ZERO specifications ({len(nonzero)}):")
        for s in nonzero[:10]:
            print(f"  {s['statistic']}/{s['ceiling_estimator']}/{s['perspectives']}"
                  f"/run{s['cross_run']}: {s['n_discriminable']} discriminable "
                  f"(band={s['noise_band']})")
    print("\nWrote results/sensitivity_analysis.json and tab_sensitivity.tex")


if __name__ == "__main__":
    main()
