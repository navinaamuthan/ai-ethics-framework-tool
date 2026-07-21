# Execution plan — diagnostic methodology chapter (4-day sprint)

Read this whole file before touching code. It supersedes any earlier plan that
mentions "CLEAR" as a name. **Do not introduce an acronym or brand name
anywhere in code, filenames, comments, or dissertation text.** Use the phrase
"the diagnostic methodology" or "the diagnostic" on first reference per
section, "the diagnostic" thereafter. This is a hard style rule — grep for
"CLEAR" before you finish and delete/rename any hit that is being used as a
proper noun.

## Dissertation title

Update the title page in all three dissertation-latex copies
(`dissertation-latex/`, `ai-ethics-framework-tool/dissertation-latex/`,
`AIEF_Review_Package_2026-07-13/dissertation/`) to:

> **Diagnosing the Validity of Reference-Label-Based Evaluation for
> Automated AI Ethics Assessors**

Do this as part of Step 7 (dissertation writing), not before — but note it
now so no placeholder title ships in the final PDF.

## The one-sentence thesis (keep this pinned above every file you write)

> An evaluation protocol that scores an automated assessor against reference
> labels is itself a measurement instrument, and its validity depends on
> conditions — chiefly, the reliability of those reference labels — that are
> not currently checked before such protocols are used.

The diagnostic methodology is the artifact that checks that condition. It has
exactly one job: given an assessor and a labelled corpus, determine whether
agreement-with-reference-labels is a valid basis for evaluating that
assessor on that corpus. It does **not** prescribe what to do instead — that
is a separately labelled "illustrative application," not part of the
diagnostic.

---

## Repo orientation (already exists, do not restructure)

- `rag-pipeline/synthetic_proposals.py` — `PROPOSALS: list[dict]`, 20 entries,
  each with keys: `id, title, risk_level, source, proposal_text,
  expected_requirements, expected_rights, expected_charter_articles,
  expected_risks, expected_risk_categories`.
- `rag-pipeline/ethics_rag.py` — pipeline orchestrator, runs an assessor
  (SHACL or LLM) over a proposal and writes JSON output.
- `shacl/aief-risk-shapes.ttl` — the symbolic/SHACL assessor.
- `rag-pipeline/annotator_agreement.py` — existing kappa-computation code
  (two human annotators vs ground truth). Reuse the `kappa()` and `to_art()`
  functions; do not duplicate them.
- `evaluation/results/` — where assessor outputs already live.
- `dissertation-latex/`, `ai-ethics-framework-tool/dissertation-latex/`,
  `AIEF_Review_Package_2026-07-13/dissertation/` — three copies that must be
  kept in sync. Edit all three whenever you touch dissertation text, or
  script the sync at the end (`diff` them and propagate).

Create a new top-level folder `diagnostic/` for everything below. Do not put
new scripts in `rag-pipeline/` — keep the diagnostic study cleanly separated
from the production pipeline it studies.

```
diagnostic/
  corpus_expansion.py
  synthetic_proposals_extended.py   # 40 proposals: original 20 + 20 new
  frame_annotation.py
  frame_annotations.json            # output of frame_annotation.py
  reliability_analysis.py
  perturbation_generator.py
  perturbation_variants.json
  property_evaluator.py
  property_scores.json
  generate_tables.py
  results/                          # all output tables/figures land here
```

---

## Step 1 — `corpus_expansion.py`

**Goal:** grow the corpus from 20 to 40 proposals, targeting gaps in the
existing set so the new proposals add information, not filler.

Gaps to target (check `synthetic_proposals_extended` risk_level distribution
as you go — the original 20 skew High-risk):
- More `Medium` risk proposals (currently under-represented)
- `Low`-risk proposals with a subtle, easy-to-miss issue (tests whether
  assessors over- or under-flag)
- Proposals whose correct Charter articles are contested even among
  reasonable experts (deliberately ambiguous — these matter for Step 3)
- Non-Western / non-US deployment contexts (the existing set is US/UK-heavy)
- Proposals that plausibly touch two frameworks in tension (e.g. an
  Art.27 FRIA concern vs a Horizon Europe requirement) — these are exactly
  the disagreement-generating cases the diagnostic needs

