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
| Asserted triples | 3,921 |
| Triples incl. OWL-Horst inference (GraphDB) | 5,197 |
| Ontology schema | 63 classes · 19 object properties · 11 data properties |

The ontology is aligned with the [W3C Data Privacy Vocabulary (DPV)](https://w3id.org/dpv) (`owl:equivalentClass` for Charter rights) and [ODRL](https://www.w3.org/TR/odrl-model/) (`rdfs:subClassOf` for deontic modalities).

## Repository layout

```
ai-ethics-final.ttl    Canonical ontology + knowledge graph (kept at root: w3id.org/aief redirects here)
ontology/              Copy of the TTL + validation script
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

Requirements: Python 3.11+, [GraphDB Desktop](https://graphdb.ontotext.com/) with `ai-ethics-final.ttl` loaded, and either [Ollama](https://ollama.com) (local Llama 3.1 8B) or a Groq API key.

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
- **RAGAS-style metrics:** context recall/precision computed on all 20 proposals (mean recall 0.80, mean precision 0.030 — retrieval is deliberately broad by design); faithfulness/answer-relevancy (LLM-judge metrics) completed on a partial sample due to Groq free-tier rate limits. Full results: `evaluation/ragas_results.json`.

## Paper and dissertation

`paper/main.tex` is a standalone research-paper writeup of this work in Trinity College Dublin's dissertation LaTeX format, with five diagrams (system architecture, ontology concept diagram, knowledge graph schema, ablation methodology, and the central retrieval-vs-generation finding) — Mermaid source for each is in `paper/diagrams/README.md`. `dissertation-latex/` contains the full five-chapter MSc dissertation this paper is drawn from. Both compile with a standard TeX Live installation (e.g. on Overleaf); no LaTeX toolchain is bundled here.

## Citation

If you use the AIEF ontology or pipeline, please cite:

> Ganapathy Amuthan, N. (2026). *AI-Assisted Ethics Assessment Framework for Early-Stage Research Projects: An Ontology-Driven Knowledge Graph and Retrieval-Augmented Generation Approach.* MSc dissertation, Trinity College Dublin.

## Acknowledgements

Ontology review by Dr. Delaram Golpayegani (ADAPT Centre). Builds on the FRIA ontology work of Pandit & Rintamäki and the AIRO ontology. Incident data sourced from the [AIAAIC Repository](https://www.aiaaic.org/) and the [AI Incident Database](https://incidentdatabase.ai/).
