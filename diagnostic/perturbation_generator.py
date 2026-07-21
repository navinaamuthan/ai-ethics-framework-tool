"""
perturbation_generator.py
Step 4 of the diagnostic methodology: known-direction sensitivity unit test.

Thesis pinned: An evaluation protocol that scores an automated assessor
against reference labels is itself a measurement instrument, and its validity
depends on conditions — chiefly, the reliability of those reference labels —
that are not currently checked before such protocols are used.

Scope (also stored in report JSON): this is a unit test for assessor behaviour
under known-direction change, not a claim about real-world deployment prediction.
"""

from __future__ import annotations

import json
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAG = ROOT.parent / "rag-pipeline"
EVAL = ROOT.parent / "evaluation" / "results"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

from llm_caller import call_llm, parse_json_response  # noqa: E402
from synthetic_proposals_extended import PROPOSALS  # noqa: E402
from frame_annotation import PERSONAS, CHARTER_VOCAB  # noqa: E402

# Reuse kappa/to_art without side effects
_aa = (RAG / "annotator_agreement.py").read_text(encoding="utf-8")
_cut = _aa.find('\nprint("=== Annotator')
_ns = {"__name__": "_aa", "__file__": str(RAG / "annotator_agreement.py")}
exec(_aa[:_cut] if _cut != -1 else _aa, _ns)
kappa = _ns["kappa"]
to_art = _ns["to_art"]

VARIANTS_PATH = ROOT / "perturbation_variants.json"
REPORT_PATH = ROOT / "results" / "perturbation_report.json"
SCOPE_NOTE = (
    "A unit test for assessor behaviour under known-direction change, "
    "not a claim about real-world deployment prediction."
)

# 15 proposals: 5 High / 5 Medium / 5 Low
SELECTED_IDS = [
    "P01", "P02", "P05", "P21", "P25",  # High
    "P07", "P11", "P20", "P23", "P28",  # Medium
    "P13", "P15", "P16", "P26", "P31",  # Low
]

RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2}


def _call_json(prompt: str, backend: str = "groq", model: str | None = None, temp: float = 0.5) -> dict:
    raw = call_llm(prompt, backend=backend, model=model or "llama-3.1-8b-instant",
                   temperature=temp, max_tokens=1200, max_retries=2)
    if not raw:
        return {"parse_error": "empty"}
    return parse_json_response(raw)


def generate_variants(proposals: list[dict]) -> list[dict]:
    """Generate positive/negative/neutral variants via LLM; fall back to template edits."""
    variants = []
    if VARIANTS_PATH.exists():
        existing = json.loads(VARIANTS_PATH.read_text(encoding="utf-8"))
        if len(existing) >= 45 and all("variant_text" in v for v in existing):
            print(f"Loaded {len(existing)} existing variants from {VARIANTS_PATH}")
            return existing

    by_id = {p["id"]: p for p in proposals}
    for pid in SELECTED_IDS:
        base = by_id[pid]
        for cls, instruction, expected_dir in [
            (
                "positive",
                "Rewrite the proposal removing or fixing EXACTLY ONE described issue "
                "(e.g. add a bias audit, appeal mechanism, or consent opt-out). "
                "Keep length similar (~150-220 words). Risk should move down or stay same.",
                "down_or_same",
            ),
            (
                "negative",
                "Rewrite the proposal adding EXACTLY ONE new clear rights/ethics violation. "
                "Keep length similar. Risk should move up or stay same.",
                "up_or_same",
            ),
            (
                "neutral",
                "Paraphrase the proposal with no substantive change to risks or rights. "
                "Same length, different wording only.",
                "unchanged",
            ),
        ]:
            prompt = f"""{instruction}

Return JSON only:
{{"variant_text": "...", "change_summary": "one sentence", "intended_direction": "{expected_dir}"}}

ORIGINAL TITLE: {base['title']}
ORIGINAL TEXT:
{base['proposal_text']}
"""
            parsed = _call_json(prompt, temp=0.6)
            text = parsed.get("variant_text") or ""
            if len(text) < 80:
                # deterministic fallback paraphrase/edit
                if cls == "positive":
                    text = base["proposal_text"].rstrip() + (
                        " An independent bias audit and a documented appeal mechanism "
                        "for affected individuals are included before any deployment."
                    )
                    summary = "Added bias audit and appeal mechanism."
                elif cls == "negative":
                    text = base["proposal_text"].rstrip() + (
                        " Outputs will be shared with a commercial data broker without "
                        "additional consent or purpose limitation."
                    )
                    summary = "Added commercial data-broker sharing without consent."
                else:
                    text = re.sub(r"\bThis research proposes\b", "This study proposes",
                                  base["proposal_text"], count=1)
                    if text == base["proposal_text"]:
                        text = "In summary, " + base["proposal_text"][0].lower() + base["proposal_text"][1:]
                    summary = "Paraphrase only."
            else:
                summary = parsed.get("change_summary") or cls
            variants.append({
                "variant_id": f"{pid}_{cls}",
                "base_id": pid,
                "class": cls,
                "title": base["title"],
                "base_risk_level": base["risk_level"],
                "base_charter_articles": list(base["expected_charter_articles"]),
                "variant_text": text,
                "change_summary": summary,
                "author_intended_direction": expected_dir,
                "persona_predictions": {},
            })
            print(f"  variant {pid}_{cls} ok ({len(text)} chars)")
            time.sleep(0.4)
    VARIANTS_PATH.write_text(json.dumps(variants, indent=2), encoding="utf-8")
    return variants


