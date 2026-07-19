# Populated knowledge graph export

The AIEF ontology schema is published at [w3id.org/aief](https://w3id.org/aief/), but the schema alone doesn't let anyone reproduce the SPARQL queries reported in the evaluation — for that you need the *populated* graph (207 requirement individuals, 70 incident individuals, 342 Charter-rights mapping triples, etc.) loaded into a triple store. These two files are that export, so reproduction doesn't require standing up GraphDB Desktop from scratch.

## Files

| File | Contents | Triples | Verified via |
|---|---|---|---|
| `aief-asserted.ttl` / `aief-asserted.nt` | Only the triples explicitly in the source data (no reasoning) | 3,931 | Independently cross-checked with `rdflib` (Python) parsing the source `ai-ethics-final.ttl` directly — identical count |
| `aief-materialised.ttl` | Asserted triples plus everything derivable under the RDFS+ ruleset (`rdfsplus-optimized`) — the ruleset actually configured on the production GraphDB repository the RAG pipeline queries at runtime | 4,863 | Re-verified 15 July 2026 after a data-consistency fix (see below) |

Both were generated via `GET /repositories/ai-ethics-kg/statements` against a local GraphDB Desktop instance, using `?infer=false` for the asserted-only export and no parameter (GraphDB's default) for the materialised export.

## A note on ruleset choice

An earlier verification pass (13 July 2026) loaded the ontology into a separate scratch repository configured with a stricter `owl-horst-optimized` ruleset and reported 5,197 materialised triples. That figure does not reflect the ruleset actually deployed in production and has been superseded by the 4,863 figure above, which was generated against the real production repository (`ai-ethics-kg`) that `rag-pipeline/sparql_retrieval.py` queries at runtime. If you load these files into your own triple store with a different reasoner (e.g. full OWL-DL), your materialised count will differ from both — this is expected and is a property of the reasoner, not the data.

## A note on a fixed data-consistency bug

Between 13 and 15 July 2026, the source Turtle file (`ai-ethics-final.ttl`) was deduplicated (two conflicting definitions of requirements R010 and R054 were merged into one each), but the production GraphDB repository had not yet been reloaded from the corrected file — a distinct step from editing the source file. This was caught and fixed on 15 July: the production repository was cleared and reloaded from the corrected source. Both exports here reflect the corrected, post-fix state. If you're comparing against evaluation numbers dated 14 July 2026 or earlier, be aware some of those (the RAGAS-style automated metrics specifically) were regenerated on 15 July for this reason — see the dissertation's Section 4.6 / the paper's RAGAS subsection for the full account.

## Loading into your own triple store

**Gotcha:** individuals are asserted with their specific deontic type (`rdf:type :Obligation`, `:Permission`, or `:Prohibition`), not directly `rdf:type :Requirement` — the latter only holds after RDFS+ reasoning derives it via the `rdfs:subClassOf` chain. So `?r a :Requirement` returns nothing against `aief-asserted.ttl` (no reasoner) but works against `aief-materialised.ttl` (reasoning already applied). The example below queries the asserted file directly via `:belongsToFramework`, sidestepping the issue; swap in `aief-materialised.ttl` if you want to rely on `a :Requirement` instead.

```bash
# rdflib (Python) — quickest way to run ad-hoc SPARQL locally, no server needed
pip install rdflib
python3 -c "
import rdflib
g = rdflib.Graph()
g.parse('aief-asserted.ttl', format='turtle')
print(len(g), 'triples loaded')
# example query: list EU AI Act requirements (works on the asserted-only file — see gotcha above)
for row in g.query('''
    PREFIX : <https://w3id.org/aief/>
    SELECT ?id ?text WHERE {
        ?r :belongsToFramework :EUAIAct ; :requirementID ?id ; :requirementText ?text .
    } LIMIT 5
'''):
    print(row.id, '-', row.text)
"
```

Verified output (15 July 2026):
```
AI001 - Assess whether organisation is obligated to conduct a FRIA (deployer of high-risk AI system)
AI002 - Record necessity status: FRIA Required or FRIA Not Required
AI003 - Record when FRIA was created, modified, submitted, accepted
AI004 - Record who conducted the FRIA (organisation, personnel, contributors)
AI005 - Record identifier/version of FRIA — must be regularly updated
```

Or load `aief-materialised.ttl` into any RDF store (Apache Jena Fuseki, GraphDB Free, Blazegraph, etc.) if you want the RDFS+-derived inferences (e.g. `a :Requirement` working directly, `rdfs:subClassOf` transitivity) without configuring a reasoner yourself.
