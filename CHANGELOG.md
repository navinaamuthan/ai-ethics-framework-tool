# AIEF Ontology & Knowledge Graph — Changelog

All notable changes to the ontology (`ai-ethics-final.ttl`) and its populated knowledge graph are
documented here. Versions follow semantic versioning applied to the ontology schema and data:
MAJOR for breaking structural changes, MINOR for additive content (new requirements/incidents),
PATCH for corrections to existing content.

Every entry below is evidence-driven: each was triggered by a specific validation finding
(expert review, an automated tool, or a targeted re-verification), not a stylistic preference.

## [2.1.2] — 2026-07-20

### Changed
- **Charter-rights matching: binary presence → density-weighted scoring.** Replaced
  substring presence matching in `extract_keywords()` / `get_matched_rights()` with
  occurrence counts, per-right density scores (`n_types + 100 × occ/words`), a
  salience threshold (incidental single mentions dropped unless the keyword is
  topic-defining), and a top-K=8 cap before requirement retrieval. Removed bare
  `"data"` (too broad) and unconditional Art41 injection (Art41 now only via
  admin-process keywords: admissions/disciplinary/REAMS/welfare/public sector/
  transparency/accountability/explain). Art8 injects only on personal/identifiable
  data signals. Same root cause as the risk-category TF bug: unweighted presence
  treats a footnote mention as equal to the central topic, flooding downstream
  retrieval. Before→after on 20 proposals: mean rights **7.8→5.3**; Art8 **20→18**/20
  (now conditional); Art41 **12→0**/20; P01 **10→6** rights / **~196→112** requirements.
  IDF risk-category validation still holds at **17/20** Transparency (P15/P20/P19
  correctly exclude; P19 is a newly honest drop — HE021 maps via Art1/Art11, which
  are no longer weakly matched). Phase-3 checks (P13≠Art21, P20=Art31, Art12 on
  protest text) still pass.

## [2.1.1] — 2026-07-20

### Changed
- **Risk-category ranking: allowlist → two-pool TF + IDF.** Replaced the hardcoded
  `ALWAYS_SURFACE_IF_PRESENT` allowlist (`Transparency`, `EnvironmentalHarm`,
  `Sustainability`, `ChildrenRights`) in `retrieve_risk_categories_for_proposal`
  with a two-pool ranker over global `:hasRisk`/`:demonstratesRisk` document
  frequencies (`ontology/risk_category_doc_frequency.json`, built by
  `ontology/compute_risk_category_idf.py`): the first 6 slots go to highest
  per-proposal term frequency (proposal-specific evidence mass); remaining
  slots to `top_n=10` go to highest IDF among categories not yet selected
  (rare-but-retrieved). Pure TF×IDF fails under Phase-0 seeding — high-recall
  proposals retrieve nearly the full taxonomy, so raw TF lets Accountability
  dominate and binary IDF promotes every ultra-rare seed label. Two-pool
  coverage ranking is a standard IR pattern and needs no hand-picked category
  list. Validation on 20 synthetic proposals: Transparency in top-10 for
  **18/20** (matching the allowlist baseline); P15/P20 correctly exclude it;
  previously unnamed rare categories (FalseIdentification, AddictionRisk,
  FunctionCreep, Surveillance, DemocraticProcessHarm) now surface where
  retrieved. No severity multiplier — `:hasRisk` triples carry no reified
  severity annotation.

## [2.1.0] — 2026-07-20

### Fixed (expert-review remediation — Monique / Delaram comments)
- **Risk taxonomy never reached the LLM.** `:hasRisk` was asserted on only 2/207 requirements;
  retrieval selected only `:mapsToRight` / `:requirementText` / `:framework` / `:tier` / `:mandatory`.
  Phase 0 populated `:hasRisk` across all requirements; Phase 1 wires `sectionReference` + risk
  categories into SPARQL retrieval; Phase 2 constrains `identified_risks[].risk_category` to the
  retrieved taxonomy (with an explicit Transparency / Well-being surfacing rule).
- **"Defaults to Art 21" pattern.** `get_matched_rights()` always injected Art41+Art8 and mapped
  bias/fairness keywords to Art21. Phase 3 adds a SHACL-style structural disambiguation step
  (identifiable individual/group treatment → Art21; systemic/bibliometric information quality →
  Art11/Art22) and softens the unconditional Art41/Art8 inject. Acceptance: P13 no longer surfaces
  Art21; P20 surfaces Art31; protest-adjacent text surfaces Art12.
- **Missing Art12.** Added `Art12_FreedomOfAssembly` (class + annotation). HE018→Art37 mapping
  verified present.

### Added
- **15 formal RiskCategory subclasses** formalising the incident `:demonstratesRisk` vocabulary
  (Surveillance, Manipulation, ChildrenRights, Dignity, GenderHarm, EconomicHarm, EmploymentHarm,
  Accountability, LibertyViolation, ExpressionHarm, DataBreach, Deception, IntellectualProperty,
  FalseIdentification, DataGovernance) — extending the original 12 to ~27 first-class categories.
- **SHACL Phase 4 shapes:** `TransparencyDisclosureShape`, `SustainabilityDisclosureShape`,
  `AssemblyAssociationShape`; `ChildrenMonitoringShape` broadened to facial/emotion recognition of
  children. Documented as a standalone RQ2 comparison arm (`shacl/PHASE4_RQ2_FINDING.md`).
- **FRIA `risk_category_breakdown`** in `docgen_templates.yaml` / `generate_documentation.py`.
- **E8 risk-category miss** in `analysis/error_taxonomy.py`; before/after case study at
  `analysis/results/phase6_before_after.md`.
- Local rdflib SPARQL fallback in `sparql_retrieval.py` when GraphDB is unreachable.

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
  to keep those results comparable to their originally-reported values.
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
  these counts were themselves later found to undercount the true schema and corrected in v2.0.0 to
  125/22/16, reflecting classes and properties always present in
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
the ontology from v1.0.0 onward; earlier lower figures were simply never
re-verified against the file until 2026-07-16.
