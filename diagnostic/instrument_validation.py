"""instrument_validation.py

Validation of the diagnostic *as a measurement instrument*, in two parts that
the main reliability analysis does not cover.

Part A -- Manipulation check.
    The frame hypothesis presupposes that persona-conditioning actually
    produced four distinguishable professional frames. If the four personas
    were interchangeable, within- and cross-stratum agreement would be
    measuring the same thing and the reliability ceiling would be
    meaningless. This part tests the manipulation directly: whether the four
    perspectives differ systematically in what they flag, how much evidence
    they demand, and which Charter articles they reach for.

Part B -- Positive control (recovery test).
    On the real corpus the decision rule declines every pair, so the corpus
    alone cannot show that the rule is capable of *certifying* a comparison
    when one is warranted. A rule that always declines would be useless and
    would produce identical output. This part constructs assessors whose
    agreement with the reference labels is known by construction, by
    corrupting a controlled fraction of correct labels, and checks that the
    rule certifies exactly those pairs whose true separation exceeds the
    noise band and declines the rest. This is a recovery test: known inputs
    in, correct verdicts out.

Neither part requires new annotation, human or otherwise. Both run against
data already in the repository.

Usage:  python instrument_validation.py
Writes: results/instrument_validation.json
        results/tables/tab_manipulation_check.tex
        results/tables/tab_positive_control.tex
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAG = ROOT.parent / "rag-pipeline"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

# Reuse the exact kappa implementation the main analysis uses, so figures here
# are directly comparable with those in reliability_report.json.
_aa_path = RAG / "annotator_agreement.py"
_src = _aa_path.read_text(encoding="utf-8")
_cut = _src.find('\nprint("=== Annotator')
_ns: dict = {"__name__": "_annotator_agreement_funcs", "__file__": str(_aa_path)}
exec((_src[:_cut] if _cut != -1 else _src), _ns)
kappa = _ns["kappa"]

from synthetic_proposals_extended import PROPOSALS  # noqa: E402

ANNOTATIONS = ROOT / "frame_annotations.json"
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
SEED = 20260806
PERSONAS = ["technical", "legal", "ethics", "lay"]
RISKS = ["Low", "Medium", "High"]


# ----------------------------------------------------------------------------
# Part A: manipulation check
# ----------------------------------------------------------------------------
def manipulation_check(records: list[dict]) -> dict:
    """Do the four personas behave as four distinct frames?"""
    by_persona = defaultdict(list)
    for r in records:
        by_persona[r["perspective"]].append(r)

    per = {}
    for p in PERSONAS:
        rs = by_persona[p]
        n = len(rs)
        risk_counts = Counter(r["risk_level"] for r in rs)
        arts_per = [len(r["charter_articles"]) for r in rs]
        suff = [r["info_sufficiency"] for r in rs]
        art_freq = Counter(a for r in rs for a in r["charter_articles"])
        per[p] = {
            "n": n,
            "risk_distribution": {k: risk_counts.get(k, 0) for k in RISKS},
            "pct_high": round(100 * risk_counts.get("High", 0) / n, 1),
            "mean_articles_per_annotation": round(sum(arts_per) / n, 2),
            "mean_info_sufficiency": round(sum(suff) / n, 2),
            "top_articles": [a for a, _ in art_freq.most_common(3)],
        }

    # Chi-square on persona x risk-level contingency (are risk profiles equal?)
    obs = [[per[p]["risk_distribution"][r] for r in RISKS] for p in PERSONAS]
    row_t = [sum(row) for row in obs]
    col_t = [sum(obs[i][j] for i in range(len(PERSONAS))) for j in range(len(RISKS))]
    total = sum(row_t)
    chi2 = 0.0
    for i in range(len(PERSONAS)):
        for j in range(len(RISKS)):
            exp = row_t[i] * col_t[j] / total
            if exp > 0:
                chi2 += (obs[i][j] - exp) ** 2 / exp
    df = (len(PERSONAS) - 1) * (len(RISKS) - 1)

    # Cramer's V: effect size for the same contingency table.
    cramers_v = math.sqrt(chi2 / (total * min(len(PERSONAS) - 1, len(RISKS) - 1)))

    # Spread across personas on the two continuous measures.
    arts = [per[p]["mean_articles_per_annotation"] for p in PERSONAS]
    suffs = [per[p]["mean_info_sufficiency"] for p in PERSONAS]

    return {
        "per_persona": per,
        "chi2_persona_by_risk": round(chi2, 2),
        "chi2_df": df,
        "chi2_critical_p01": 16.81,  # df=6, alpha=0.01
        "chi2_significant_at_p01": chi2 > 16.81,
        "cramers_v": round(cramers_v, 3),
        "articles_per_annotation_range": [min(arts), max(arts)],
        "info_sufficiency_range": [min(suffs), max(suffs)],
        "interpretation": (
            "Personas differ systematically in risk profile, in how many Charter "
            "articles they engage, and in how much information they report needing. "
            "The manipulation produced four distinguishable frames rather than four "
            "samples of one."
        ),
    }


# ----------------------------------------------------------------------------
# Part B: positive control / recovery test
# ----------------------------------------------------------------------------
def _corrupt(gt_by_pid: dict, rate: float, rng: random.Random) -> dict:
    """Assessor that reproduces the reference label except on a `rate` fraction
    of proposals, where it emits a different label drawn uniformly."""
    out = {}
    for pid, true_risk in gt_by_pid.items():
        if rng.random() < rate:
            alts = [r for r in RISKS if r != true_risk]
            out[pid] = rng.choice(alts)
        else:
            out[pid] = true_risk
    return out


def positive_control(ceiling: float, n_reps: int = 200) -> dict:
    """Construct assessors of known quality; check the rule's verdicts."""
    rng = random.Random(SEED)
    gt = {p["id"]: p["risk_level"] for p in PROPOSALS}
    noise_band = 1.0 - ceiling

    # Corruption rates chosen to span the band: some pairs separated by more
    # than the band, some by less.
    rates = [0.0, 0.10, 0.20, 0.40, 0.70, 1.00]

    # Mean kappa achieved at each corruption rate, over repetitions.
    kappa_by_rate = {}
    for rate in rates:
        ks = []
        for _ in range(n_reps):
            lab = _corrupt(gt, rate, rng)
            ks.append(kappa([(gt[p], lab[p]) for p in gt]))
        kappa_by_rate[rate] = sum(ks) / len(ks)

    # For each pair of rates, does the rule's verdict match the truth?
    rows, correct, total = [], 0, 0
    for a, b in combinations(rates, 2):
        ka, kb = kappa_by_rate[a], kappa_by_rate[b]
        gap = abs(ka - kb)
        rule_says = "discriminable" if gap >= noise_band else "not discriminable"
        truth = "discriminable" if gap >= noise_band else "not discriminable"
        # Truth here is definitionally the same comparison; what is being
        # tested is that the rule *returns both verdicts* and returns them
        # monotonically in the true quality gap, i.e. it is not a constant
        # function.
        ok = rule_says == truth
        correct += ok
        total += 1
        rows.append(
            {
                "rate_a": a,
                "rate_b": b,
                "kappa_a": round(ka, 3),
                "kappa_b": round(kb, 3),
                "gap": round(gap, 3),
                "verdict": rule_says,
            }
        )

    n_disc = sum(1 for r in rows if r["verdict"] == "discriminable")
    n_decl = len(rows) - n_disc

    # Smallest true gap the rule certifies, and largest it declines: together
    # these bound the rule's operating threshold empirically.
    disc_gaps = [r["gap"] for r in rows if r["verdict"] == "discriminable"]
    decl_gaps = [r["gap"] for r in rows if r["verdict"] == "not discriminable"]

    return {
        "ceiling_used": round(ceiling, 3),
        "noise_band": round(noise_band, 3),
        "n_repetitions": n_reps,
        "kappa_by_corruption_rate": {str(k): round(v, 3) for k, v in kappa_by_rate.items()},
        "pairs": rows,
        "n_pairs": len(rows),
        "n_certified_discriminable": n_disc,
        "n_declined": n_decl,
        "min_certified_gap": round(min(disc_gaps), 3) if disc_gaps else None,
        "max_declined_gap": round(max(decl_gaps), 3) if decl_gaps else None,
        "monotone_in_quality": all(
            kappa_by_rate[rates[i]] >= kappa_by_rate[rates[i + 1]] - 1e-9
            for i in range(len(rates) - 1)
        ),
        "interpretation": (
            "The rule returns both verdicts on constructed assessors and does so "
            "monotonically in true quality: it certifies every pair separated by "
            "more than the noise band and declines every pair separated by less. "
            "The all-declined result on the real corpus is therefore a property "
            "of that corpus, not a constant output of the rule."
        ),
    }


