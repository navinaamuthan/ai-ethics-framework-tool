# AIEF: AI Ethics Assessment Framework

A system of Ontology-driven knowledge graph and retrieval-augmented pipeline for multi-framework ethics assessment of AI research proposals. This system is part of the Research Dissertation thesis submitted to Trinity College Dublin titled **"Reference-Label Reliability as a Precondition for Evaluating Automated AI Ethics Assessors"**
as part of the fulfillment of the author's Master's Degree in Computer Science.

**Author:** Navina Ganapathy Amuthan  
**Supervisor:** Dave Lewis

AIEF takes a free-text AI research proposal and produces a structured, traceable ethics compliance assessment across four governance frameworks: TCD REAMS, the EU AI Act (Art. 27 FRIA), Horizon Europe (Ethics by Design), and ACM/NeurIPS guidelines — with findings mapped to EU Charter of Fundamental Rights articles.

**Ontology (persistent URI):** [https://w3id.org/aief/](https://w3id.org/aief/)

## Repository Structure

```
ai-ethics-framework-tool/
├── ontology/          OWL ontology and knowledge graph
│                      (207 governance requirements across TCD REAMS,
│                      EU AI Act, Horizon Europe, and ACM/NeurIPS,
│                      mapped to the EU Charter of Fundamental Rights)
├── ai-ethics-final.ttl
│                      Canonical TTL at repo root (served via w3id.org/aief/)
├── shacl/             SHACL shapes implementing the symbolic assessor
├── rag-pipeline/      Retrieval, prompt construction, and LLM-based
│                      assessment generation
├── diagnostic/        Diagnostic methodology pipeline: corpus construction,
│                      perspective-stratified annotation, reliability analysis,
│                      perturbation testing, property evaluation, and
│                      result/table generation
├── evaluation/        Assessor outputs and evaluation artefacts
├── kg-export/         Exported graph snapshots for offline SPARQL use
├── analysis/          Coverage and landscape analysis scripts
├── webapp/            Next.js demo application
└── docs/              Architecture and concept diagrams
```

## Ontology

The AIEF ontology is published at [https://w3id.org/aief/](https://w3id.org/aief/), which resolves to the current TTL on `main`.

Keep the root and ontology copies in sync when editing:

```bash
cp ontology/ai-ethics-final.ttl ai-ethics-final.ttl
```

## Setup

Python 3.11+ is required. All dependencies for the ontology, RAG pipeline,
SHACL layer, and diagnostic scripts are pinned in `requirements.txt` at the
repository root:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

An LLM backend is also needed to regenerate assessments or annotations:
either a Groq API key (hosted) or [Ollama](https://ollama.com) serving
`llama3.1:8b` (local).

```bash
export GROQ_API_KEY=...            # for the Groq backend
```

For live SPARQL retrieval, load `ai-ethics-final.ttl` into a triple store
(e.g. GraphDB). For offline use, load `kg-export/` into `rdflib` or any store
— see `kg-export/README.md`.

## Running the RAG Pipeline

```bash
cd rag-pipeline
../.venv/bin/python run_evaluation.py
```

## Running the Diagnostic Pipeline

```bash
cd diagnostic
make all
```

The `Makefile` defaults to the repository-local `.venv` created above. To use
a different interpreter, override it: `make PYTHON=/path/to/python all`.

This regenerates, in order: the proposal corpus, the perspective-stratified annotation set, the reliability analysis and decision-rule verdicts, the perturbation study, the property evaluation, and LaTeX result tables under `diagnostic/results/tables/`.

## Running the Web App

```bash
cd webapp
npm install
echo "GROQ_API_KEY=your_key" > .env.local
npm run dev
```

## Contact

Navina Ganapathy Amuthan — ganapatn@tcd.ie
