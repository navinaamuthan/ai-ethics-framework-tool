# Next instructions for Cursor — Steps 4, 5, 6 + one consistency fix

Steps 1–3 are done and verified. `reliability_report.json` is final. Do not
re-touch corpus_expansion.py, frame_annotation.py, or reliability_analysis.py
except for the one item below.

## 0. Fix the P21–P40 prompt inconsistency first

LLM-70B's outputs for P01–P20 were generated with the full RAG pipeline
(retrieval + prompt_builder), but P21–P40 used a compact risk+rights-only
prompt as a workaround for the Groq TPD limit. This is a confound: any
difference in LLM-70B's behaviour on the new 20 proposals could be the
prompt format, not the proposal content.

**Action:** re-run P21–P40 for LLM-70B through the full RAG pipeline
(`ethics_rag.py`, same code path as P01–P20), now that a working key/quota
is available. Overwrite the compact-prompt outputs in
`evaluation/results/llama-3.3-70b/`.

**If quota blocks this again:** do not silently keep the compact-prompt
numbers as if they were equivalent. Instead:
- Keep the compact-prompt results but add a boolean field
  `"compact_prompt": true` to each of those 20 output JSONs.
- In `reliability_analysis.py`'s report, add a sensitivity check: recompute
  LLM-70B's `risk_kappa`/`rights_kappa` restricted to P01–P20 only (the
  full-RAG subset), and report that alongside the all-40 number. If the
  two numbers are close, the compact-prompt confound is probably minor and
  say so explicitly in the methods text. If they diverge notably, flag it
  as a limitation and do not use the all-40 LLM-70B number as a headline
  figure — use the P01–P20-only number instead and note n=20 for that row.

Either way, add one sentence to the Chapter 4 methods draft (Step 7 below)
documenting which path was taken and why.

## 1. Step 4 — `perturbation_generator.py`

Exactly as specified in `CURSOR_EXECUTION_PLAN.md` Step 4: 15 proposals
(spread across risk levels, drawn from the 40) × 3 perturbation classes
(positive / negative / neutral) = 45 variants. Blind persona pre-labelling
of expected direction using the same 4 persona prompts from
`frame_annotation.py` (reuse, don't rewrite), 1 run each this time.

Run all 45 variants through all 4 assessors (SHACL, LLM-8B, LLM-70B via
full RAG — same fix as above applies, don't introduce a new compact-prompt
path here, use full RAG from the start), score sensitivity rate per
assessor per perturbation class.

Output: `diagnostic/perturbation_variants.json`,
`diagnostic/results/perturbation_report.json`.

Frame in the stored report's own text field: this is a unit test for
known-direction sensitivity, not a deployment-prediction claim — bake that
caveat into the JSON's `"scope_note"` field so it can't be dropped when the
tables are generated.

## 2. Step 5 — `property_evaluator.py`

Exactly as specified in `CURSOR_EXECUTION_PLAN.md` Step 5, on all 40
proposals, all 4 assessors:
- **Stability**: 5 runs each for LLM-8B/LLM-70B (full RAG), flip rate.
  SHACL/keyword deterministic, verify = 1.0 once.
- **Traceability**: coverage % per assessor as specified.
- **Amendability**: pick 5 currently-wrong proposals per assessor (use
  `assessor_vs_gt` mismatches from `reliability_report.json` to select
  them — don't re-derive from scratch), measure edit size + collateral
  flips across all 40.
- **Comprehensibility**: LLM-as-judge, 1–5 scale, averaged over 40 per
  assessor.

Explicitly check and report the degenerate-baseline pattern: does the
keyword baseline score near-ceiling on stability/traceability but poorly
on amendability/comprehensibility? Report the actual numbers regardless of
which way they come out — if keyword-baseline does NOT show that pattern,
say so plainly, don't smooth it over.

Output: `diagnostic/property_scores.json`,
`diagnostic/results/property_report.json`.

## 3. Step 6 — `generate_tables.py`

Read `reliability_report.json`, `perturbation_report.json`,
`property_report.json`. Emit one `.tex` table file per result into
`diagnostic/results/tables/`, named clearly (e.g.
`tab_reliability_headline.tex`, `tab_decision_rule.tex`,
`tab_perturbation_sensitivity.tex`, `tab_property_scores.tex`). No number
should exist only in a script's stdout — every headline figure needs a
`.tex` table it's sourced from.

## 4. Report back before writing

Once Steps 4–6 finish, report back here with:
- perturbation sensitivity rates per assessor/class
- property scores per assessor (stability, traceability, amendability
  edit+collateral, comprehensibility)
- confirmation of which path was taken for the P21–P40 fix (full re-run,
  or compact-prompt-with-sensitivity-check)

Do not start drafting dissertation chapter text yet — that happens after
this data is reviewed, per the original execution plan's Step 7 gate.