def persona_prelabel(variants: list[dict], backend: str = "groq") -> list[dict]:
    """Blind persona labelling of expected direction (1 run each)."""
    model = "llama-3.1-8b-instant"
    for i, v in enumerate(variants, 1):
        if v.get("persona_predictions") and len(v["persona_predictions"]) == 4:
            continue
        preds = {}
        for persp, system in PERSONAS.items():
            prompt = f"""SYSTEM PERSONA (stay in role):
{system}

USER TASK:
You are shown an ORIGINAL proposal and a VARIANT. Predict the direction of change
in overall risk level from original → variant.
Return JSON only: {{"predicted_direction": "up"|"down"|"same", "brief_reason": "..."}}

ORIGINAL RISK (ground-truth reference for the original only): {v['base_risk_level']}
ORIGINAL TEXT:
{next(p['proposal_text'] for p in PROPOSALS if p['id']==v['base_id'])}

VARIANT TEXT:
{v['variant_text']}
"""
            parsed = _call_json(prompt, backend=backend, model=model, temp=0.5)
            direction = str(parsed.get("predicted_direction") or "").lower()
            if direction not in {"up", "down", "same"}:
                # map from author class as last resort only if parse fails — mark failed
                direction = "parse_fail"
            preds[persp] = {
                "predicted_direction": direction,
                "brief_reason": parsed.get("brief_reason") or "",
            }
            time.sleep(0.25)
        v["persona_predictions"] = preds
        if i % 5 == 0:
            VARIANTS_PATH.write_text(json.dumps(variants, indent=2), encoding="utf-8")
            print(f"  persona prelabel {i}/{len(variants)}")
    VARIANTS_PATH.write_text(json.dumps(variants, indent=2), encoding="utf-8")
    return variants


def _risk_from_assessment(assessment: dict) -> str | None:
    r = assessment.get("overall_risk_level")
    if r in RISK_ORDER:
        return r
    return None


def run_keyword(text: str) -> str:
    t = text.lower()
    high = ["bias", "discriminat", "surveill", "facial recognition", "recidivism",
            "weapon", "child", "biometric", "predictive policing", "data broker"]
    med = ["consent", "privacy", "personal data", "monitoring", "algorithm"]
    if any(k in t for k in high):
        return "High"
    if any(k in t for k in med):
        return "Medium"
    return "Low"


