"""
AIEF — SHACL risk-dimension validation demonstrator
====================================================
Validates structured proposal descriptions against the scrutable risk
rules in aief-risk-shapes.ttl and prints a per-dimension risk profile
for each proposal, instead of a single aggregated High/Medium/Low label.

Every rule's priority (aiefsh:priority) and tier (sh:severity) is data
in the shapes file: an evaluator who disagrees with a ranking edits one
triple and re-runs this script. No LLM is involved in this layer.

Usage:
  python run_shacl.py                # validate the bundled examples
  python run_shacl.py my-data.ttl    # validate your own proposal descriptions
"""

import sys
from collections import defaultdict
from pathlib import Path

import rdflib
from pyshacl import validate

HERE = Path(__file__).parent
SHAPES_FILE = HERE / "aief-risk-shapes.ttl"
DEFAULT_DATA = HERE / "example-proposals.ttl"

SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
AIEFSH = rdflib.Namespace("https://w3id.org/aief/shapes#")
RDFS = rdflib.RDFS

SEVERITY_LABEL = {
    SH.Violation: "VIOLATION",
    SH.Warning: "warning",
    SH.Info: "info",
}


def local(iri):
    s = str(iri)
    return s.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def main():
    data_file = DEFAULT_DATA
    profile_file = None
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--profile" and i + 1 < len(sys.argv):
            profile_file = Path(sys.argv[i + 1])
            i += 2
            continue
        if not sys.argv[i].startswith("--"):
            data_file = Path(sys.argv[i])
        i += 1

    shapes = rdflib.Graph().parse(SHAPES_FILE, format="turtle")
    # after parsing shapes, before validate():
    if profile_file is not None:
        prof = rdflib.Graph().parse(profile_file, format="turtle")
        for s, p, o in prof:
            if p in (AIEFSH.priority, SH.severity):
                shapes.remove((s, p, None))
                shapes.add((s, p, o))
        print(f"Profile applied: {profile_file.name}")

    data = rdflib.Graph().parse(data_file, format="turtle")

    conforms, report_graph, _ = validate(
        data, shacl_graph=shapes, advanced=True, inference="none"
    )

    # index shape metadata: severity, dimension, priority, label
    meta = {}
    for shape in shapes.subjects(rdflib.RDF.type, SH.NodeShape):
        meta[shape] = {
            "severity": shapes.value(shape, SH.severity, default=SH.Violation),
            "dimension": shapes.value(shape, AIEFSH.riskDimension),
            "priority": int(shapes.value(shape, AIEFSH.priority, default=99)),
            "label": str(shapes.value(shape, RDFS.label, default=local(shape))),
        }

    # collect results per focus node
    per_proposal = defaultdict(list)
    for result in report_graph.subjects(rdflib.RDF.type, SH.ValidationResult):
        focus = report_graph.value(result, SH.focusNode)
        source = report_graph.value(result, SH.sourceShape)
        message = str(report_graph.value(result, SH.resultMessage, default=""))
        m = meta.get(source, {})
        per_proposal[focus].append(
            {
                "priority": m.get("priority", 99),
                "severity": SEVERITY_LABEL.get(m.get("severity"), "?"),
                "dimension": local(m.get("dimension", "")) if m.get("dimension") else "?",
                "rule": m.get("label", local(source) if source else "?"),
                "message": message,
            }
        )

    proposals = sorted(
        data.subjects(rdflib.RDF.type, rdflib.URIRef("https://w3id.org/aief/ResearchProposal"))
    )
    print(f"Shapes: {SHAPES_FILE.name} | Data: {data_file.name}")
    print(f"Overall conformance: {conforms}\n")

    for p in proposals:
        label = data.value(p, RDFS.label, default=local(p))
        findings = sorted(per_proposal.get(p, []), key=lambda f: f["priority"])
        print(f"=== {label} ===")
        if not findings:
            print("  No risk-dimension flags. All scrutable rules pass.\n")
            continue
        dims = defaultdict(list)
        for f in findings:
            dims[f["dimension"]].append(f)
        for dim, items in dims.items():
            print(f"  Dimension {dim}: {len(items)} flag(s)")
            for f in items:
                print(f"    [P{f['priority']} {f['severity']}] {f['rule']}")
                print(f"        {f['message']}")
        print()


if __name__ == "__main__":
    main()
