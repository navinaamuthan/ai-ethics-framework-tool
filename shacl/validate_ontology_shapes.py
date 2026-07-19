"""Run the ontology-level data shapes (ontology-data-shapes.ttl) against
the live knowledge graph, reporting per-shape pass/fail and violation
counts. This validates the KG's structural integrity -- distinct from
OOPS! (schema pitfalls) and HermiT (logical consistency)."""
import rdflib
from pyshacl import validate

HERE = __file__.rsplit("/", 1)[0]
shapes = rdflib.Graph().parse(f"{HERE}/ontology-data-shapes.ttl", format="turtle")
data = rdflib.Graph().parse(f"{HERE}/../ai-ethics-final.ttl", format="turtle")

conforms, report_graph, report_text = validate(
    data, shacl_graph=shapes, advanced=True, inference="rdfs"
)

SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
violations = list(report_graph.subjects(rdflib.RDF.type, SH.ValidationResult))

# Group violations by resultMessage rather than sourceShape: sh:property
# blank-node shapes and sh:sparql constraint blank nodes do not reliably
# trace back to their parent NodeShape IRI as a string, so message text
# (which we author to be unique per shape) is the robust join key.
by_message = {}
for v in violations:
    msg = str(report_graph.value(v, SH.resultMessage, default=""))
    by_message.setdefault(msg, 0)
    by_message[msg] += 1

shape_names = sorted(str(s).rsplit("/", 1)[-1] for s in
                      shapes.subjects(rdflib.RDF.type, SH.NodeShape))
# Map each shape to the resultMessage(s) it can produce, by re-reading its
# own sh:message / sh:sparql sh:message literal(s) from the shapes graph.
shape_messages = {}
for s in shapes.subjects(rdflib.RDF.type, SH.NodeShape):
    name = str(s).rsplit("/", 1)[-1]
    msgs = set(str(m) for m in shapes.objects(s, SH.message))
    for prop in shapes.objects(s, SH.property):
        msgs |= set(str(m) for m in shapes.objects(prop, SH.message))
    for sp in shapes.objects(s, SH.sparql):
        msgs |= set(str(m) for m in shapes.objects(sp, SH.message))
    shape_messages[name] = msgs

print(f"Overall conformance: {conforms}")
print(f"Data shapes checked: {len(shape_names)}\n")
matched_messages = set()
for name in shape_names:
    hits = [(m, c) for m, c in by_message.items() if m in shape_messages.get(name, set())]
    if hits:
        for m, c in hits:
            matched_messages.add(m)
            print(f"FAIL  {name}: {c} violation(s) -- {m[:100]}")
    else:
        print(f"PASS  {name}")

unattributed = sum(c for m, c in by_message.items() if m not in matched_messages)
if unattributed:
    print(f"\n[WARN] {unattributed} violations could not be attributed to a named shape -- inspect manually.")
print(f"\nTotal violations: {len(violations)}")