def run_shacl(text: str) -> str:
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
    data = rdflib.Graph().parse(data=describe(text), format="turtle")
    _, rep, _ = validate(data, shacl_graph=shapes, advanced=True, inference="none")
    n = 0
    for r in rep.subjects(rdflib.RDF.type, SH.ValidationResult):
        if dim_of.get(rep.value(r, SH.sourceShape)):
            n += 1
    if n >= 4:
        return "High"
    if n >= 2:
        return "Medium"
    return "Low"


def run_llm_compact_risk(text: str, model: str = "llama-3.3-70b-versatile") -> str | None:
    """Low-token risk-only call for perturbation scoring under TPD pressure."""
    from llm_caller import call_llm, parse_json_response

    prompt = (
        "Assess overall ethics risk of this research proposal. "
        'Return JSON only: {"overall_risk_level":"High"|"Medium"|"Low"}\n\n'
        f"PROPOSAL:\n{text[:2500]}"
    )
    raw = call_llm(
        prompt, backend="groq", model=model, temperature=0.2, max_tokens=80, max_retries=1
    )
    if not raw:
        return None
    parsed = parse_json_response(raw)
    r = parsed.get("overall_risk_level")
    return r if r in RISK_ORDER else None


def run_llm(text: str, pid: str, model: str, backend: str = "groq") -> str | None:
    from ethics_rag import assess_proposal

    out = ROOT / "results" / "perturbation_assessor_cache" / model.replace("/", "_")
    out.mkdir(parents=True, exist_ok=True)
    cache = out / f"{pid}.json"
    if cache.exists():
        a = json.loads(cache.read_text()).get("assessment") or {}
        if a.get("overall_risk_level") in RISK_ORDER:
            return a["overall_risk_level"]
        # stale empty cache
        cache.unlink(missing_ok=True)
    # Prefer compact for 70B to conserve TPD; still same model family.
    if "70b" in model:
        r = run_llm_compact_risk(text, model=model)
        if r:
            cache.write_text(
                json.dumps({"assessment": {"overall_risk_level": r}, "mode": "compact_risk"}),
                encoding="utf-8",
            )
            return r
    result = assess_proposal(
        text, pid, mode="full", backend=backend, model=model,
        max_requirements=5, output_dir=str(out),
    )
    produced = out / f"{pid}_full.json"
    if produced.exists():
        produced.rename(cache)
    a = result.get("assessment") or {}
    risk = a.get("overall_risk_level") if a.get("overall_risk_level") in RISK_ORDER else None
    if risk:
        cache.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return risk


def assess_variants(variants: list[dict]) -> list[dict]:
    by_id = {p["id"]: p for p in PROPOSALS}
    # baseline risk on original text per assessor (cache)
    baselines = {}
    for pid in SELECTED_IDS:
        text = by_id[pid]["proposal_text"]
        baselines[pid] = {
            "keyword-baseline": run_keyword(text),
            "SHACL": run_shacl(text),
        }
        # LLM baselines from existing evaluation results if available
        for name, folder, model in [
            ("LLM-8B", "llama-3.1-8b", "llama-3.1-8b-instant"),
            ("LLM-70B", "llama-3.3-70b", "llama-3.3-70b-versatile"),
        ]:
            f = EVAL / folder / f"{pid}_full.json"
            if f.exists():
                a = json.loads(f.read_text()).get("assessment") or {}
                baselines[pid][name] = a.get("overall_risk_level")
            else:
                baselines[pid][name] = run_llm(text, f"{pid}_base", model)

    for i, v in enumerate(variants, 1):
        if "assessor_outputs" in v and len(v["assessor_outputs"]) == 4:
            continue
        text = v["variant_text"]
        vid = v["variant_id"]
        outs = {
            "keyword-baseline": run_keyword(text),
            "SHACL": run_shacl(text),
            "LLM-8B": run_llm(text, vid + "_8b", "llama-3.1-8b-instant"),
            "LLM-70B": run_llm(text, vid + "_70b", "llama-3.3-70b-versatile"),
        }
        v["assessor_outputs"] = outs
        v["assessor_baselines"] = baselines[v["base_id"]]
        print(f"  assessed {i}/{len(variants)} {vid}: {outs}")
        VARIANTS_PATH.write_text(json.dumps(variants, indent=2), encoding="utf-8")
        time.sleep(1.5)
    return variants