**Method:** use an LLM (Ollama local 8B or Groq 70B, whichever is under
quota) to draft each proposal in the same prose style as the existing 20
(one paragraph, ~150–220 words, grounded in a real or realistic
case — cite a real source where possible, following the `source` field
convention already used). For each, YOU (Cursor, or the calling script)
must also produce ground truth:
- `risk_level`: High/Medium/Low
- `expected_charter_articles`: list, using the exact article-name strings
  already used in `synthetic_proposals.py` (e.g. `'Art21_NonDiscrimination'`)
  — grep the existing file for the full vocabulary before inventing new
  labels
- `expected_risk_categories`: same constraint, grep
  `ontology/risk_category_doc_frequency.json` for the valid category names
- **New field**: `"info_sufficiency_expected": <1-5>` — your best-faith
  estimate of how much information the proposal text gives an annotator to
  make a confident judgement (5 = fully sufficient, 1 = genuinely
  under-specified). Low scores are fine and expected for a few proposals —
  those are the ones testing the ambiguity-vs-contestedness distinction.
- `"rationale"`: 1–2 sentences justifying the ground truth, for your own
  audit trail, not shown to annotators.

Write `synthetic_proposals_extended.py` exporting `PROPOSALS` (all 40,
original 20 preserved verbatim + 20 new) in the exact same schema plus the
two new fields above (backfill `info_sufficiency_expected` and `rationale`
for the original 20 too — quick pass, doesn't need to be elaborate).

**Acceptance check (script must assert, not just print):**
- `len(PROPOSALS) == 40`
- every entry has all 8 original keys + 2 new keys, no `None`/empty
  `expected_charter_articles`
- risk_level distribution is not more than 70% High (i.e., you actually
  added Medium/Low cases)
- every `expected_charter_articles` and `expected_risk_categories` value
  is drawn from the vocabulary already present in the original 20 proposals
  (no invented label strings) — assert this by set-membership check
- fail loudly (raise, don't silently continue) if any check fails

---

## Step 2 — `frame_annotation.py`

**Goal:** simulate four annotator perspectives on all 40 proposals, 3
independent runs each, to get within-perspective and cross-perspective
disagreement data.

**The four persona system prompts** (use verbatim, do not paraphrase —
consistency across runs matters more than prose quality):

1. `technical`: *"You are a senior machine learning engineer reviewing this
   research proposal for an internal risk assessment. Focus on what is
   technically verifiable: data provenance, model validation, measurable
   failure modes. You are skeptical of claims that cannot be checked against
   the described methodology."*
2. `legal`: *"You are an EU data protection and fundamental rights lawyer
   reviewing this proposal against the EU Charter of Fundamental Rights and
   GDPR. Identify which Charter articles are engaged and how severely,
   based on established case law and regulatory guidance where relevant."*
3. `ethics`: *"You are a member of a university research ethics committee
   reviewing this proposal. Focus on consent, power imbalances, vulnerable
   populations, and whether affected people have any way to contest or
   opt out of the described system."*
4. `lay`: *"You are a person with no technical or legal training who would
   be directly affected by the system described in this proposal (e.g. a
   patient, defendant, student, or employee, whichever applies). Judge the
   proposal based on how it would feel to be subject to this system,
   without using technical or legal jargon."*

**Task given to each persona, each run:** for each of the 40 proposals,
output: `risk_level` (High/Medium/Low), `charter_articles` (list, must use
the same vocabulary as Step 1 — give the model the vocabulary list in the
prompt so it doesn't invent variants), and `info_sufficiency` (1-5, "how
much information did you need vs how much were you given").

Run each persona **3 times independently** (temperature > 0, e.g. 0.7, no
shared context between runs — fresh call each time) → 4 personas × 3 runs ×
40 proposals = 480 records.

Use structured output (JSON mode / function-calling schema if the backend
supports it) to avoid parse failures. Retry once on parse failure, then
skip-and-log (do not crash the whole run over one bad record).

**Output** `frame_annotations.json`:
```json
[
  {"proposal_id": "P01", "perspective": "technical", "run": 1,
   "risk_level": "High", "charter_articles": ["Art8_DataProtection", ...],
   "info_sufficiency": 4},
  ...
]
```

**Acceptance check:** 480 records minus logged skips; print skip count;
assert skip count < 24 (i.e. < 5% failure rate) or halt and report which
persona/run is failing systematically (usually a prompt or parsing bug, fix
before continuing — don't paper over it).

---

## Step 3 — `reliability_analysis.py`

**Goal:** the actual empirical core of the dissertation. Reuse `kappa()` and
`to_art()` from `rag-pipeline/annotator_agreement.py` (import, don't
re-implement).

1. **Within-stratum reliability**: for each of the 4 personas, compute
   pairwise κ across its 3 runs (3 pairs per persona × 4 personas = 12 κ
   values) for both `risk_level` and binary per-article agreement (same
   binary-decision expansion method as `rights_kappa` in the existing file).
   Average within a persona to get one within-stratum κ per persona (4
   values), report the 12 raw pairs too.

2. **Cross-stratum reliability**: pick one representative run per persona
   (run 1, to avoid combinatorial explosion — note this choice explicitly
   in the output), compute κ between every pair of personas (6 pairs) for
   risk_level and rights.

3. **The headline test**: is mean(within-stratum κ) > mean(cross-stratum
   κ)? Report both means with bootstrap 95% CIs (resample proposals with
   replacement, 10,000 iterations, recompute κ each time — write a small
   reusable `bootstrap_ci(pairs_list, kappa_fn, n=10000)` helper).
   - If within > across and CIs don't overlap: frame-hypothesis supported,
     write this up as the finding.
   - If not: **do not force a positive result.** Write up honestly per the
     pre-registered kill condition (see below) — report that disagreement
     is not structured by perspective in this corpus, and say what that
     implies (the diagnostic's reliability-ceiling computation still holds
     regardless; only the *explanation* for low reliability changes).

4. **Information-sufficiency filter**: split proposals into
   `info_sufficiency >= 3` (mean across all 480 records for that proposal)
   vs `< 3`. Recompute the headline reliability numbers (both within- and
   cross-stratum κ) on each subset separately. Report both. This is the
   test for Criticism 5 (ambiguity vs contestedness) — low-sufficiency
   proposals with low agreement = ambiguous; high-sufficiency proposals
   with low agreement = genuinely contested. State which proposals fall in
   which quadrant.

5. **The reliability ceiling and decision rule**: 
   - `ceiling = max(within-stratum κ across all 4 personas)` — the best
     agreement achievable by any single consistent perspective, i.e. the
     empirical upper bound on how reliable these reference labels can be
     shown to be.
   - For each assessor (SHACL, LLM-8B, LLM-70B, keyword-baseline — outputs
     should already exist in `evaluation/results/`, or generate them by
     running `ethics_rag.py` over all 40 proposals if missing), compute
     assessor-vs-ground-truth κ.
   - Compute the **accuracy gap** between every pair of assessors (|κ_a −
     κ_b|).
   - **Decision rule**: if the accuracy gap between two assessors is
     smaller than (1 − ceiling) — i.e. within the noise band implied by
     imperfect reference reliability — accuracy cannot be trusted to rank
     those two assessors. Report this as a table: every assessor pair, gap,
     ceiling-implied noise band, verdict (discriminable / not
     discriminable).

6. **LOO + D-study**: leave-one-proposal-out recomputation of every
   headline number above (40 reruns, report min/max range). D-study:
   using the observed within-stratum variance, project what reliability
   would be at n=60 and n=100 proposals (standard Spearman-Brown
   prophecy formula is fine here — cite it as a formula, not as the
   dissertation's theoretical foundation).

**Output:** `reliability_analysis.py` prints a full report to stdout AND
writes `results/reliability_report.json` with every number above, structured
for `generate_tables.py` to consume.

**Pre-registered kill conditions — write these into a `KILL_CONDITIONS`
docstring at the top of the file, commit before running, do not edit after
seeing results:**
1. If within-stratum κ ≤ cross-stratum κ: the perspective-based explanation
   for disagreement fails; report honestly (see step 3 above).
2. If ceiling > every observed accuracy gap: reference-based evaluation IS
   valid for this corpus; the diagnostic correctly says "use accuracy,"
   and the illustrative property-based application becomes unnecessary here
   — still report it as a validation of the diagnostic, not a failure of
   the dissertation.
3. If all four assessors are statistically indistinguishable on every
   property in Step 5 (below): report that the property suite is
   uninformative for this assessor set — this is an honest limitation, not
   something to hide.

---

## Step 4 — `perturbation_generator.py`

Select 15 proposals (spread across risk levels) from the 40. For each,
generate 3 variants using an LLM:
- **positive**: remove or fix exactly one described issue (e.g. add a
  bias audit, add an appeal mechanism) → expected risk level moves down
  or stays same, never up
- **negative**: add exactly one new violation → expected risk level moves
  up or stays same, never down
- **neutral**: paraphrase only, no substantive change → expected risk level
  and Charter articles unchanged

45 variants total. For each, have the 4 personas (reuse Step 2's prompts,
1 run each this time, not 3 — budget) label their *expected* direction
**before** any assessor sees the variant — this is the blind pre-labelling
that avoids circularity (Criticism 6 in the design doc). Store persona
predictions separately from the actual perturbation-author's intended
direction; report inter-persona agreement on predicted direction too.

Then run all 45 variants through all 4 assessors. Score: fraction of
variants where the assessor's output moved in the expected direction
("sensitivity rate"), separately per assessor per perturbation class.

Frame this explicitly in the write-up as **"a unit test for assessor
behaviour under known-direction change, not a claim about real-world
deployment prediction."** State that limitation in the same paragraph the
result appears in, not just in a limitations chapter — do not let the
number stand without its scope caveat next to it.

**Output:** `perturbation_variants.json`, `results/perturbation_report.json`.

---

## Step 5 — `property_evaluator.py`

For all 40 proposals, all 4 assessors:

- **Stability**: run each non-deterministic assessor (both LLMs) 5× per
  proposal; SHACL and keyword-baseline are deterministic, stability = 1.0
  by construction, verify once. Report flip rate = fraction of the 5 runs
  disagreeing with the modal output.
- **Traceability**: SHACL → fraction of output claims backed by a firing
  rule (should be ~100% by construction, verify). LLM → fraction of
  `identified_risks` entries whose `risk_category` cites a real requirement
  ID that is retrievable in the ontology (reuse
  `requirement_ids_for_risk_category()` from `generate_documentation.py`).
  Keyword baseline → fraction of flagged terms traceable to the literal
  keyword list (should be 100%, verify).
- **Amendability**: for each assessor, pick 5 proposals where the assessor
  is currently *wrong* (vs ground truth) and estimate the minimal edit to
  fix that one case: SHACL → count TTL lines changed; LLM → count prompt
  words/lines changed in `prompt_builder.py`'s scope-construction logic;
  keyword baseline → count keywords added/removed. For each edit, also
  measure **collateral**: rerun the edited assessor on all 40 proposals,
  count how many *other* previously-correct outputs flipped. Report
  `(edit_size, collateral_count)` triples per assessor, averaged over the
  5 cases.
- **Comprehensibility**: LLM-as-judge — feed the assessor's raw output for
  a proposal to a separate LLM call with the prompt: *"You are a person
  affected by the system described, with no technical background. Based on
  this assessment output, could you identify what you would dispute and
  why? Answer 1 (completely unclear) to 5 (completely clear what to
  dispute)."* Run over all 40 proposals per assessor, average score.

**Explicitly verify and report the degenerate-baseline check**: the
keyword baseline should score ~1.0 on stability and traceability but
noticeably worse on amendability (large collateral for any fix, since it
has no structure) and comprehensibility (flags terms without explaining
relevance). If it does NOT show this pattern, say so plainly — that would
itself be a finding (the property suite isn't discriminating), consistent
with kill condition 3.

**Output:** `property_scores.json`, `results/property_report.json`.

---

## Step 6 — `generate_tables.py`

Read every `results/*.json` file, emit LaTeX tables (one `.tex` file per
table, named to match where they're `\input{}`'d in the dissertation
chapters) into `diagnostic/results/tables/`. No hand-typed numbers in the
dissertation text anywhere — every number in prose must be
`\input`-sourced or manually copy-pasted *from this script's stdout*, and
regenerable by rerunning this one script. Add a `make all` target (a
`Makefile` or a `run_all.sh`) that runs Steps 1–6 in order.

---

## Dissertation writing — structure and terminology rules

**Global find-and-replace rule before submission:** grep the whole
`dissertation-latex/` tree (all three copies) for `CLEAR`. If found as a
proper noun/acronym, replace with "the diagnostic" or "the diagnostic
methodology" per the style below. It is fine for the string "clear" to
appear as an ordinary English word.

**Chapter 1 — Introduction**
Open with the one-sentence thesis (top of this file). Immediately follow
with the definition of evaluation (two objectives: epistemic fitness —
is it accurate — and procedural fitness — is it contestable/legitimate).
State plainly: *"This dissertation does not name its diagnostic methodology
with an acronym. It is referred to throughout simply as 'the diagnostic' or
'the diagnostic methodology.'"* One sentence, kills the branding question
before an examiner can raise it.

**Chapter 2 — Background**
Three literature streams, each closing on the specific gap the diagnostic
fills. No new streams beyond what's already drafted in earlier planning —
do not add G-theory or Spearman literature reviews; they are demoted to
brief method citations in Chapter 4, not literature chapters of their own.

**Chapter 3 — The argument**
Two paragraphs, explicitly split and labelled "Argument A (empirical)" and
"Argument B (normative)", then one paragraph titled "Conjunction" explaining
that the diagnostic operationalises Argument A, and the illustrative
property-based application (Chapter 5) is one way of acting on Argument B
once Argument A says accuracy is untrustworthy.

**Chapter 4 — Methodology**
Describe the diagnostic in this order: (1) definition — one sentence, the
one from the top of Step 3; (2) the reliability-ceiling and decision-rule
procedure; (3) the alternative-explanations table (info-sufficiency filter,
within/cross-stratum split — this is how annotation-quality,
ambiguity, and frame are disentangled); (4) the pre-registered kill
conditions, verbatim from the code docstring; (5) a short "when to use
this" economics paragraph (diagnostic is a one-time per-corpus check, not
a per-evaluation cost). Explicitly state: *"The diagnostic deliberately
does not prescribe a unique replacement evaluation methodology. Its purpose
is diagnostic: to determine whether reference-label-based evaluation is
justified for a given assessor-corpus pair. What to do once it is not is a
separate, domain-specific question, illustrated but not resolved by this
dissertation."*

**Chapter 5 — Illustrative application** (explicitly subordinate, titled
as such, not "Results Part 2")
Present the property suite (stability, traceability, amendability,
comprehensibility) as *one example* of what becomes possible once the
diagnostic has ruled out accuracy. Include the degenerate-baseline finding
here as the chapter's main argument for why the four properties, taken
together, are non-trivial.

**Chapter 6 — Discussion**
Frequency-ranking bug (Transparency 0/20, from earlier work) as the closing
vignette. Limitations listed per-experiment, not lumped. One paragraph
generalising the diagnostic beyond AI ethics assessment (content
moderation, medical triage, legal prediction — anywhere reference labels
may be unreliable) — scoped as "the diagnostic's logic transfers in
principle; only this domain was tested."

**Chapter 7 — Conclusion**
Restate the one sentence. Nothing new introduced here.

---

## Execution order (do not parallelize steps 1→3; 4 and 5 can run in
parallel with each other after 3 is done)

1. `corpus_expansion.py` → assert 40 proposals, valid vocabulary
2. `frame_annotation.py` → assert ≥456/480 records
3. `reliability_analysis.py` → this is the number the whole dissertation
   depends on; do not proceed to writing Chapter 4/5 text until this has
   run cleanly and you've read the kill-condition outcomes
4. `perturbation_generator.py` (parallel with 5)
5. `property_evaluator.py` (parallel with 4)
6. `generate_tables.py`
7. Write dissertation chapters using ONLY numbers from `results/*.json` /
   generated tables
8. Sync all three dissertation-latex copies
9. Final grep for stray "CLEAR" and for any hand-typed number not sourced
   from `results/`

Report back after step 3 completes with the headline reliability numbers
before continuing to steps 4–9 — that result determines which kill
condition, if any, applies and shapes how Chapters 4–6 are framed.
