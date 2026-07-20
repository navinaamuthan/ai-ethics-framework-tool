# AIEF — AI-Assisted Ethics Assessment Framework

**Ontology-driven knowledge graph and retrieval-augmented generation for multi-framework AI ethics assessment of research proposals.**

Navina Ganapathy Amuthan · MSc Computer Science (Intelligent Systems), Trinity College Dublin
Supervisor: Prof. Dave Lewis, ADAPT Centre · Ontology review: Dr. Delaram Golpayegani

AIEF takes a free-text AI research proposal and produces a structured, traceable ethics compliance assessment across four governance frameworks — **TCD REAMS**, the **EU AI Act (Art. 27 FRIA)**, **Horizon Europe (Ethics by Design)**, and **ACM/NeurIPS guidelines** — with every finding mapped to **EU Charter of Fundamental Rights** articles and grounded in documented AI incidents.

- **Ontology (persistent URI):** https://w3id.org/aief/
- **Live demo:** deployed on Vercel (see repository "About" link)

## What's in the knowledge graph

| Element | Count |
|---|---|
| Governance requirements | **207** (REAMS R001–R087 · EU AI Act AI001–AI030 · Horizon Europe HE001–HE052 · ACM/NeurIPS ACM001–ACM038) |
| AI incidents (AIAAIC-001 … 070) | 70 |
| Charter rights mappings (`mapsToRight`) | 342 |
| Asserted triples | 3,931 |
| Triples incl. RDFS+ inference (GraphDB production ruleset) | 4,863 |
| Ontology schema | 125 classes · 22 object properties · 16 data properties |