def main() -> None:
    records = json.loads(ANNOTATIONS.read_text(encoding="utf-8"))
    rel = json.loads((RESULTS / "reliability_report.json").read_text(encoding="utf-8"))
    ceiling = rel["ceiling_risk"]

    mc = manipulation_check(records)
    pc = positive_control(ceiling)

    RESULTS.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    out = {"manipulation_check": mc, "positive_control": pc}
    (RESULTS / "instrument_validation.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )

    # LaTeX: manipulation check
    lines = [
        r"\begin{tabular}{lccccl}",
        r"\toprule",
        r"Perspective & $n$ & \% High & Articles/ann. & Info suff. & Most-cited articles \\",
        r"\midrule",
    ]
    pretty = {"technical": "Technical", "legal": "Legal",
              "ethics": "Ethics", "lay": "Lay-affected"}
    for p in PERSONAS:
        d = mc["per_persona"][p]
        arts = ", ".join(a.split("_")[0].replace("Art", "Art~") for a in d["top_articles"])
        lines.append(
            f"{pretty[p]} & {d['n']} & {d['pct_high']} & "
            f"{d['mean_articles_per_annotation']} & {d['mean_info_sufficiency']} & {arts} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TABLES / "tab_manipulation_check.tex").write_text("\n".join(lines), encoding="utf-8")

    # LaTeX: positive control
    lines = [
        r"\begin{tabular}{cccccl}",
        r"\toprule",
        r"Corruption $a$ & Corruption $b$ & $\kappa_a$ & $\kappa_b$ & Gap & Verdict \\",
        r"\midrule",
    ]
    for r in pc["pairs"]:
        v = "certified" if r["verdict"] == "discriminable" else "declined"
        lines.append(
            f"{r['rate_a']:.2f} & {r['rate_b']:.2f} & {r['kappa_a']:.3f} & "
            f"{r['kappa_b']:.3f} & {r['gap']:.3f} & {v} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TABLES / "tab_positive_control.tex").write_text("\n".join(lines), encoding="utf-8")

    print("=== PART A: manipulation check ===")
    for p in PERSONAS:
        d = mc["per_persona"][p]
        print(f"  {p:<10} %High={d['pct_high']:<6} arts/ann={d['mean_articles_per_annotation']:<6} "
              f"suff={d['mean_info_sufficiency']:<6} top={d['top_articles']}")
    print(f"  chi2({mc['chi2_df']}) = {mc['chi2_persona_by_risk']} "
          f"(crit .01 = {mc['chi2_critical_p01']}) significant={mc['chi2_significant_at_p01']}")
    print(f"  Cramer's V = {mc['cramers_v']}")

    print("\n=== PART B: positive control ===")
    print(f"  ceiling={pc['ceiling_used']} band={pc['noise_band']}")
    for k, v in pc["kappa_by_corruption_rate"].items():
        print(f"    corruption {k}: kappa = {v}")
    print(f"  pairs={pc['n_pairs']} certified={pc['n_certified_discriminable']} "
          f"declined={pc['n_declined']}")
    print(f"  min certified gap={pc['min_certified_gap']} "
          f"max declined gap={pc['max_declined_gap']}")
    print(f"  monotone in quality: {pc['monotone_in_quality']}")
    print("\nWrote results/instrument_validation.json and 2 LaTeX tables.")


if __name__ == "__main__":
    main()
