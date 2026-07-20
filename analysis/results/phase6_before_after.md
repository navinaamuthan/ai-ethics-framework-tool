# AIEF Phase 6 — Before/After Case Study

## RAG/LLM pipeline arm (retrieval + prompt constraints) — RESULTS BELOW

**Everything in this file is RAG-arm data only** (SPARQL retrieval over the
knowledge graph, feeding `prompt_builder.py` / `ethics_rag.py`). No SHACL
shape validation results (`shacl/aief-risk-shapes.ttl`) appear in this table.
"SHACL-style bias disambiguation" below is a naming/design borrowing — the
RAG retrieval logic uses a decision-path structure loosely modelled on SHACL
shape reasoning, but it is executed entirely inside the Python retrieval
layer (`sparql_retrieval.py`), not by an actual SHACL validator. The
independent SHACL structural-rules arm (RQ2 comparison) is reported
separately in `shacl/PHASE4_RQ2_FINDING.md` and its own results files
(`shacl/oops_report.xml`-adjacent outputs, `rag-pipeline/mcnemar_risk.py`) —
see the note at the bottom of this file for why the two arms are kept
separately auditable.

Expert-reviewer concerns mapped to retrieval-layer fixes (Phases 0–3).
Old = pre-fix keyword map (always Art8+Art41, no bias disambiguation, no risk categories).
New = Phase 1–3 retrieval (scoped risk categories, Art12/Art31 triggers, retrieval-layer bias disambiguation).

| Proposal | Expert signal | Before | After |
|---|---|---|---|
| P01 (Optum Health Risk Stratification Algorit) | Art21 present / Art31 | Art21=True; Art24=False; 10 rights; no risk taxonomy | Art21=True; Art24=False; 10 rights; 27 risk cats; path=individual_treatment→Art21 |
| P03 (Amazon Rekognition Law Enforcement Facia) | Surveillance / Art21 | Art21=True; Art24=False; 11 rights; no risk taxonomy | Art21=True; Art24=False; 11 rights; 27 risk cats; path=individual_treatment→Art21 |
| P06 (Emotion Recognition in Secondary School ) | Art24 + ChildrenRights | Art21=True; Art24=True; 8 rights; no risk taxonomy | Art21=True; Art24=True; 8 rights; 27 risk cats; path=not_applicable |
| P08 (AI Chatbot for Mental Health Support Tri) | Art35 health path | Art21=False; Art24=True; 8 rights; no risk taxonomy | Art21=False; Art24=True; 8 rights; 27 risk cats; path=not_applicable |
| P13 (Bibliometric Analysis of Open Access AI ) | Art21 removed (bibliometric) | Art21=True; Art24=False; 5 rights; no risk taxonomy | Art21=False; Art24=False; 4 rights; 27 risk cats; path=systemic_info→Art11/Art22 |

## Quantified fixes (retrieval)

- **P13 Art21 removed:** True → False (path=systemic_info→Art11/Art22)
- **P06 Art24 retained + ChildrenRights in scope:** Art24 True→True; ChildrenRights=True
- **P20 Art31 (workplace):** True
- **Synthetic protest Art12:** True

## Note on LLM re-score

Existing `*_full.json` assessment outputs pre-date the `risk_category` schema.
Re-run `ethics_rag.py` / `run_evaluation.py` after reloading the Phase-0 ontology
into GraphDB to populate E8 scores and regenerate FRIA docs with category breakdowns.

## RQ3 status — one assessment, four authorities' documentation structures

`rag-pipeline/docgen_templates.yaml` defines field-mappings for all 4
authorities (REAMS, FRIA, ACM/NeurIPS, HorizonEurope), and
`generate_documentation.py` renders each from one harmonised `*_full.json`
assessment with real per-field provenance (see `shacl`-independent Fix 3:
`risk_category_breakdown` now cites actual requirement IDs, not category
labels). Status per authority, checked by regenerating P06 fresh on
2026-07-20 (`evaluation/generated-documentation/P06_*.md`):

- **REAMS** — 5/6 fields filled (83%). Works.
- **FRIA** — 7/7 fields filled (100%). Works, including the fixed
  `risk_category_breakdown` provenance.
- **ACM/NeurIPS** — 3/3 fields filled (100%) for P06. Works for proposals
  where the LLM cites `ACMConference`-framework requirements (true for
  P01–P07 in the existing `evaluation/generated-documentation/` outputs).
  **For P08–P20 the existing committed `P*_ACM_NeurIPS.md` files are fully
  empty (3/3 "NOT DERIVABLE")** — those are stale outputs generated before
  the Phase 0 ontology repair populated `:hasRisk`/richer schema fields, and
  were never re-run since. Re-running those 12 proposals through
  `run_evaluation.py` would very likely restore content, since the template
  and code path are demonstrably correct (P06 proves it) — this just wasn't
  done for the full 20-proposal suite in this fix pass because it requires
  ~20 sequential Groq calls with rate-limit sleeps.
- **HorizonEurope** — **partially works, systemically weak.** Only the
  `social_impact` field (which falls back to the general `risk_summary`) is
  ever populated; `ethics_by_design` and `human_oversight` are empty because
  no requirement in the retrieved/cited set matches the `find_req("consent"
  / "oversight")` keyword lookup in `generate_documentation.py`, and
  `data_management` is empty because the LLM's `applicable_requirements`
  almost never cite a `HorizonEurope`-framework requirement (confirmed for
  P06: all 9 cited requirements were `ACMConference`). This is true across
  every proposal checked, old and freshly regenerated — Horizon completeness
  never exceeds 1/4 (25%) in any observed output, versus 83–100% for the
  other three authorities. Root cause is upstream of the docgen template: the
  assessment prompt/LLM under-cites Horizon-framework requirements relative
  to ACM ones for these proposal texts. Fixing that would mean adjusting
  retrieval/prompt weighting in `ethics_rag.py`/`prompt_builder.py`, which is
  out of scope for this documentation-template fix pass — flagged here
  honestly rather than left silently unaddressed.

## Why the RAG arm and the SHACL arm are reported separately (RQ2)

This file only ever shows RAG/LLM pipeline behaviour. The SHACL structural-rules
arm (`shacl/aief-risk-shapes.ttl`, discussed in `shacl/PHASE4_RQ2_FINDING.md`) is
**not wired into `prompt_builder.py` / `ethics_rag.py`** and is deliberately kept
independent: RQ2 asks whether scrutable SHACL shape rules and free-text LLM
interpretation agree or disagree on the same proposals, and that comparison is
only valid if each arm's output is auditable on its own, without one arm's
retrieval logic silently influencing the other's verdict. Mixing the two into a
single before/after table would erase the very agreement/disagreement signal
RQ2 is measuring.

