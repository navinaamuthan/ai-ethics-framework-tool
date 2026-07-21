"""
reliability_analysis.py
Empirical core of the diagnostic methodology.

KILL_CONDITIONS (pre-registered — do not edit after seeing results):
1. If within-stratum κ ≤ cross-stratum κ: the perspective-based explanation
   for disagreement fails; report honestly that disagreement is not structured
   by perspective in this corpus. The diagnostic's reliability-ceiling
   computation still holds; only the *explanation* for low reliability changes.
2. If EVERY assessor-pair accuracy gap is within the noise band
   (gap < 1 − ceiling) — i.e. no pair is discriminable — then
   reference-based ranking cannot separate any assessors on this corpus;
   report that honestly. If only some pairs (typically near-floor assessors)
   are non-discriminable while others are discriminable, that is partial
   validity / a floor-effect breakdown, not a clean kill.
3. If all four assessors are statistically indistinguishable on every
   property in the property suite: report that the property suite is
   uninformative for this assessor set — an honest limitation, not something
   to hide.

Thesis pinned: An evaluation protocol that scores an automated assessor
against reference labels is itself a measurement instrument, and its validity
depends on conditions — chiefly, the reliability of those reference labels —
that are not currently checked before such protocols are used.

The diagnostic's one job: given an assessor and a labelled corpus, determine
whether agreement-with-reference-labels is a valid basis for evaluating that
assessor on that corpus.
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
EVAL = ROOT.parent / "evaluation" / "results"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

# Import kappa/to_art without executing annotator_agreement's top-level report.
_aa_path = RAG / "annotator_agreement.py"
_src = _aa_path.read_text(encoding="utf-8")
_cut = _src.find('\nprint("=== Annotator')
_ns: dict = {"__name__": "_annotator_agreement_funcs", "__file__": str(_aa_path)}
exec((_src[:_cut] if _cut != -1 else _src), _ns)
kappa = _ns["kappa"]
to_art = _ns["to_art"]

from synthetic_proposals_extended import PROPOSALS  # noqa: E402

ANNOTATIONS_PATH = ROOT / "frame_annotations.json"
REPORT_PATH = ROOT / "results" / "reliability_report.json"

PERSONAS = ["technical", "legal", "ethics", "lay"]
RISK_LEVELS = ["High", "Medium", "Low"]
N_BOOT = 10_000
RNG = random.Random(20260720)

# Cross-stratum uses run 1 only (explicit design choice to avoid combinatorial explosion).
CROSS_RUN = 1


def load_annotations() -> list[dict]:
    if not ANNOTATIONS_PATH.exists():
        raise SystemExit(f"Missing {ANNOTATIONS_PATH}; run frame_annotation.py first.")
    data = json.loads(ANNOTATIONS_PATH.read_text(encoding="utf-8"))
    if len(data) < 456:
        raise SystemExit(f"Only {len(data)} annotation records; need ≥456.")
    return data


def index_annotations(records: list[dict]) -> dict:
    """(perspective, run, proposal_id) -> record"""
    idx = {}
    for r in records:
        idx[(r["perspective"], int(r["run"]), r["proposal_id"])] = r
    return idx


def proposal_ids() -> list[str]:
    return [p["id"] for p in PROPOSALS]


def all_articles(records: list[dict]) -> list[str]:
    arts = set()
    for p in PROPOSALS:
        arts |= {to_art(a) for a in p["expected_charter_articles"]}
    for r in records:
        arts |= {to_art(a) for a in r.get("charter_articles", [])}
    arts.discard(None)
    return sorted(arts)


def risk_pairs_for_runs(
    idx: dict, persona_a: str, run_a: int, persona_b: str, run_b: int, pids: list[str]
) -> list[tuple]:
    pairs = []
    for pid in pids:
        ra = idx.get((persona_a, run_a, pid))
        rb = idx.get((persona_b, run_b, pid))
        if ra is None or rb is None:
            continue
        pairs.append((ra["risk_level"], rb["risk_level"]))
    return pairs


def rights_pairs_for_runs(
    idx: dict,
    persona_a: str,
    run_a: int,
    persona_b: str,
    run_b: int,
    pids: list[str],
    articles: list[str],
) -> list[tuple]:
    pairs = []
    for pid in pids:
        ra = idx.get((persona_a, run_a, pid))
        rb = idx.get((persona_b, run_b, pid))
        if ra is None or rb is None:
            continue
        a_set = {to_art(x) for x in ra["charter_articles"]}
        b_set = {to_art(x) for x in rb["charter_articles"]}
        for art in articles:
            pairs.append((art in a_set, art in b_set))
    return pairs


def bootstrap_ci(
    pairs: list[tuple],
    n: int = N_BOOT,
    seed: int = 20260720,
) -> dict:
    """Resample *proposal-level* blocks when pairs are flat risk pairs.

    For risk: each pair is one proposal → resample pairs.
    For rights: pairs are (proposal × article); we detect block size = len(articles)
    if caller passes block_size, else resample individual decisions (conservative).
    """
    if not pairs:
        return {"mean": float("nan"), "ci95": [float("nan"), float("nan")], "n_pairs": 0}
    rng = random.Random(seed)
    point = kappa(pairs)
    boots = []
    m = len(pairs)
    for _ in range(n):
        sample = [pairs[rng.randrange(m)] for _ in range(m)]
        boots.append(kappa(sample))
    boots.sort()
    lo = boots[int(0.025 * n)]
    hi = boots[int(0.975 * n)]
    return {"mean": point, "ci95": [lo, hi], "n_pairs": m, "boot_mean": sum(boots) / n}


def bootstrap_ci_by_proposal(
    pids: list[str],
    pair_builder,
    n: int = N_BOOT,
    seed: int = 20260720,
) -> dict:
    """Bootstrap by resampling proposals with replacement, then rebuilding pairs."""
    rng = random.Random(seed)
    base_pairs = pair_builder(pids)
    point = kappa(base_pairs) if base_pairs else float("nan")
    boots = []
    m = len(pids)
    for _ in range(n):
        sample_pids = [pids[rng.randrange(m)] for _ in range(m)]
        pairs = pair_builder(sample_pids)
        boots.append(kappa(pairs) if pairs else float("nan"))
    boots = [b for b in boots if not math.isnan(b)]
    boots.sort()
    if not boots:
        return {"mean": point, "ci95": [float("nan"), float("nan")], "n_proposals": m}
    lo = boots[int(0.025 * len(boots))]
    hi = boots[int(0.975 * len(boots))]
    return {
        "mean": point,
        "ci95": [lo, hi],
        "n_proposals": m,
        "boot_mean": sum(boots) / len(boots),
    }


def within_stratum(idx: dict, articles: list[str], pids: list[str]) -> dict:
    raw_risk = {}
    raw_rights = {}
    persona_means_risk = {}
    persona_means_rights = {}

    for persp in PERSONAS:
        risk_ks, rights_ks = [], []
        for ra, rb in combinations((1, 2, 3), 2):
            key = f"{persp}:run{ra}-run{rb}"
            rp = risk_pairs_for_runs(idx, persp, ra, persp, rb, pids)
            rtp = rights_pairs_for_runs(idx, persp, ra, persp, rb, pids, articles)
            rk = kappa(rp) if rp else float("nan")
            rtk = kappa(rtp) if rtp else float("nan")
            raw_risk[key] = rk
            raw_rights[key] = rtk
            if not math.isnan(rk):
                risk_ks.append(rk)
            if not math.isnan(rtk):
                rights_ks.append(rtk)
        persona_means_risk[persp] = sum(risk_ks) / len(risk_ks) if risk_ks else float("nan")
        persona_means_rights[persp] = (
            sum(rights_ks) / len(rights_ks) if rights_ks else float("nan")
        )

    return {
        "raw_pairs_risk": raw_risk,
        "raw_pairs_rights": raw_rights,
        "persona_mean_risk": persona_means_risk,
        "persona_mean_rights": persona_means_rights,
        "mean_within_risk": _nanmean(list(persona_means_risk.values())),
        "mean_within_rights": _nanmean(list(persona_means_rights.values())),
    }


def cross_stratum(idx: dict, articles: list[str], pids: list[str]) -> dict:
    raw_risk, raw_rights = {}, {}
    risk_vals, rights_vals = [], []
    for a, b in combinations(PERSONAS, 2):
        key = f"{a}-vs-{b} (run {CROSS_RUN})"
        rp = risk_pairs_for_runs(idx, a, CROSS_RUN, b, CROSS_RUN, pids)
        rtp = rights_pairs_for_runs(idx, a, CROSS_RUN, b, CROSS_RUN, pids, articles)
        rk = kappa(rp) if rp else float("nan")
        rtk = kappa(rtp) if rtp else float("nan")
        raw_risk[key] = rk
        raw_rights[key] = rtk
        if not math.isnan(rk):
            risk_vals.append(rk)
        if not math.isnan(rtk):
            rights_vals.append(rtk)
    return {
        "note": f"Cross-stratum uses run {CROSS_RUN} only per persona (design choice).",
        "raw_pairs_risk": raw_risk,
        "raw_pairs_rights": raw_rights,
        "mean_cross_risk": _nanmean(risk_vals),
        "mean_cross_rights": _nanmean(rights_vals),
    }


def _nanmean(vals: list[float]) -> float:
    vals = [v for v in vals if v is not None and not math.isnan(v)]
    return sum(vals) / len(vals) if vals else float("nan")


def headline_test(within: dict, cross: dict, idx: dict, articles: list[str], pids: list[str]) -> dict:
    """Bootstrap CIs for mean within vs mean cross (risk and rights)."""

    # Within: average of 12 pairwise κs, bootstrapped by resampling proposals.
    def within_risk_mean(sample_pids):
        ks = []
        for persp in PERSONAS:
            for ra, rb in combinations((1, 2, 3), 2):
                pairs = risk_pairs_for_runs(idx, persp, ra, persp, rb, sample_pids)
                if pairs:
                    ks.append(kappa(pairs))
        return _nanmean(ks)

    def within_rights_mean(sample_pids):
        ks = []
        for persp in PERSONAS:
            for ra, rb in combinations((1, 2, 3), 2):
                pairs = rights_pairs_for_runs(
                    idx, persp, ra, persp, rb, sample_pids, articles
                )
                if pairs:
                    ks.append(kappa(pairs))
        return _nanmean(ks)

    def cross_risk_mean(sample_pids):
        ks = []
        for a, b in combinations(PERSONAS, 2):
            pairs = risk_pairs_for_runs(idx, a, CROSS_RUN, b, CROSS_RUN, sample_pids)
            if pairs:
                ks.append(kappa(pairs))
        return _nanmean(ks)

    def cross_rights_mean(sample_pids):
        ks = []
        for a, b in combinations(PERSONAS, 2):
            pairs = rights_pairs_for_runs(
                idx, a, CROSS_RUN, b, CROSS_RUN, sample_pids, articles
            )
            if pairs:
                ks.append(kappa(pairs))
        return _nanmean(ks)

    def boot_stat(fn, n=N_BOOT, seed=20260720):
        rng = random.Random(seed)
        point = fn(pids)
        boots = []
        m = len(pids)
        for _ in range(n):
            sample = [pids[rng.randrange(m)] for _ in range(m)]
            boots.append(fn(sample))
        boots = [b for b in boots if not math.isnan(b)]
        boots.sort()
        return {
            "mean": point,
            "ci95": [boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]],
        }

    wr = boot_stat(within_risk_mean)
    cr = boot_stat(cross_risk_mean, seed=20260721)
    wri = boot_stat(within_rights_mean, seed=20260722)
    cri = boot_stat(cross_rights_mean, seed=20260723)

    def supported(w, c):
        # within > cross and CIs don't overlap
        if not (w["mean"] > c["mean"]):
            return False
        return w["ci95"][0] > c["ci95"][1]

    risk_ok = supported(wr, cr)
    rights_ok = supported(wri, cri)

    # Kill condition 1: within ≤ cross (primary risk-label test).
    kill1_risk = within["mean_within_risk"] <= cross["mean_cross_risk"]
    directional_risk = within["mean_within_risk"] > cross["mean_cross_risk"]
    cis_overlap_risk = not (wr["ci95"][0] > cr["ci95"][1])

    if risk_ok:
        interpretation = (
            "Frame-hypothesis supported for risk labels: mean(within-stratum κ) > "
            "mean(cross-stratum κ) and bootstrap 95% CIs do not overlap."
        )
    elif kill1_risk:
        interpretation = (
            "Kill condition 1 triggered: mean(within-stratum κ) ≤ mean(cross-stratum κ). "
            "Disagreement is NOT structured by perspective in this corpus. "
            "The reliability-ceiling computation still holds; only the explanation "
            "for low reliability changes."
        )
    elif directional_risk and cis_overlap_risk:
        interpretation = (
            "Directional but inconclusive: mean(within-stratum κ) > mean(cross-stratum κ), "
            "but bootstrap 95% CIs overlap, so the pre-registered non-overlap criterion "
            "for supporting the frame hypothesis is not met. Kill condition 1 is NOT "
            "triggered. Report as suggestive, not confirmatory. Reliability-ceiling "
            "computation still holds."
        )
    else:
        interpretation = "Inconclusive on the frame hypothesis for risk labels."

    return {
        "within_risk": wr,
        "cross_risk": cr,
        "within_rights": wri,
        "cross_rights": cri,
        "frame_hypothesis_supported_risk": risk_ok,
        "frame_hypothesis_supported_rights": rights_ok,
        "kill_condition_1_triggered_risk": kill1_risk,
        "directional_within_gt_cross_risk": directional_risk,
        "cis_overlap_risk": cis_overlap_risk,
        "interpretation": interpretation,
    }


def info_sufficiency_filter(records: list[dict], idx: dict, articles: list[str]) -> dict:
    by_pid = defaultdict(list)
    for r in records:
        by_pid[r["proposal_id"]].append(r["info_sufficiency"])

    mean_info = {pid: sum(vs) / len(vs) for pid, vs in by_pid.items()}
    high = [pid for pid, m in mean_info.items() if m >= 3]
    low = [pid for pid, m in mean_info.items() if m < 3]

    def subset_block(pids):
        if len(pids) < 3:
            return {"n": len(pids), "note": "too few proposals for stable κ"}
        w = within_stratum(idx, articles, pids)
        c = cross_stratum(idx, articles, pids)
        return {
            "n": len(pids),
            "mean_within_risk": w["mean_within_risk"],
            "mean_cross_risk": c["mean_cross_risk"],
            "mean_within_rights": w["mean_within_rights"],
            "mean_cross_rights": c["mean_cross_rights"],
            "proposal_ids": sorted(pids),
        }

    # Quadrants need agreement measure per proposal: use pairwise risk agreement
    # across all annotation pairs for that proposal.
    agreement = {}
    for pid in mean_info:
        labels = [
            r["risk_level"]
            for r in records
            if r["proposal_id"] == pid
        ]
        if len(labels) < 2:
            continue
        # mean pairwise agreement
        pairs = list(combinations(labels, 2))
        agreement[pid] = sum(a == b for a, b in pairs) / len(pairs)

    # Low agreement threshold: below median
    if agreement:
        med = sorted(agreement.values())[len(agreement) // 2]
    else:
        med = 0.5

    quadrants = {
        "ambiguous_low_info_low_agree": [],
        "contested_high_info_low_agree": [],
        "clear_high_info_high_agree": [],
        "noisy_low_info_high_agree": [],
    }
    for pid, info in mean_info.items():
        agr = agreement.get(pid, 0.0)
        low_agr = agr < med
        if info < 3 and low_agr:
            quadrants["ambiguous_low_info_low_agree"].append(pid)
        elif info >= 3 and low_agr:
            quadrants["contested_high_info_low_agree"].append(pid)
        elif info >= 3 and not low_agr:
            quadrants["clear_high_info_high_agree"].append(pid)
        else:
            quadrants["noisy_low_info_high_agree"].append(pid)

    return {
        "mean_info_by_proposal": mean_info,
        "agreement_by_proposal": agreement,
        "agreement_median_threshold": med,
        "info_ge_3": subset_block(high),
        "info_lt_3": subset_block(low),
        "quadrants": quadrants,
        "criticism_5_note": (
            "Low-sufficiency + low agreement ≈ ambiguous; "
            "high-sufficiency + low agreement ≈ genuinely contested."
        ),
    }


def load_assessor_labels() -> dict:
    """Load assessor risk/rights labels from existing evaluation outputs.

    SHACL is computed on the fly from proposal text via the SHACL pipeline when
    available. Keyword baseline is a simple keyword→risk heuristic. LLM labels
    come from evaluation/results/{model}/P##_full.json.

    Returns {assessor_name: {pid: {risk, rights:set}}}.
    Missing proposals are omitted (decision rule uses intersection).
    """
    assessors: dict[str, dict] = {}

    # Prefer full-corpus outputs under evaluation/results; fall back to variance.
    model_dirs = {
        "LLM-8B": [
            EVAL / "llama-3.1-8b",
            ROOT.parent / "evaluation" / "variance" / "8b_run1",
            ROOT / "results" / "assessor_llm8b",
        ],
        "LLM-70B": [
            EVAL / "llama-3.3-70b",
            ROOT.parent / "evaluation" / "variance" / "70b_run1",
            ROOT / "results" / "assessor_llm70b",
        ],
    }
    for name, dirs in model_dirs.items():
        labels = {}
        for d in dirs:
            if not d.exists():
                continue
            for p in PROPOSALS:
                if p["id"] in labels:
                    continue
                f = d / f"{p['id']}_full.json"
                if not f.exists():
                    continue
                data = json.loads(f.read_text(encoding="utf-8"))
                assessment = data.get("assessment") or {}
                if not isinstance(assessment, dict):
                    assessment = {}
                risk = assessment.get("overall_risk_level") or data.get("overall_risk_level")
                if risk not in RISK_LEVELS and isinstance(risk, str):
                    for cand in RISK_LEVELS:
                        if cand.lower() in risk.lower():
                            risk = cand
                            break
                if risk not in RISK_LEVELS:
                    severities = [
                        (item.get("severity") or "")
                        for item in (assessment.get("identified_risks") or [])
                        if isinstance(item, dict)
                    ]
                    sev_l = " ".join(severities).lower()
                    if "high" in sev_l:
                        risk = "High"
                    elif "medium" in sev_l or "moderate" in sev_l:
                        risk = "Medium"
                    elif severities:
                        risk = "Low"
                # Assessor rights = LLM assessment output ONLY.
                # Do NOT union retrieval matched_rights — that is keyword→article
                # retrieval, identical across models for the same proposal text,
                # and was collapsing rights_kappa to the same value for 8B/70B.
                rights = set()
                for item in assessment.get("charter_rights_at_risk") or []:
                    if isinstance(item, dict):
                        art = to_art(item.get("article") or item.get("right_name") or "")
                    else:
                        art = to_art(item)
                    if art:
                        rights.add(art)
                if risk in RISK_LEVELS:
                    labels[p["id"]] = {"risk": risk, "rights": set(rights)}
        if labels:
            assessors[name] = labels

    # Keyword baseline: flag High if discrimination/surveillance keywords present
    KEYWORDS_HIGH = [
        "bias", "discriminat", "surveill", "facial recognition", "recidivism",
        "weapon", "child", "biometric", "predictive policing",
    ]
    KEYWORDS_MED = [
        "consent", "privacy", "personal data", "monitoring", "algorithm",
    ]
    kw_labels = {}
    for p in PROPOSALS:
        text = p["proposal_text"].lower()
        if any(k in text for k in KEYWORDS_HIGH):
            risk = "High"
        elif any(k in text for k in KEYWORDS_MED):
            risk = "Medium"
        else:
            risk = "Low"
        rights = set()
        # crude rights from keywords
        mapping = [
            ("discriminat", "Article21"),
            ("bias", "Article21"),
            ("privacy", "Article8"),
            ("personal data", "Article8"),
            ("surveill", "Article7"),
            ("child", "Article24"),
            ("expression", "Article11"),
            ("health", "Article35"),
            ("consent", "Article8"),
        ]
        for needle, art in mapping:
            if needle in text:
                rights.add(art)
        kw_labels[p["id"]] = {"risk": risk, "rights": rights}
    assessors["keyword-baseline"] = kw_labels

    # SHACL: try to run lightweight dimension flags
    try:
        assessors["SHACL"] = _shacl_labels()
    except Exception as e:
        print(f"  [WARN] SHACL labels unavailable: {e}")

    return assessors


def _shacl_labels() -> dict:
    import rdflib
    from pyshacl import validate

    shacl_dir = ROOT.parent / "shacl"
    sys.path.insert(0, str(shacl_dir))
    from text_to_description import describe  # type: ignore

    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    AIEFSH = rdflib.Namespace("https://w3id.org/aief/shapes#")
    shapes = rdflib.Graph().parse(shacl_dir / "aief-risk-shapes.ttl", format="turtle")
    dim_of = {
        s: shapes.value(s, AIEFSH.riskDimension)
        for s in shapes.subjects(rdflib.RDF.type, SH.NodeShape)
    }

    labels = {}
    for p in PROPOSALS:
        data = rdflib.Graph().parse(data=describe(p["proposal_text"]), format="turtle")
        _, rep, _ = validate(data, shacl_graph=shapes, advanced=True, inference="none")
        flagged = set()
        for r in rep.subjects(rdflib.RDF.type, SH.ValidationResult):
            art = to_art(dim_of.get(rep.value(r, SH.sourceShape)))
            if art:
                flagged.add(art)
        # Map flag count to risk level (heuristic aligned with prior SHACL eval practice)
        n = len(flagged)
        if n >= 4:
            risk = "High"
        elif n >= 2:
            risk = "Medium"
        else:
            risk = "Low"
        labels[p["id"]] = {"risk": risk, "rights": flagged}
    return labels


def assessor_vs_gt(assessors: dict) -> dict:
    gt = {p["id"]: p for p in PROPOSALS}
    out = {}
    for name, labels in assessors.items():
        risk_pairs = []
        rights_pairs = []
        arts = sorted(
            {
                to_art(a)
                for p in PROPOSALS
                for a in p["expected_charter_articles"]
            }
            - {None}
        )
        for pid, lab in labels.items():
            if pid not in gt:
                continue
            risk_pairs.append((gt[pid]["risk_level"], lab["risk"]))
            gset = {to_art(a) for a in gt[pid]["expected_charter_articles"]}
            aset = lab["rights"]
            for art in arts:
                rights_pairs.append((art in gset, art in aset))
        out[name] = {
            "n_proposals": len(labels),
            "risk_kappa": kappa(risk_pairs) if risk_pairs else float("nan"),
            "rights_kappa": kappa(rights_pairs) if rights_pairs else float("nan"),
        }
    return out


def decision_rule(ceiling: float, assessor_kappas: dict) -> dict:
    """If |κ_a − κ_b| < (1 − ceiling), pair is not discriminable by accuracy."""
    names = sorted(assessor_kappas)
    noise_band = 1.0 - ceiling if not math.isnan(ceiling) else float("nan")
    rows = []
    for a, b in combinations(names, 2):
        ka = assessor_kappas[a]["risk_kappa"]
        kb = assessor_kappas[b]["risk_kappa"]
        if math.isnan(ka) or math.isnan(kb):
            gap = float("nan")
            verdict = "missing_data"
        else:
            gap = abs(ka - kb)
            verdict = (
                "not_discriminable"
                if gap < noise_band
                else "discriminable"
            )
        rows.append(
            {
                "assessor_a": a,
                "assessor_b": b,
                "kappa_a": ka,
                "kappa_b": kb,
                "gap": gap,
                "noise_band_1_minus_ceiling": noise_band,
                "verdict": verdict,
            }
        )

    gaps = [r["gap"] for r in rows if not math.isnan(r["gap"])]
    n_disc = sum(1 for r in rows if r["verdict"] == "discriminable")
    n_not = sum(1 for r in rows if r["verdict"] == "not_discriminable")
    # Kill condition 2: EVERY finite gap falls inside the noise band.
    kill2 = bool(gaps) and all(g < noise_band for g in gaps)

    if kill2:
        note = (
            "All assessor-pair gaps are within the noise band (1−ceiling); "
            "accuracy cannot discriminate any pair on this corpus."
        )
    elif n_not > 0 and n_disc > 0:
        note = (
            f"Partial validity / floor-effect breakdown: {n_disc} pair(s) "
            f"discriminable, {n_not} not_discriminable (typically near-floor "
            f"assessors whose gap < noise band). Accuracy-based ranking is "
            f"valid for the discriminable pairs only."
        )
    elif n_disc > 0 and n_not == 0:
        note = (
            "Every assessor pair is discriminable (all gaps ≥ noise band); "
            "accuracy-based ranking is valid for this assessor set."
        )
    else:
        note = "Insufficient assessor-pair data to evaluate kill condition 2."

    return {
        "ceiling": ceiling,
        "noise_band": noise_band,
        "pairs": rows,
        "n_discriminable": n_disc,
        "n_not_discriminable": n_not,
        "kill_condition_2_triggered": kill2,
        "kill_condition_2_note": note,
    }


def leave_one_out(idx: dict, articles: list[str], pids: list[str]) -> dict:
    within_risks, cross_risks = [], []
    ceilings = []
    for hold in pids:
        subset = [p for p in pids if p != hold]
        w = within_stratum(idx, articles, subset)
        c = cross_stratum(idx, articles, subset)
        within_risks.append(w["mean_within_risk"])
        cross_risks.append(c["mean_cross_risk"])
        ceilings.append(max(w["persona_mean_risk"].values()))
    return {
        "n_reruns": len(pids),
        "within_risk_min": min(within_risks),
        "within_risk_max": max(within_risks),
        "cross_risk_min": min(cross_risks),
        "cross_risk_max": max(cross_risks),
        "ceiling_min": min(ceilings),
        "ceiling_max": max(ceilings),
    }


def d_study(within_kappa: float, n_obs: int, targets=(60, 100)) -> dict:
    """Spearman-Brown prophecy: ρ* = (k ρ) / (1 + (k−1) ρ) where k = n*/n."""
    out = {"formula": "Spearman-Brown: ρ* = (kρ)/(1+(k-1)ρ), k=n*/n_obs", "n_obs": n_obs}
    if math.isnan(within_kappa) or n_obs <= 0:
        return out
    for n_star in targets:
        k = n_star / n_obs
        rho = (k * within_kappa) / (1 + (k - 1) * within_kappa)
        out[f"projected_n{n_star}"] = rho
    return out


def _jsonable(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonable(v) for v in obj]
    return obj


def main() -> None:
    print("=" * 72)
    print("Diagnostic methodology — reliability analysis")
    print("=" * 72)

    records = load_annotations()
    idx = index_annotations(records)
    pids = proposal_ids()
    articles = all_articles(records)
    print(f"Loaded {len(records)} annotations; {len(pids)} proposals; {len(articles)} articles.")

    within = within_stratum(idx, articles, pids)
    cross = cross_stratum(idx, articles, pids)
    headline = headline_test(within, cross, idx, articles, pids)
    info = info_sufficiency_filter(records, idx, articles)

    ceiling_risk = max(within["persona_mean_risk"].values())
    ceiling_rights = max(within["persona_mean_rights"].values())

    print("\n--- Within-stratum (persona means) ---")
    for p, v in within["persona_mean_risk"].items():
        print(f"  {p}: risk κ={v:.3f}  rights κ={within['persona_mean_rights'][p]:.3f}")
    print(f"  MEAN within risk={within['mean_within_risk']:.3f}  rights={within['mean_within_rights']:.3f}")

    print("\n--- Cross-stratum (run 1) ---")
    print(f"  MEAN cross risk={cross['mean_cross_risk']:.3f}  rights={cross['mean_cross_rights']:.3f}")

    print("\n--- Headline test (bootstrap 95% CIs, 10k) ---")
    print(
        f"  within risk {headline['within_risk']['mean']:.3f} "
        f"CI{headline['within_risk']['ci95']}"
    )
    print(
        f"  cross  risk {headline['cross_risk']['mean']:.3f} "
        f"CI{headline['cross_risk']['ci95']}"
    )
    print(f"  {headline['interpretation']}")
    print(f"  kill_condition_1_triggered_risk={headline['kill_condition_1_triggered_risk']}")

    print("\n--- Info-sufficiency filter ---")
    print(f"  info≥3: n={info['info_ge_3'].get('n')} within={info['info_ge_3'].get('mean_within_risk')} cross={info['info_ge_3'].get('mean_cross_risk')}")
    print(f"  info<3: n={info['info_lt_3'].get('n')} within={info['info_lt_3'].get('mean_within_risk')} cross={info['info_lt_3'].get('mean_cross_risk')}")
    for q, ids in info["quadrants"].items():
        print(f"  {q}: {ids}")

    print("\n--- Assessor vs GT + decision rule ---")
    assessors = load_assessor_labels()
    a_vs_gt = assessor_vs_gt(assessors)
    for name, row in a_vs_gt.items():
        print(f"  {name}: n={row['n_proposals']} riskκ={row['risk_kappa']:.3f} rightsκ={row['rights_kappa']:.3f}")

    decision = decision_rule(ceiling_risk, a_vs_gt)
    print(f"  ceiling (max within-stratum risk κ)={ceiling_risk:.3f}")
    print(f"  noise band (1−ceiling)={decision['noise_band']:.3f}")
    print(f"  kill_condition_2_triggered={decision['kill_condition_2_triggered']}")
    for row in decision["pairs"]:
        print(
            f"    {row['assessor_a']} vs {row['assessor_b']}: "
            f"gap={row['gap'] if row['gap'] is None or isinstance(row['gap'], str) else f'{row['gap']:.3f}'} "
            f"→ {row['verdict']}"
        )

    print("\n--- LOO + D-study ---")
    loo = leave_one_out(idx, articles, pids)
    print(
        f"  LOO within risk [{loo['within_risk_min']:.3f}, {loo['within_risk_max']:.3f}]  "
        f"cross [{loo['cross_risk_min']:.3f}, {loo['cross_risk_max']:.3f}]"
    )
    dstudy = d_study(within["mean_within_risk"], n_obs=len(pids))
    print(f"  D-study: {dstudy}")

    report = {
        "n_annotations": len(records),
        "n_proposals": len(pids),
        "cross_run_choice": CROSS_RUN,
        "within_stratum": within,
        "cross_stratum": cross,
        "headline_test": headline,
        "info_sufficiency": info,
        "ceiling_risk": ceiling_risk,
        "ceiling_rights": ceiling_rights,
        "assessor_vs_gt": a_vs_gt,
        "decision_rule": decision,
        "leave_one_out": loo,
        "d_study": dstudy,
        "kill_conditions": {
            "1_within_le_cross_risk": headline["kill_condition_1_triggered_risk"],
            "2_all_gaps_within_noise_band": decision["kill_condition_2_triggered"],
            "2_note": decision["kill_condition_2_note"],
            "3_property_suite": "evaluated in property_evaluator.py (Step 5)",
        },
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(_jsonable(report), indent=2), encoding="utf-8")
    print(f"\nWrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
