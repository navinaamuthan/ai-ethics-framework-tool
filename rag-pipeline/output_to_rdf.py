#!/usr/bin/env python3
"""
Task 2.1 — Lift an AIEF assessment JSON object into RDF so the Week-2
consistency shapes (shacl/aief-consistency-shapes.ttl) can validate it.

Emits one blank/named node per identified_risk, linked via:
  :assessmentRiskCategory
  :assessmentCitesRequirement
  :assessmentHasMitigation

Because the assessment schema keeps requirements and mitigations at the
assessment level (not nested under each risk), every risk node receives
the full set of cited requirements and recommended mitigations. That is
intentional: the shapes then check assessment-level completeness and
category/mitigation coherence projected onto each stated risk.

Usage:
  python rag-pipeline/output_to_rdf.py path/to/P01_full.json -o /tmp/P01_assessment.ttl
  python -c "from output_to_rdf import assessment_to_graph; ..."
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, BNode
from rdflib.namespace import XSD

# Allow importing the rule table whether run from rag-pipeline/ or repo root
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO / "ontology") not in sys.path:
    sys.path.insert(0, str(_REPO / "ontology"))
from risk_to_mitigation_table import RISK_TO_MITIGATION  # noqa: E402

AIEF = Namespace("https://w3id.org/aief/")
AIEFSH = Namespace("https://w3id.org/aief/shapes#")

# Known mitigation class local names (from the rule table values)
MITIGATION_IDS = sorted(
    {m.lstrip(":") for mits in RISK_TO_MITIGATION.values() for m in mits}
)
RISK_CATEGORY_IDS = sorted(RISK_TO_MITIGATION.keys())

# Light keyword hints for resolving free-text mitigations in pre-Week-1 outputs
_MITIGATION_HINTS: list[tuple[str, str]] = [
    ("encrypt", "Encryption"),
    ("pseudonym", "Pseudonymisation"),
    ("anonym", "Anonymisation"),
    ("access control", "AccessControl"),
    ("audit log", "AuditLog"),
    ("audit", "AuditLog"),
    ("staff training", "StaffTraining"),
    ("training", "StaffTraining"),
    ("governance", "GovernanceProcedure"),
    ("complaint", "ComplaintMechanism"),
    ("appeal", "ComplaintMechanism"),
    ("incident response", "IncidentResponsePlan"),
    ("ethics review", "EthicsReviewBoard"),
    ("ethics board", "EthicsReviewBoard"),
    ("human oversight", "HumanOversight"),
    ("oversight", "HumanOversight"),
    ("responsible release", "ResponsibleReleasePolicy"),
    ("release policy", "ResponsibleReleasePolicy"),
    ("environmental safeguard", "EnvironmentalSafeguard"),
    ("environmental", "EnvironmentalSafeguard"),
]


def _local_iri(name: str) -> URIRef:
    # Requirement IDs occasionally contain spaces (e.g. "EUAIAct AI008");
    # sanitise so the URI is legal without changing the human-facing id elsewhere.
    safe = re.sub(r"[^\w\-.:]", "_", str(name).strip())
    return AIEF[safe]


def resolve_mitigation_id(entry: dict | str) -> str | None:
    """Map a recommended_mitigations entry to a taxonomy class local name, if possible."""
    if isinstance(entry, str):
        text = entry
        mid = None
        from_tax = None
    else:
        text = str(entry.get("mitigation") or entry.get("mitigation_id") or "")
        mid = entry.get("mitigation_id") or entry.get("id")
        from_tax = entry.get("from_taxonomy")

    if mid:
        # Normalise "Human Oversight" / "human-oversight" → try CamelCase match
        compact = re.sub(r"[^A-Za-z0-9]", "", str(mid))
        for known in MITIGATION_IDS:
            if mid == known or compact.lower() == known.lower():
                return known

    # Exact CamelCase / id token in the text
    for known in MITIGATION_IDS:
        if re.search(rf"\b{re.escape(known)}\b", text):
            return known

    lower = text.lower()
    for hint, known in _MITIGATION_HINTS:
        if hint in lower:
            return known

    # Explicitly non-taxonomy alternatives stay unresolved (None)
    if from_tax is False:
        return None
    return None


def resolve_risk_category(risk_entry: dict) -> str | None:
    cat = risk_entry.get("risk_category") or risk_entry.get("category")
    if cat:
        cat = str(cat).lstrip(":").strip()
        if cat in RISK_CATEGORY_IDS:
            return cat
    # Fallback: look for a known category token in the risk / explanation text
    blob = " ".join(
        str(risk_entry.get(k) or "")
        for k in ("risk", "risk_category", "explanation", "severity")
    )
    for known in RISK_CATEGORY_IDS:
        if re.search(rf"\b{re.escape(known)}\b", blob):
            return known
    return None


def typically_mitigated_by_triples(g: Graph) -> None:
    """Materialise the Task 1.1 rule table as :typicallyMitigatedBy triples."""
    g.add((AIEF.typicallyMitigatedBy, RDF.type, AIEF.ObjectProperty))
    g.add((AIEF.typicallyMitigatedBy, RDFS.label, Literal("typically mitigated by")))
    for cat, mits in RISK_TO_MITIGATION.items():
        for m in mits:
            g.add((_local_iri(cat), AIEF.typicallyMitigatedBy, _local_iri(m.lstrip(":"))))


def assessment_to_graph(
    assessment_doc: dict,
    include_rule_table: bool = True,
) -> Graph:
    """
    Convert a full pipeline output JSON (or a bare assessment dict) into RDF.

    Accepts either:
      {"assessment": {...}, "proposal_id": "P01", ...}
    or the inner assessment object itself.
    """
    g = Graph()
    g.bind("aief", AIEF)
    g.bind("aiefsh", AIEFSH)
    g.bind("rdfs", RDFS)

    if include_rule_table:
        typically_mitigated_by_triples(g)

    # Unwrap pipeline envelope if present
    if "assessment" in assessment_doc and isinstance(assessment_doc["assessment"], dict):
        meta = assessment_doc
        assessment = assessment_doc["assessment"]
    else:
        meta = {}
        assessment = assessment_doc

    pid = meta.get("proposal_id") or assessment.get("proposal_id") or "unknown"
    assessment_uri = AIEF[f"Assessment_{pid}"]
    g.add((assessment_uri, RDF.type, AIEF.EthicsAssessment))
    g.add((assessment_uri, AIEF.proposalID, Literal(str(pid))))
    level = assessment.get("overall_risk_level")
    if level:
        g.add((assessment_uri, AIEF.overallRiskLevel, Literal(str(level))))

    # Collect assessment-level citations / mitigations once
    req_ids: list[str] = []
    for req in assessment.get("applicable_requirements") or []:
        rid = (req.get("requirement_id") or req.get("id") or "").strip()
        if rid and rid not in req_ids:
            req_ids.append(rid)

    mit_ids: list[str] = []
    unresolved_mits: list[str] = []
    for m in assessment.get("recommended_mitigations") or []:
        resolved = resolve_mitigation_id(m)
        if resolved:
            if resolved not in mit_ids:
                mit_ids.append(resolved)
        else:
            text = m if isinstance(m, str) else str(m.get("mitigation") or "")
            if text:
                unresolved_mits.append(text)

    risks = assessment.get("identified_risks") or []
    for idx, risk_entry in enumerate(risks):
        risk_uri = AIEF[f"IdentifiedRisk_{pid}_{idx + 1}"]
        g.add((risk_uri, RDF.type, AIEF.IdentifiedRisk))
        g.add((assessment_uri, AIEF.hasIdentifiedRisk, risk_uri))
        g.add((risk_uri, RDFS.label, Literal(str(risk_entry.get("risk") or f"risk-{idx+1}"))))
        sev = risk_entry.get("severity")
        if sev:
            g.add((risk_uri, AIEF.severity, Literal(str(sev))))

        cat = resolve_risk_category(risk_entry)
        if cat:
            g.add((risk_uri, AIEF.assessmentRiskCategory, _local_iri(cat)))

        for rid in req_ids:
            g.add((risk_uri, AIEF.assessmentCitesRequirement, _local_iri(rid)))

        for mid in mit_ids:
            g.add((risk_uri, AIEF.assessmentHasMitigation, _local_iri(mid)))

        # Unresolved free-text mitigations: attach as literals so RiskHasMitigationShape
        # can still see *a* mitigation, while MitigationCategoryMatchShape (which
        # compares IRIs via typicallyMitigatedBy) will fail if nothing taxonomy-linked
        # matched the category.
        for i, text in enumerate(unresolved_mits):
            lit_node = BNode(f"free_mit_{pid}_{idx}_{i}")
            g.add((lit_node, RDF.type, AIEF.FreeTextMitigation))
            g.add((lit_node, RDFS.label, Literal(text)))
            g.add((risk_uri, AIEF.assessmentHasMitigation, lit_node))

    return g


def graph_to_turtle(g: Graph) -> str:
    return g.serialize(format="turtle")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path, help="Assessment JSON path")
    parser.add_argument("-o", "--output", type=Path, help="Write Turtle here")
    parser.add_argument(
        "--no-rule-table",
        action="store_true",
        help="Omit :typicallyMitigatedBy triples (shapes that need them will fail closed)",
    )
    args = parser.parse_args()

    doc = json.loads(args.json_path.read_text(encoding="utf-8"))
    g = assessment_to_graph(doc, include_rule_table=not args.no_rule_table)
    ttl = graph_to_turtle(g)
    if args.output:
        args.output.write_text(ttl, encoding="utf-8")
        print(f"Wrote {args.output} ({len(g)} triples)")
    else:
        print(ttl)


if __name__ == "__main__":
    main()