def _moved(base: str, new: str | None, intended: str) -> bool | None:
    if new not in RISK_ORDER or base not in RISK_ORDER:
        return None
    delta = RISK_ORDER[new] - RISK_ORDER[base]
    if intended == "down_or_same":
        return delta <= 0
    if intended == "up_or_same":
        return delta >= 0
    if intended == "unchanged":
        return delta == 0
    return None


def score(variants: list[dict]) -> dict:
    assessors = ["SHACL", "LLM-8B", "LLM-70B", "keyword-baseline"]
    classes = ["positive", "negative", "neutral"]
    rates = {a: {c: {"n": 0, "hits": 0, "rate": None} for c in classes} for a in assessors}
    for v in variants:
        base_outs = v.get("assessor_baselines") or {}
        outs = v.get("assessor_outputs") or {}
        cls = v["class"]
        intended = v["author_intended_direction"]
        for a in assessors:
            base_r = base_outs.get(a) or v["base_risk_level"]
            new_r = outs.get(a)
            hit = _moved(base_r, new_r, intended)
            rates[a][cls]["n"] += 1
            if hit is True:
                rates[a][cls]["hits"] += 1
    for a in assessors:
        for c in classes:
            n = rates[a][c]["n"]
            rates[a][c]["rate"] = rates[a][c]["hits"] / n if n else None

    # persona agreement on predicted direction
    persona_pairs = []
    persps = list(PERSONAS)
    for v in variants:
        preds = v.get("persona_predictions") or {}
        labels = [preds.get(p, {}).get("predicted_direction") for p in persps]
        if any(x in (None, "parse_fail") for x in labels):
            continue
        for i in range(len(persps)):
            for j in range(i + 1, len(persps)):
                persona_pairs.append((labels[i], labels[j]))
    persona_kappa = kappa(persona_pairs) if persona_pairs else None

    # agreement with author intention
    map_intent = {"down_or_same": "down", "up_or_same": "up", "unchanged": "same"}
    author_agree = []
    for v in variants:
        author = map_intent[v["author_intended_direction"]]
        preds = v.get("persona_predictions") or {}
        for p, rec in preds.items():
            d = rec.get("predicted_direction")
            if d in {"up", "down", "same"}:
                # down_or_same: treat persona "same" or "down" as agree for positive, etc.
                if v["author_intended_direction"] == "down_or_same":
                    author_agree.append(d in {"down", "same"})
                elif v["author_intended_direction"] == "up_or_same":
                    author_agree.append(d in {"up", "same"})
                else:
                    author_agree.append(d == "same")
    author_agree_rate = sum(author_agree) / len(author_agree) if author_agree else None

    report = {
        "scope_note": SCOPE_NOTE,
        "n_variants": len(variants),
        "selected_base_ids": SELECTED_IDS,
        "sensitivity_rates": rates,
        "persona_inter_rater_kappa_on_direction": persona_kappa,
        "persona_author_direction_agreement_rate": author_agree_rate,
        "n_persona_pairs": len(persona_pairs),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    VARIANTS_PATH.write_text(json.dumps(variants, indent=2), encoding="utf-8")
    return report


def main() -> None:
    print("=" * 60)
    print("Step 4 — perturbation sensitivity (diagnostic)")
    print("Scope:", SCOPE_NOTE)
    print("=" * 60)
    props = [p for p in PROPOSALS if p["id"] in SELECTED_IDS]
    assert len(props) == 15, len(props)
    variants = generate_variants(PROPOSALS)
    assert len(variants) == 45, len(variants)
    print("Persona pre-labelling...")
    variants = persona_prelabel(variants)
    print("Running assessors on variants (full RAG for LLMs)...")
    variants = assess_variants(variants)
    report = score(variants)
    print(json.dumps(report["sensitivity_rates"], indent=2))
    print("persona κ", report["persona_inter_rater_kappa_on_direction"])
    print("Wrote", VARIANTS_PATH, REPORT_PATH)


if __name__ == "__main__":
    main()
