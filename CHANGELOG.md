# AIEF Ontology & Knowledge Graph — Changelog

All notable changes to the ontology (`ai-ethics-final.ttl`) and its populated knowledge graph are
documented here. Versions follow semantic versioning applied to the ontology schema and data:
MAJOR for breaking structural changes, MINOR for additive content (new requirements/incidents),
PATCH for corrections to existing content.

Every entry below is evidence-driven: each was triggered by a specific validation finding
(expert review, an automated tool, or a targeted re-verification), not a stylistic preference.
This is the record referenced from the dissertation's Design Science Research framing
(`dissertation-latex/project/project.tex`, §Research Methodology) as the artifact's iterative
build-evaluate cycle.

## [2.0.0] — 2026-07-16

### Fixed
- **Art48_PresumptionOfInnocence class-hierarchy gap.** The individual was declared with an
  `owl:equivalentClass` (DPV alignment) and an `rdfs:label` but was never given `rdf:type owl:Class`
  or `rdfs:subClassOf` into the `EUCharterRight` hierarchy — meaning it was invisible to any
  `rdfs:subClassOf*` traversal, including the ontology-level SHACL data shapes introduced in this
  release. Found via `shacl/validate_ontology_shapes.py`, which initially reported 555 false-positive
  violations against a wrong assumption about the ontology's rights-modelling pattern (individuals of
  a `FundamentalRight` class); investigating the false positive surfaced the real, separate gap. Fixed
  by adding `:Art48_PresumptionOfInnocence rdf:type owl:Class ; rdfs:subClassOf :Title6_Justice .`

### Added
- **Ontology-level SHACL data shapes** (`shacl/ontology-data-shapes.ttl`, 11 shapes): structural
  integrity constraints over the KG itself (uniqueness of `requirementID`/`incidentID`, type
  consistency of `mapsToRight`/`impactsRight` targets, tier/mandatory-flag consistency, orphaned-right
  detection), distinct in purpose from the application-level risk-rule shapes. 9/11 pass cleanly; one
  legitimate ongoing finding retained (12 Tier-2 requirements demand evidence inconsistent with their
  reflective tier — not yet resolved, tracked as future work).
- **3 incidents** (AIAAIC-071 SyRI, AIAAIC-072 US predictive-policing discontinuations, AIAAIC-073
  GPT-detector bias) added specifically to stress-test the RQ1 landscape-analysis finding that
  Articles 13, 15, and 48 carry incident evidence but zero requirement coverage. All three gaps
  persisted under this deliberate augmentation (70→73 incidents). Scoped to the landscape re-analysis
  only; the primary 20-proposal evaluation continues to use the pre-augmentation 70-incident baseline
  to keep those results comparable to their originally-reported values (see dissertation footnote,
  Table "AIEF ontology structural summary").
- **21 → 27 SHACL risk-rule shapes**: 6 compound/conjunctive rules added (`shacl/aief-risk-shapes.ttl`)
  demonstrating auditable multi-condition escalation logic (e.g. children + continuous monitoring +
  no safeguards → automatic priority-1 escalation) not expressible by the atomic rules alone.

## [1.2.0] — 2026-07-15

### Fixed
- **Production/verification repository divergence.** The source Turtle file was deduplicated
  (removing conflicting duplicate blocks for R010 and R054) on 2026-07-13, but the production GraphDB
  repository that the RAG pipeline queries at runtime (`ai-ethics-kg`) was never reloaded with the
  corrected file — a distinct oversight from editing the source file. Verified directly: the live
  repository still returned two conflicting `requirementText` values for R010 as of 2026-07-14. Fixed
  by clearing and reloading the production repository from the corrected source; all RAGAS-style
  evaluation metrics were re-run and context recall/precision were confirmed bit-for-bit identical
  before and after the fix (0.7962326562326563 to sixteen significant figures), evidencing the
  duplication was namespace/property-scoped and had not corrupted identifier-level retrieval.
- **Materialised-triple ruleset mismatch.** An earlier verification pass (2026-07-13) loaded the
  ontology into a separate scratch repository configured with the stricter `owl-horst-optimized`
  ruleset and reported 5,197 materialised triples. This did not reflect the `rdfsplus-optimized`
  ruleset actually deployed in production (4,847, later 4,863 post-Art48-fix). Corrected everywhere
  the earlier figure had been cited.

## [1.1.0] — 2026-07-13

### Fixed
- **Legacy namespace duplication.** The production repository held the entire graph twice, once under
  a legacy `http://example.org/ai-ethics#` namespace and once under the permanent `w3id.org/aief/`
  namespace — inflating reported triple counts (4,282 asserted / 9,718 materialised) and the
  requirement count (217, later corrected to the true 207). Root cause: an earlier load never cleared
  the repository before reloading the corrected/renamespaced source file. Fixed by clearing and
  reloading; verified via two independent methods (GraphDB asserted-only SPARQL count and an
  independent `rdflib` parse of the source file), which now agree exactly.
- **Duplicate requirement blocks.** R010 and R054 were each defined twice in the source Turtle with
  conflicting `requirementText` and `sectionReference` values (not literal duplicate triples, which
  RDF would silently deduplicate, but genuinely conflicting assertions about the same IRI). Fixed by
  removing the duplicate block for each, retaining the more complete/accurate version.
- **ACM005 mapping omission.** Found during the RQ1 landscape gap-verification pass: ACM005 had no
  `mapsToRight` triple at all. Corrected to map to `Art17_RightToProperty`.

## [1.0.0] — 2026-06-26

### Added
- Initial public release. 63 classes / 19 object properties / 11 data properties (see note below —
  these counts were themselves later found to undercount the true schema and corrected in v2.0.0's
  contemporaneous dissertation text to 125/22/16, reflecting classes and properties always present in
  the source file but not previously tallied correctly).
- Permanent namespace registered at `https://w3id.org/aief/` via the W3C Permanent Identifier
  Community Group.
- Delaram Golpayegani's (ADAPT Centre) seven-point ontology review implemented in full: namespace
  migration off placeholder `example.org` URIs, DPV EU Fundamental Rights alignment via
  `owl:equivalentClass`, ODRL deontic-modality alignment via `rdfs:subClassOf`, `rdfs:label` /
  `rdfs:comment` / `dct:source` annotations, REAMS Tier 1/2 formalisation, concept diagram.

---

**Note on schema-count corrections:** the 63/19/11 → 125/22/16 class/property-count correction is not
listed as its own dated entry above because it was a measurement correction (an independent count
against the actual source file, not a change to the file's content) rather than an ontology edit. It
is documented here for completeness: the true counts were verified via `rdflib` parse and were true of
the ontology from v1.0.0 onward; the dissertation's earlier, lower figures were simply never
re-verified against the file until 2026-07-16.
