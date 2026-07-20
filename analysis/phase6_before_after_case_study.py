"""
Phase 6 — before/after case study for the AIEF risk-category + Charter fix.

Compares OLD retrieval behaviour (keyword map + unconditional Art8/Art41,
no disambiguation, no risk categories) against NEW behaviour (Phase 1–3)
for the expert-reviewed proposals: P01, P03, P06, P08, P13.

Also scores existing evaluation JSON outputs for E8 risk-category miss
where risk_category fields are present.

Usage:
  python analysis/phase6_before_after_case_study.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "rag-pipeline"))

from synthetic_proposals import PROPOSALS  # noqa: E402
from sparql_retrieval import (  # noqa: E402
    KEYWORD_TO_RIGHTS,
    extract_keywords,
    get_matched_rights,
    retrieve_all_for_proposal,
    set_retrieval_backend,
)

CASE_IDS = ["P01", "P03", "P06", "P08", "P13"]
OUT_DIR = Path(__file__).parent / "results"
OUT_DIR.mkdir(exist_ok=True)

# Snapshot of pre-Phase-3 always-injected rights (for the "before" column)
_OLD_ALWAYS = {"Art41_GoodAdministration", "Art8_DataProtection"}


def old_matched_rights(proposal: str) -> list:
    """Reproduce pre-fix Charter matching (no Art12/Art31 extras beyond employ,
    always inject Art41+Art8, no bias disambiguation)."""
    # Use a frozen keyword map without Phase-3-only keys for fairness on Art12/Art31 demo,
    # but keep employ→Art31 as it existed; exclude new keys.
    old_keys = {
        k: v for k, v in KEYWORD_TO_RIGHTS.items()
        if k not in {
            "employee", "staff", "workplace", "working conditions",
            "protest", "assembly", "union", "organizing", "organisation",
            "association", "collective",
        }
    }
    text = proposal.lower()
    rights = set(_OLD_ALWAYS)
    for term, arts in old_keys.items():
        if term in text:
            rights.update(arts)
    return sorted(rights)


def norm_art(s: str) -> str | None:
    m = re.search(r"Art(?:icle)?\s*(\d+)", str(s))
    return f"Art{m.group(1)}" if m else None


def load_assessment(pid: str) -> dict | None:
    candidates = [
        ROOT / "evaluation" / "results" / "llama-3.3-70b" / f"{pid}_full.json",
        ROOT / "rag-pipeline" / "outputs" / f"{pid}_full.json",
        ROOT.parent / "ethics-rag" / "outputs" / f"{pid}_full.json",
    ]
    for p in candidates:
        if p.exists():
            return json.load(open(p))
    return None


def main():
    set_retrieval_backend("local")
    by_id = {p["id"]: p for p in PROPOSALS}
    rows = []

    print("=" * 88)
    print("AIEF Phase 6 — Before/After Case Study (retrieval layer)")
    print("=" * 88)
    print(f"{'PID':4}  {'Signal':28}  {'BEFORE':40}  {'AFTER'}")
    print("-" * 88)

    for pid in CASE_IDS:
        p = by_id[pid]
        text = p["proposal_text"]
        old_rights = old_matched_rights(text)
        new_rights = get_matched_rights(extract_keywords(text), proposal=text)
        path = get_matched_rights.last_disambiguation

        reqs, incs, rights, kws, risk_cats = retrieve_all_for_proposal(text)
        risk_ids = [c["id"] for c in risk_cats]
        sections = sorted({
            r.get("section_reference") for r in reqs
            if r.get("section_reference") and any(
                x in (r.get("section_reference") or "")
                for x in ("Transparency", "Well-being")
            )
        })

        exp_rights = p.get("expected_rights", [])
        exp_risks = p.get("expected_risk_categories") or p.get("expected_risks") or []

        # Key signals per proposal (expert-reviewer concerns)
        signals = {
            "P01": ("Art21 present / Art31", "Art21"),
            "P03": ("Surveillance / Art21", "Surveillance"),
            "P06": ("Art24 + ChildrenRights", "ChildrenRights"),
            "P08": ("Art35 health path", "Art35"),
            "P13": ("Art21 removed (bibliometric)", "Art21"),
        }
        label, _ = signals[pid]

        before_art21 = "Art21_NonDiscrimination" in old_rights
        after_art21 = "Art21_NonDiscrimination" in new_rights
        before_art24 = "Art24_RightsOfChild" in old_rights
        after_art24 = "Art24_RightsOfChild" in new_rights
        before_art31 = "Art31_FairWorkingConditions" in old_rights
        after_art31 = "Art31_FairWorkingConditions" in new_rights

        before_summary = (
            f"Art21={before_art21} Art24={before_art24} Art31={before_art31} "
            f"rights={len(old_rights)} risks=∅"
        )
        after_summary = (
            f"Art21={after_art21} Art24={after_art24} Art31={after_art31} "
            f"rights={len(new_rights)} risks={len(risk_ids)} path={path}"
        )
        print(f"{pid:4}  {label:28}  {before_summary}")
        print(f"{'':4}  {'':28}  → {after_summary}")
        if sections:
            print(f"{'':4}  transparency/well-being sections retrieved: {sections}")
        if exp_risks:
            hit = [c for c in exp_risks if c in risk_ids]
            miss = [c for c in exp_risks if c not in risk_ids]
            print(f"{'':4}  expected risk cats hit={hit} miss={miss}")

        # Score existing LLM output if available
        assessment_doc = load_assessment(pid)
        llm_cats = []
        llm_arts = []
        if assessment_doc:
            a = assessment_doc.get("assessment", {})
            for r in a.get("identified_risks", []) or []:
                if r.get("risk_category"):
                    llm_cats.append(r["risk_category"])
            for r in a.get("charter_rights_at_risk", []) or []:
                n = norm_art(r.get("article", ""))
                if n:
                    llm_arts.append(n)

        row = {
            "proposal_id": pid,
            "title": p["title"],
            "expert_signal": label,
            "before": {
                "matched_rights": old_rights,
                "art21": before_art21,
                "art24": before_art24,
                "art31": before_art31,
                "risk_categories_retrieved": [],
            },
            "after": {
                "matched_rights": new_rights,
                "art21": after_art21,
                "art24": after_art24,
                "art31": after_art31,
                "disambiguation_path": path,
                "risk_categories_retrieved": risk_ids,
                "transparency_wellbeing_sections": sections,
                "requirements_retrieved": len(reqs),
            },
            "expected_rights": exp_rights,
            "expected_risk_categories": exp_risks,
            "existing_llm_output": {
                "risk_categories": llm_cats,
                "charter_articles": llm_arts,
                "note": (
                    "Pre-rerun outputs lack risk_category fields; "
                    "re-run ethics_rag after GraphDB reload to populate."
                    if not llm_cats else "risk_category fields present"
                ),
            },
            "fix_highlights": _highlights(pid, before_art21, after_art21, after_art24, risk_ids, path),
        }
        rows.append(row)
        print()

    # Extra acceptance rows
    print("-" * 88)
    protest = "Campus CCTV monitoring of student protest assembly and union organizing."
    pr = get_matched_rights(extract_keywords(protest), proposal=protest)
    print(f"SYNTHETIC protest → Art12 present: {'Art12_FreedomOfAssembly' in pr}")
    p20 = by_id["P20"]
    r20 = get_matched_rights(extract_keywords(p20["proposal_text"]), proposal=p20["proposal_text"])
    print(f"P20 workplace   → Art31 present: {'Art31_FairWorkingConditions' in r20}")
    print("-" * 88)

    # Markdown table for dissertation
    md_lines = [
        "# AIEF Phase 6 — Before/After Case Study",
        "",
        "Expert-reviewer concerns mapped to retrieval-layer fixes (Phases 0–3).",
        "Old = pre-fix keyword map (always Art8+Art41, no bias disambiguation, no risk categories).",
        "New = Phase 1–3 retrieval (scoped risk categories, Art12/Art31 triggers, SHACL-style bias disambiguation).",
        "",
        "| Proposal | Expert signal | Before | After |",
        "|---|---|---|---|",
    ]
    for row in rows:
        b = row["before"]
        a = row["after"]
        before_cell = (
            f"Art21={b['art21']}; Art24={b['art24']}; "
            f"{len(b['matched_rights'])} rights; no risk taxonomy"
        )
        after_cell = (
            f"Art21={a['art21']}; Art24={a['art24']}; "
            f"{len(a['matched_rights'])} rights; "
            f"{len(a['risk_categories_retrieved'])} risk cats; "
            f"path={a['disambiguation_path']}"
        )
        md_lines.append(
            f"| {row['proposal_id']} ({row['title'][:40]}) | {row['expert_signal']} | {before_cell} | {after_cell} |"
        )

    md_lines += [
        "",
        "## Quantified fixes (retrieval)",
        "",
        f"- **P13 Art21 removed:** "
        f"{rows[4]['before']['art21']} → {rows[4]['after']['art21']} "
        f"(path={rows[4]['after']['disambiguation_path']})",
        f"- **P06 Art24 retained + ChildrenRights in scope:** "
        f"Art24 {rows[2]['before']['art24']}→{rows[2]['after']['art24']}; "
        f"ChildrenRights={'ChildrenRights' in rows[2]['after']['risk_categories_retrieved']}",
        f"- **P20 Art31 (workplace):** {'Art31_FairWorkingConditions' in r20}",
        f"- **Synthetic protest Art12:** {'Art12_FreedomOfAssembly' in pr}",
        "",
        "## Note on LLM re-score",
        "",
        "Existing `*_full.json` assessment outputs pre-date the `risk_category` schema.",
        "Re-run `ethics_rag.py` / `run_evaluation.py` after reloading the Phase-0 ontology",
        "into GraphDB to populate E8 scores and regenerate FRIA docs with category breakdowns.",
        "",
    ]

    json_path = OUT_DIR / "phase6_before_after.json"
    md_path = OUT_DIR / "phase6_before_after.md"
    json.dump(
        {
            "cases": rows,
            "acceptance": {
                "P13_art21_removed": (rows[4]["before"]["art21"] is True and rows[4]["after"]["art21"] is False),
                "P06_children_rights_in_scope": "ChildrenRights" in rows[2]["after"]["risk_categories_retrieved"],
                "P06_art24": rows[2]["after"]["art24"],
                "P20_art31": "Art31_FairWorkingConditions" in r20,
                "synthetic_protest_art12": "Art12_FreedomOfAssembly" in pr,
            },
        },
        open(json_path, "w"),
        indent=2,
    )
    md_path.write_text("\n".join(md_lines) + "\n")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


def _highlights(pid, before_art21, after_art21, after_art24, risk_ids, path):
    notes = []
    if pid == "P13":
        notes.append(f"Art21 {before_art21}→{after_art21} via {path}")
    if pid == "P06":
        notes.append(f"Art24={after_art24}; ChildrenRights={'ChildrenRights' in risk_ids}")
    if "Surveillance" in risk_ids:
        notes.append("Surveillance category retrieved")
    if "Transparency" in str(risk_ids):
        pass
    return notes


if __name__ == "__main__":
    main()
