# Phase 4 SHACL audit finding (RQ2)

## Two independent arms — read as separate results, never merged

**Arm A — RAG/LLM pipeline arm (retrieval + prompt constraints).** Implemented
in `rag-pipeline/sparql_retrieval.py`, `rag-pipeline/prompt_builder.py`,
`rag-pipeline/ethics_rag.py`. Produces the `*_full.json` assessments and the
generated documentation in `evaluation/generated-documentation/`. Results:
`analysis/results/phase6_before_after.md`, `evaluation/results/`.

**Arm B — SHACL structural-rules arm (independent, not wired into the LLM
prompt).** Implemented in `shacl/aief-risk-shapes.ttl` and validated directly
against proposal RDF (e.g. `shacl/example-proposals.ttl`) with a SHACL engine.
Results live under `shacl/` (e.g. `shacl/oops_report.xml`) and are never read
by `prompt_builder.py` or `ethics_rag.py`.

**Why kept separate:** this separation IS the RQ2 finding. RQ2 asks whether
scrutable SHACL structural rules and free-text LLM interpretation agree or
diverge on the same proposals. That comparison is only meaningful if each
arm's verdict is independently auditable — if SHACL flags leaked into the LLM
prompt (or vice versa), agreement/disagreement between the two would no
longer tell us anything about the SHACL-vs-LLM tradeoff, only about a single
blended pipeline. Any report or table that shows results from both arms must
label them as Arm A / Arm B (or equivalent) in separate sections — never a
single unified "pipeline result".

The SHACL risk-dimension layer (`shacl/aief-risk-shapes.ttl`) is a **standalone,
scrutable comparison arm** relative to the LLM RAG assessment — not a feed into
`prompt_builder.py` / `ethics_rag.py`. This is intentional for RQ2:

> Scrutable structural rules catch transparency, children's-monitoring, clinical-
> validation, and assembly risks that free-text LLM interpretation often omits
> or crowds out with bias/privacy framing.

Phase 4 work therefore:
1. **Audited** existing triggers (`ChildrenMonitoringShape` broadened to facial/
   emotion recognition of children — the P06 pattern).
2. **Added** `TransparencyDisclosureShape`, `SustainabilityDisclosureShape`,
   `AssemblyAssociationShape` (Art12).
3. **Did not** wire SHACL flags into the primary LLM prompt — keeping the two
   arms independent so the dissertation can report agreement/disagreement as
   evidence, rather than collapsing them into one opaque score.
