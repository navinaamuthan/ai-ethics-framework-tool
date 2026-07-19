# SHACL risk-dimension demonstrator

A prototype answer to two critiques of the main AIEF pipeline, raised in supervisory review (July 2026):

1. **A single High/Medium/Low label collapses heterogeneous risk.** A proposal can be severe on data protection, moderate on discrimination, and clean on everything else — one aggregate label hides that structure, and different disciplines legitimately weigh the dimensions differently.
2. **The ranking rationale must be scrutable.** In the main pipeline, the aggregation from per-concern risks to one label happens inside the LLM, which is not inspectable. The rules deciding *why one problem outranks another* should be machine-readable, so an evaluator can inspect them, disagree, change a priority, and re-validate — consistently and observably.

This directory demonstrates the alternative: risk rules as **SHACL shapes**, with the risk dimension, priority rank, severity tier, and written rationale all expressed **as data** in the shapes file, and validation producing a **per-dimension risk profile** per proposal instead of a single label. No LLM is involved in this layer.

**Update (16 July 2026, Week-2 widening):** the rule set was expanded from 6 shapes covering 4 Charter dimensions to **21 shapes covering 20 of the 22 Charter dimensions present in the knowledge graph**. This was done specifically to close a fairness objection: a 6-rule/4-dimension comparison against the full RAG pipeline invited the charge that the "architecture comparison" in RQ2 was rigged toward whichever side was more convenient. Two dimensions remain deliberately unruled — Art13 (Freedom of Arts and Science) and Art20 (Equality Before the Law) — because no reliable keyword signal in free text distinguishes them from the already-ruled adjacent dimensions (Art11 Expression; Art21 Non-Discrimination) without a materially richer NLU layer than the keyword bridge supports. This is stated as a scope limit, not silently dropped.

Widening the rule set changed the quantitative comparison substantially: mean precision rose from 0.417 to **0.566** and mean recall from 0.193 to **0.327** (both computed by `evaluate_shacl.py` over the same 20 proposals). The direction confirms the expected relationship — recall was bounded by rule-set coverage, not by some intrinsic limit of the SHACL approach — while the absolute recall still trails the RAG pipeline's rights coverage (0.773), which is the honest and expected result of comparing 21 hand-authored deterministic rules against an LLM with much broader (if less precise and less traceable) interpretive reach.

## Files

- `aief-risk-shapes.ttl` — 21 risk rules across 20 Charter dimensions. Each declares: `aiefsh:riskDimension` (an EU Charter right IRI), `aiefsh:priority` (editable integer), `sh:severity` (editable tier), `rdfs:comment` (the explicit rationale for its rank), and a SPARQL constraint (the inspectable pattern).
- `evaluate_shacl.py` — quantitative precision/recall of the rule set against all 20 synthetic proposals' `expected_rights` annotations, via the text→description bridge.
- `harm_evidenced_priorities.py` / `harm-evidenced-priorities.ttl` — SPARQL-derived incident in-degree per Charter right, tiered into priorities 1–3 (see provenance below).
- `text_to_description.py` — keyword bridge from free-text proposals to structured TTL for SHACL validation.
- `example-proposals.ttl` — structured descriptions of three proposals from the evaluation set (P01, P08, P13).
- `run_shacl.py` — validates and prints per-dimension profiles, ordered by priority.

## Harm-evidenced priority provenance

Default priorities are no longer intuition-only. `harm_evidenced_priorities.py` queries GraphDB for `COUNT(DISTINCT ?incident)` per right via `:impactsRight`, normalises against the maximum count, and tiers: top third → priority 1, middle → 2, remainder → 3. The generated triples (`aiefsh:harmEvidence`, `aiefsh:evidencedPriority`) are inspectable in `harm-evidenced-priorities.ttl`. Where a shape's `aiefsh:priority` differs from that right's `evidencedPriority` — e.g. Art~21 ranks evidenced-1 but Rule~3 keeps priority 2 because bias audits are remediable within the project; Art~8 ranks evidenced-2 but Rules 1–2 keep priority 1 as per-se GDPR infringements — the divergence is recorded in the shape's `rdfs:comment`. Both values are usable in the write-up: defaults are harm-evidenced; deliberate deviations are explicit and editable.

## Run it

```bash
pip install pyshacl rdflib
python run_shacl.py
```

Output (15 July 2026, verified):

```
=== P01: Facial recognition for campus security ===
  Dimension Art8_DataProtection: 2 flag(s)
    [P1 VIOLATION] Biometric data requires opt-in consent
    [P1 VIOLATION] Special-category data requires a DPIA
  Dimension Art21_NonDiscrimination: 1 flag(s)
    [P2 VIOLATION] Models affecting people require an independent bias audit

=== P08: AI chatbot for mental health support triage ===
  Dimension Art8_DataProtection: 1 flag(s)     [P1 VIOLATION]
  Dimension Art21_NonDiscrimination: 1 flag(s) [P2 VIOLATION]
  Dimension Art35_HealthCare: 1 flag(s)        [P2 warning]

=== P13: Bibliometric analysis ===
  No risk-dimension flags. All scrutable rules pass.
```

Note what the single-label pipeline loses: P01 and P08 were both non-trivial-risk proposals, but their *profiles* differ — P01 is a data-protection problem twice over, P08's risk is spread across three dimensions with clinical validation as the distinctive one. P13's profile is simply empty rather than "Low."

## The scrutability demonstration

Suppose a health-faculty ethics reviewer weighs clinical risk more heavily than the defaults. They change two triples on one shape — `aiefsh:priority 2` → `1` and `sh:severity sh:Warning` → `sh:Violation` — and re-run. Verified result: P08's clinical-validation finding moves to the top tier of its profile, ahead of the bias-audit finding. The change is one diff in a version-controllable Turtle file: consistent, observable, and reviewable in a pull request — which is what "scrutable rules" means in practice.

## Relationship to the main pipeline

The main RAG pipeline and this SHACL layer are complementary, not competing:

- The **RAG pipeline** handles free-text input and produces narrative assessments with requirement citations — broad coverage, LLM-dependent judgement.
- The **SHACL layer** handles structured proposal descriptions and produces deterministic, per-dimension rule verdicts — narrow coverage, zero LLM involvement, fully scrutable.

The bridge between them is `text_to_description.py`, which materialises structured descriptions (`aief:involvesDataCategory`, `aief:usesCapability`, …) from free text using the same keyword heuristics as the retrieval stage. Hand-authored examples in `example-proposals.ttl` remain available for deterministic demos. Negation handling in the bridge is naive (regex, not NLU) — a known limitation of the same class as keyword retrieval.

## Scope honesty

Six rules over three dimensions is a demonstrator, not a rule base. Its claim is architectural: that per-dimension, priority-as-data, evaluator-editable risk rules are expressible over the AIEF ontology with standard Semantic Web tooling (SHACL + pyshacl), and that they compose with the existing knowledge graph. Populating a full rule base — and deciding *whose* priorities the defaults encode — is exactly the kind of question the AIEF platform is meant to make explorable rather than settle.
