# Reference-Label Reliability as a Precondition for Evaluating Automated AI Ethics Assessors

MSc Dissertation, School of Computer Science and Statistics, Trinity College Dublin.

**Author:** Navina Ganapathy Amuthan  
**Supervisor:** Dave Lewis  
**Degree:** M.Sc. Computer Science (Intelligent Systems), 2026

## Overview

Automated tools for assessing the ethical and fundamental-rights risks of AI research are increasingly compared using reference-label-based evaluation: system outputs are scored against expert-annotated labels using accuracy or Cohen's κ. This work identifies and addresses a precondition that such evaluation practice leaves unchecked: an evaluation protocol that scores an assessor against reference labels is itself a measurement instrument, and its validity depends on the reliability of those labels.

The dissertation contributes a two-stage diagnostic methodology that determines whether reference-label-based evaluation is a sound basis for comparison for a given assessor and corpus, before that evaluation is used to draw conclusions. Stage one computes stratified inter-annotator reliability, derives a reliability-ceiling estimate, and applies a decision rule classifying assessor-pair comparisons as discriminable or not by accuracy. Stage two, invoked only when accuracy is uninformative, illustrates a reference-independent alternative based on contestability.

The methodology is developed and demonstrated on AIEF (AI Ethics Assessment Framework), a knowledge-graph-and-retrieval-augmented system built for this research, instantiated in four configurations spanning a symbolic rule engine, two language-model scales, and a degenerate keyword baseline. AIEF is the empirical vehicle for this research; the diagnostic methodology is its contribution.

## Repository Structure

```
ai-ethics-framework-tool/
├── ontology/              OWL ontology and knowledge graph (207 governance
│                          requirements across TCD REAMS, EU AI Act, Horizon
│                          Europe, and ACM/NeurIPS, mapped to the EU Charter
│                          of Fundamental Rights)
├── shacl/                 SHACL shapes implementing the symbolic assessor
├── rag-pipeline/          Retrieval, prompt construction, and LLM-based
│                          assessment generation
├── diagnostic/            The diagnostic methodology pipeline: corpus
│                          construction, perspective-stratified annotation,
│                          reliability analysis, perturbation testing,
│                          property evaluation, and result/table generation
├── evaluation/            Assessor outputs and evaluation artefacts
└── dissertation-latex/    Dissertation source (this is the canonical copy;
                           see FINAL_DISSERTATION_UPDATED/ for the
                           standalone submission build)

FINAL_DISSERTATION_UPDATED/
├── main.tex               Master file (TCD tcdthesis.sty)
├── Introduction.tex       Problem, motivation, research question
├── StateOfTheArt.tex      Literature review
├── Design.tex             The diagnostic methodology
├── Implementation.tex     Apparatus, corpus, and experimental protocol
├── Evaluation.tex         Results and critical analysis
├── Conclusions.tex        Summary, limitations, future work
├── references.bib
└── figures/               Architecture and process diagrams (Mermaid
                           source) and pgfplots data figures
```

## Reproducing the Diagnostic

The diagnostic pipeline runs as a sequence of six steps under `diagnostic/`:

```bash
cd ai-ethics-framework-tool/diagnostic
make all
```

This regenerates, in order: the 40-proposal corpus, the perspective-stratified annotation set, the reliability analysis and decision-rule verdicts, the perturbation study, the property evaluation, and the LaTeX result tables under `diagnostic/results/tables/`. Every quantitative result reported in the dissertation is produced by this pipeline; no figures are hand-entered.

Requires Python 3 and API access to the language model backends configured in `rag-pipeline/` (Ollama for local inference, Groq for hosted inference).

## Compiling the Dissertation

The dissertation is written for Trinity's `tcdthesis.sty` M.Sc. template. To compile:

```bash
cd FINAL_DISSERTATION_UPDATED
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

`tcdthesis.sty` is not included in this repository and must be obtained from Trinity's Overleaf template. Two figures (`figures/aief_architecture.mmd`, `figures/diagnostic_flowchart.mmd`) are Mermaid diagrams; compile them at [mermaid.live](https://mermaid.live) and export as PNG into `figures/` before building. The remaining evaluation figures are native `pgfplots` and require no external step.

## Ontology

The AIEF ontology has a permanent identifier at [https://w3id.org/aief/](https://w3id.org/aief/), resolving to the current TTL file.

## Use of Generative AI

Use of generative AI tools in this work is disclosed in full in the dissertation itself (`main.tex`), covering literature summarisation, synthetic data generation, and automated execution of evaluation scripts. All experimental design, verification, and interpretation are the author's own.

## Citation

If referencing this work, please cite the dissertation directly. Full bibliographic details are available on request from the author.

## Contact

Navina Ganapathy Amuthan — ganapatn@tcd.ie