The ontology is aligned with the [W3C Data Privacy Vocabulary (DPV)](https://w3id.org/dpv) (`owl:equivalentClass` for Charter rights) and [ODRL](https://www.w3.org/TR/odrl-model/) (`rdfs:subClassOf` for deontic modalities).

## Repository layout

```
ai-ethics-final.ttl    Canonical ontology + knowledge graph (kept at root: w3id.org/aief redirects here)
ontology/              Copy of the TTL + validation script
kg-export/             Populated graph as TTL/N-Triples — load into any triple store, no GraphDB required
rag-pipeline/          Python RAG pipeline (SPARQL retrieval → prompt building → LLM call → scoring)
evaluation/            Evaluation outputs per model, OOPS! report, RAGAS results
webapp/                Next.js 14 demo application (deployed on Vercel)
docs/                  Concept and architecture diagrams
paper/                 Standalone research paper (Trinity LaTeX format, with diagrams)
dissertation-latex/    Full five-chapter MSc dissertation (LaTeX source)
```

## Architecture

```
Proposal text ──► Keyword extraction ──► SPARQL retrieval (GraphDB) ──► Prompt construction ──► LLM ──► Structured assessment
                                        207 requirements · 70 incidents · 342 rights mappings
```

The pipeline separates **retrieval** (knowledge-graph driven, model-agnostic) from **generation** (LLM-dependent). Retrieval recall is 0.99 regardless of the LLM used; risk-classification accuracy scales with model capacity (65% at Llama 3.1 8B, 90% at Llama 3.3 70B on 20 stratified synthetic proposals).

## Running the RAG pipeline

Requirements: Python 3.11+, [GraphDB Desktop](https://graphdb.ontotext.com/) with `ai-ethics-final.ttl` loaded, and either [Ollama](https://ollama.com) (local Llama 3.1 8B) or a Groq API key. If you just want to run SPARQL queries against the populated graph without standing up GraphDB, load `kg-export/aief-asserted.ttl` (or `aief-materialised.ttl` for RDFS+-derived inferences) into `rdflib` or any triple store instead — see `kg-export/README.md`.

```bash
cd rag-pipeline
pip install requests python-dotenv
export GROQ_API_KEY=...          # only for the Groq backend
python run_evaluation.py         # full evaluation over 20 synthetic proposals
python score_evaluation.py       # score against ground truth
python run_ablation.py           # LLM-only vs KG-only vs full pipeline
```

## Running the web app

```bash
cd webapp
npm install
echo "GROQ_API_KEY=your_key" > .env.local
npm run dev
```

Deployment (Vercel): set the project **Root Directory** to `webapp/` and add `GROQ_API_KEY` as an environment variable. The app ships with a static knowledge-graph snapshot (`webapp/lib/kg-snapshot.json`, exported from GraphDB) so no triplestore is needed in production; set `USE_LIVE_KG=true` + `GRAPHDB_ENDPOINT` to query a live endpoint instead.

## Evaluation summary

- **Dataset:** 20 synthetic proposals (9 High / 7 Medium / 4 Low risk) + 5 real-world cases (Optum, COMPAS, Amazon Rekognition, Facebook ad delivery, the Epic Sepsis Model — Wong et al., *JAMA Internal Medicine* 2021).
- **Retrieval recall:** 0.99 across all model configurations — the KG contribution is model-agnostic.
- **Risk accuracy:** 65% (Llama 3.1 8B, Ollama) / 90% (Llama 3.3 70B, Groq); misclassifications skew conservative (upward).
- **Ablation:** LLM-only cites no traceable requirement IDs and hallucinates incidents; the full pipeline cites requirement IDs with framework provenance and grounds findings in curated incidents.
- Qwen3 32B results are exploratory only (7/20 runs failed on free-tier rate limits) and excluded from the primary comparison — see `evaluation/results/qwen3-32b-exploratory/`.
- Annotation methodology validated by inter-annotator agreement on incident–rights mappings (Cohen's κ = 0.712, substantial).
- **OOPS! ontology validation:** 8 non-critical pitfall categories found (2 "Important": missing domain/range on 5 properties, missing disjointness axioms; rest "Minor" annotation-completeness gaps). Full report: `evaluation/oops_report.xml`.
- **RAGAS-style metrics:** context recall/precision on all 20 proposals (mean recall 0.80, mean precision 0.030 — retrieval is deliberately broad by design); faithfulness 0.35 / answer relevancy 0.88 (LLM judge, 19/20). Full results: `evaluation/ragas_results.json`.
- **Retrieval baseline (controlled comparison):** ontology-driven SPARQL retrieval reaches 0.992 recall vs BM25 0.915 / TF-IDF 0.925 at matched set size; lexical baselines fall to 0.61–0.64 at k=100. `evaluation/retrieval_baselines.json`.
- **Ontology evaluation battery:** 20/20 competency questions pass (incl. exact-value checks); HermiT reasoner reports zero inconsistent classes; OOPS! scan as above. `analysis/competency_questions.py`.
- **Error taxonomy:** zero risk under-classifications across 20 proposals (2 over-classifications); 98.9% of requirement misses are generation-stage, with citation recall skewed against the largest framework (REAMS 0.067 vs ACM 0.297). `analysis/results/error_taxonomy.json`.
- **Requirement redundancy (RQ1):** 207 requirement statements compress to 180 distinct obligation clusters (13.0% paraphrase redundancy); 9 clusters are cross-framework pairs, spanning every pairwise framework combination; none span 3+ frameworks at the calibrated similarity threshold. `analysis/requirement_clustering.py`.
- **Gap stress test (RQ1):** the 3 genuine harm-without-governance gaps (Art 13, 15, 48) survive deliberate augmentation with 3 additional, independently-sourced real incidents (SyRI, US predictive-policing discontinuations, GPT-detector bias) — all remain at zero requirement coverage. `analysis/landscape_analysis.py`.
- **Ontology data-shape validation:** 9/11 SHACL data shapes pass cleanly against the live KG; one genuine modelling gap found and fixed (Art 48 was never wired into the Charter-right class hierarchy) and one legitimate finding retained (12 Tier-2 requirements demand evidence inconsistent with their reflective tier). `shacl/ontology-data-shapes.ttl`, `shacl/validate_ontology_shapes.py`.
- **SHACL widened + compound rules:** rule set expanded from 6→27 shapes (21 atomic + 6 compound conjunctive-escalation rules) across 20 of 22 Charter dimensions; precision 0.417→0.566, recall 0.193→0.327. Compound rules demonstrate auditable multi-condition escalation logic (e.g. children + monitoring + no safeguards → automatic priority-1 escalation) that a single aggregated label cannot express. `shacl/aief-risk-shapes.ttl`, `shacl/evaluate_shacl.py`.
- **Repeated-run variance study:** Llama 3.1 8B, 4 full runs (original + 3 repeats) — mean accuracy 66.2% (95% bootstrap CI [0.613, 0.725]), 5/20 proposals (25%) show a genuine label disagreement across runs, directionally mixed (not purely conservative-biased — one proposal under-classifies High→Medium on 3/4 runs). Llama 3.3 70B: 1 repeat completed (0/20 flips vs original), 2 further repeats blocked by Groq's free-tier daily token cap. `evaluation/variance/`.

## Paper and dissertation

`paper/main.tex` is a standalone research-paper writeup of this work in Trinity College Dublin's dissertation LaTeX format, with five diagrams (system architecture, ontology concept diagram, knowledge graph schema, ablation methodology, and the central retrieval-vs-generation finding) — Mermaid source for each is in `paper/diagrams/README.md`. `dissertation-latex/` contains the full five-chapter MSc dissertation this paper is drawn from. Both compile with a standard TeX Live installation (e.g. on Overleaf); no LaTeX toolchain is bundled here.

## Citation

If you use the AIEF ontology or pipeline, please cite:

> Ganapathy Amuthan, N. (2026). *AI-Assisted Ethics Assessment Framework for Early-Stage Research Projects: An Ontology-Driven Knowledge Graph and Retrieval-Augmented Generation Approach.* MSc dissertation, Trinity College Dublin.

## Acknowledgements

Ontology review by Dr. Delaram Golpayegani (ADAPT Centre). Builds on the FRIA ontology work of Pandit & Rintamäki and the AIRO ontology. Incident data sourced from the [AIAAIC Repository](https://www.aiaaic.org/) and the [AI Incident Database](https://incidentdatabase.ai/).
