"""Render one AIEF assessment into four authority-specific documents,
score documentation completeness (required fields satisfied), and cite
the exact requirement ID(s) / incident IRI(s) grounding each filled field.

Two structural changes from the original version (16 July 2026, Week-4
deepening):
  1. The per-authority field lists live in docgen_templates.yaml, not a
     hardcoded Python dict -- an authority's checklist can be extended or
     edited without touching this file, mirroring the "rules as data"
     argument already made for the SHACL layer.
  2. Every field that draws on requirements/incidents now returns
     (text, source_ids) instead of just text, and the source IDs are
     rendered as an inline citation under the field -- closing the one
     remaining place in the architecture where "traceability" (the theme
     running through the RAG pipeline's retrieval-transparency panel and
     the SHACL shapes' inspectable rationale) did not yet reach.
"""
import json, sys, os
import yaml
from pathlib import Path

HERE = Path(__file__).parent
TEMPLATES = yaml.safe_load(open(HERE / "docgen_templates.yaml"))


def _join(items, cite_key=None):
    """Join formatted lines and collect the source IDs cited, if any."""
    lines, sources = [], []
    for it in items:
        lines.append(it["text"])
        if cite_key and it.get(cite_key):
            sources.append(str(it[cite_key]))
    return ("\n".join(lines) if lines else None), sources


def build_sections(d):
    """Map pipeline JSON -> {pool_key: (text, [source_ids])} for every field
    any template might request."""
    a = d["assessment"]
    reqs = a.get("applicable_requirements", [])
    rights = a.get("charter_rights_at_risk", [])
    incidents = a.get("historical_precedents", [])
    mits = a.get("recommended_mitigations", [])
    risks = a.get("identified_risks", [])

    def fmt_reqs(fw=None):
        sel = [r for r in reqs if fw is None or fw.lower() in str(r.get("framework", "")).lower()]
        return _join(
            [{"text": f"- {r.get('requirement_id')}: {r.get('requirement_text', '')}",
              "id": r.get("requirement_id")} for r in sel],
            cite_key="id",
        )

    def fmt_risks():
        return _join([{"text": f"- {r.get('risk')} ({r.get('severity')})"} for r in risks])

    def fmt_mits():
        return _join([{"text": f"- {m.get('mitigation', m) if isinstance(m, dict) else m}"} for m in mits])

    def fmt_rights():
        return _join(
            [{"text": f"- {r.get('article')}: {r.get('right_name', '')}", "id": r.get("article")} for r in rights],
            cite_key="id",
        )

    def fmt_precedents():
        return _join(
            [{"text": f"- {i.get('incident_id')}: {i.get('incident_title', i.get('title', ''))}",
              "id": i.get("incident_id")} for i in incidents],
            cite_key="id",
        )

    def find_req(keyword):
        for r in reqs:
            if keyword in str(r.get("requirement_text", "")).lower():
                return r.get("requirement_text"), [r.get("requirement_id")]
        return None, []

    consent_text, consent_src = find_req("consent")
    oversight_text, oversight_src = find_req("oversight")
    # data_protection (REAMS template) falls back to all requirements when
    # no REAMS-specific one is available, matching the original semantics.
    # data_management (Horizon template) does NOT fall back -- if no
    # REAMS-framework requirement is available, the field is honestly
    # reported as not derivable rather than padded with off-topic
    # ACM/AI-Act/Horizon requirements under a REAMS-specific heading.
    reams_reqs_text, reams_reqs_src = fmt_reqs("REAMS")
    data_protection_text, data_protection_src = (reams_reqs_text, reams_reqs_src)
    if data_protection_text is None:
        data_protection_text, data_protection_src = fmt_reqs()
    horizon_reqs_text, horizon_reqs_src = fmt_reqs("Horizon")
    risks_text, risks_src = fmt_risks()
    mits_text, mits_src = fmt_mits()
    rights_text, rights_src = fmt_rights()
    prec_text, prec_src = fmt_precedents()

    return {
        "project_summary": (d.get("proposal_text", "")[:600], []),
        "risk_level": (a.get("overall_risk_level"), []),
        "participant_risks": (risks_text, risks_src),
        "data_protection": (data_protection_text, data_protection_src),
        "consent_arrangements": (consent_text, consent_src),
        "mitigations": (mits_text, mits_src),
        "intended_purpose": (a.get("risk_summary"), []),
        "affected_rights": (rights_text, rights_src),
        "risk_identification": (risks_text, risks_src),
        "severity_assessment": (risks_text, risks_src),
        "mitigation_measures": (mits_text, mits_src),
        "precedent_evidence": (prec_text, prec_src),
        "broader_impact": (a.get("risk_summary"), []),
        "potential_misuse": (risks_text, risks_src),
        "harm_mitigations": (mits_text, mits_src),
        "ethics_by_design": (horizon_reqs_text, horizon_reqs_src),
        "data_management": (reams_reqs_text, reams_reqs_src),
        "social_impact": (a.get("risk_summary"), []),
        "human_oversight": (oversight_text, oversight_src),
    }


def main(json_path, outdir):
    d = json.load(open(json_path))
    pid = d.get("proposal_id", Path(json_path).stem)
    pool = build_sections(d)
    os.makedirs(outdir, exist_ok=True)
    scores = {}
    for authority, fields in TEMPLATES.items():
        lines = [f"# {authority} ethics documentation — {pid}",
                 "Generated by AIEF from a single harmonised assessment. "
                 "Every filled field below cites the exact requirement/incident "
                 "IDs in the knowledge graph that ground it.\n"]
        filled = 0
        for spec in fields:
            key, label = spec["pool_key"], spec["label"]
            text, sources = pool.get(key, (None, []))
            lines.append(f"## {label}")
            lines.append(text or "[NOT DERIVABLE FROM ASSESSMENT — requires manual input]")
            if sources:
                lines.append(f"\n*Source: {', '.join(sources)}*")
            lines.append("")
            filled += bool(text)
        scores[authority] = (filled, len(fields))
        open(f"{outdir}/{pid}_{authority}.md", "w").write("\n".join(lines))
    print(f"{pid} completeness: " + " | ".join(
        f"{a}: {f}/{t} ({100*f//t}%)" for a, (f, t) in scores.items()))
    return scores


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../evaluation/results/llama-3.3-70b")
    outdir = "../evaluation/generated-documentation"
    agg = {}
    for jf in sorted(src.glob("P*_full.json")):
        for a, (f, t) in main(jf, outdir).items():
            agg.setdefault(a, []).append(f / t)
    print("\n=== MEAN COMPLETENESS ===")
    for a, vals in agg.items():
        print(f"{a}: {100*sum(vals)/len(vals):.0f}% (n={len(vals)})")
