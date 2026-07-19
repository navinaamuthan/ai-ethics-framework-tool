# Where AI Governance Frameworks Agree, Diverge, and Leave Harm Ungoverned: A Knowledge-Graph Analysis of Four Ethics Regimes

*Draft short paper — extracted from the AIEF MSc dissertation (Trinity College Dublin, 2026) for
standalone submission consideration (FAccT / AIES short-paper track). Status: first draft, not yet
submitted anywhere. Author to confirm venue, formatting, and co-authorship before any submission.*

## Abstract (150 words)

Researchers building AI systems face ethics obligations from at least four distinct authorities —
institutional review boards, national/regional AI legislation, research funders, and professional
codes of conduct — each with its own terminology, granularity, and enforcement mechanism. We harmonise
207 requirements from four such regimes (an institutional research-ethics system, the EU AI Act,
Horizon Europe's Ethics by Design guidance, and ACM/NeurIPS codes) into a single OWL ontology and
knowledge graph, mapped to EU Charter of Fundamental Rights articles and cross-referenced against 73
documented AI harm incidents. We report three findings: (1) convergence across frameworks is real but
uneven — 8 of 18 mapped Charter rights are addressed by all four regimes, while children's rights are
addressed by only one; (2) three Charter rights carry documented incident evidence but zero requirement
coverage in any framework, a gap that persists under deliberate evidentiary stress-testing; (3) 13% of
requirement statements are near-verbatim paraphrases of another framework's requirement, evidencing
redundant, uncoordinated policy-making rather than deliberate harmonisation. We release the ontology,
knowledge graph, and analysis scripts as open, reproducible artifacts.

## 1. Introduction

[Draw from dissertation Introduction \S1 and Background \S2.1 "The Cross-Framework Compliance
Challenge" — condense to ~400 words. Lead with the practical problem (duplicated, uncoordinated
ethics-review burden on researchers), not the system. This paper's contribution is the *empirical
landscape analysis*, not the assessment tool built around it — the tool should be mentioned as the
instrument that produced the analysis, in one sentence, with a link to the full system.]

## 2. Method

### 2.1 Ontology and Knowledge Graph Construction

[Draw from dissertation \S\ref{sec:ontology}, \S\ref{sec:kg}. Key facts to include: 125 classes, 22
object properties, 16 data properties; 207 requirements manually extracted and classified by deontic
modality; requirements mapped to EU Charter articles via `mapsToRight`; validated via 20 competency
questions (Grüninger & Fox method) and HermiT reasoner consistency check (zero inconsistencies); OOPS!
pitfall scan (8 non-critical categories, none Critical severity).]

### 2.2 Incident Corpus and Evidentiary Stress-Testing

[73 incidents from AIAAIC and the AI Incident Database, annotated with impacted Charter rights
(Cohen's kappa = 0.712 on a 10-incident inter-annotator pilot). Describe the stress-test methodology
explicitly: 3 additional incidents were deliberately sourced for the two thinnest-evidenced gap rights
(Art. 13, Art. 48) to test whether the gap finding was an artifact of sparse initial evidence. This
methodological move — actively trying to falsify your own finding by seeking disconfirming evidence —
is worth stating explicitly as a strength in a short paper aimed at a venue that will scrutinise
empirical rigor.]

### 2.3 Requirement Redundancy Clustering

[Sentence embeddings (MiniLM) of all 207 requirement texts, agglomerative clustering (complete
linkage, cosine distance), threshold calibrated against the empirical cross-framework similarity
distribution (90th percentile = 0.670) rather than chosen to hit a target number — state this
calibration methodology explicitly, since an unstated arbitrary threshold is a common and fair
critique of clustering-based findings.]

## 3. Findings

### 3.1 Convergence Is Real but Uneven

[Table: coverage matrix. 8/18 mapped rights covered by all 4 frameworks (data protection,
non-discrimination, dignity, remedy — the "obvious" shared priorities); Article 24 (children's
rights) covered by REAMS alone. State the implication plainly: a researcher whose work touches
children's data is protected by institutional review but not by AI Act, funder, or professional-code
language — a genuine cross-framework gap in coverage of a specific vulnerable population.]

### 3.2 Harm Without Governance

[The headline finding. Table: Art 15 (11 incidents, 0 requirements), Art 48 (7 incidents post
stress-test, 0 requirements), Art 13 (2 incidents post stress-test, 0 requirements). Each incident
cited with one sentence of real-world context (SyRI, predictive-policing discontinuations, COMPAS,
GPT-detector bias, GitHub Copilot). State the stress-test result as the key robustness claim: *the gap
survived deliberate evidentiary augmentation and is not an artifact of an initially thin incident
sample.*]

### 3.3 Requirement Redundancy: 13% Uncoordinated Overlap

[207 -> 180 distinct obligation clusters; 9 cross-framework pairs, one example from every pairwise
framework combination. Frame this as evidence of *uncoordinated*, not *deliberately harmonised*,
overlap — each framework was authored independently and arrived at near-identical language for some
obligations (e.g. re-identification risk, environmental footprint) without apparent cross-reference to
each other. This is itself informative for policy coordination: these are the clearest candidates for
future cross-framework harmonisation efforts, since the substantive content is already aligned.]

## 4. Discussion

[Connect to the FRIA/HUDERIA/ForHumanity landscape — this analysis is complementary to, not
competitive with, single-framework FRIA methodologies: it is specifically the *multi-framework*
comparative view that a single-regime FRIA process cannot produce. Acknowledge the annotation-validity
limitation directly and early: the requirement-to-rights mappings underlying \S3.1-3.2 were authored
by a single researcher (validated for the *incident*-to-rights mappings via inter-annotator kappa, not
yet for the *requirement*-to-rights mappings specifically) — state this as a limitation and a direction
for follow-up work (a second annotator's review of a requirement-mapping sample) rather than omitting
it.]

## 5. Limitations

[Single-annotator requirement mappings (see 4); four frameworks only, not exhaustive of the global
governance landscape; incident corpus of 73 is a curated subset, not a census; embedding-based
clustering is a proxy for substantive overlap, not a legal-equivalence determination — two requirements
in the same cluster may still differ in binding force or enforcement mechanism even where their text
is near-identical.]

## 6. Conclusion

[One paragraph. The reusable contribution: an open, reproducible method (ontology + KG + embedding
clustering + incident cross-referencing) for auditing any set of governance frameworks for coverage
gaps and redundant overlap, demonstrated on four AI-ethics regimes but not specific to AI ethics as a
domain.]

## Data and Code Availability

Ontology: https://w3id.org/aief/ · Repository: https://github.com/navinaamuthan/ai-ethics-framework-tool
· Analysis scripts: `analysis/landscape_analysis.py`, `analysis/requirement_clustering.py`,
`analysis/competency_questions.py` · Zenodo archive: [DOI pending, see ZENODO_INSTRUCTIONS.md]

## Author's note on what's left before this is submittable

This is a **first-draft skeleton**, not a submittable paper: every bracketed instruction above needs
to become real prose, the abstract needs trimming to whatever the target venue's word limit is, and
the tables need to be built from `analysis/results/*.json` rather than described. Before submitting
anywhere: (1) decide on co-authorship with Dave/Delaram given their contributions to the underlying
ontology and its review; (2) get the requirement-mapping second-annotation this draft flags as a gap,
since a reviewer at a venue like FAccT will ask exactly that question; (3) check the target venue's
specific short-paper template and length limit before formatting.
