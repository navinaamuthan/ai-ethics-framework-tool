#!/usr/bin/env python3
"""
Task 2.3 — Run the Week-2 consistency shapes over assessment outputs.

Reports, per configuration directory, the fraction of identified risks that:
  - cite ≥1 requirement
  - have ≥1 mitigation
  - have a mitigation whose class matches the risk category (rule table)

Usage:
  python shacl/run_consistency_check.py
  python shacl/run_consistency_check.py --dirs evaluation/results/llama-3.1-8b evaluation/results/llama-3.3-70b
  python shacl/run_consistency_check.py --self-test   # deliberate mismatch must fire
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import rdflib
from pyshacl import validate

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SHAPES_FILE = HERE / "aief-consistency-shapes.ttl"
DEFAULT_DIRS = [
    REPO / "evaluation" / "results" / "llama-3.1-8b",
    REPO / "evaluation" / "results" / "llama-3.3-70b",
    REPO / "evaluation" / "results" / "qwen3-32b-exploratory",
]

sys.path.insert(0, str(REPO / "rag-pipeline"))
sys.path.insert(0, str(REPO / "ontology"))
from output_to_rdf import assessment_to_graph  # noqa: E402

AIEF = rdflib.Namespace("https://w3id.org/aief/")
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
AIEFSH = rdflib.Namespace("https://w3id.org/aief/shapes#")

SHAPE_KEYS = {
    str(AIEFSH.RiskHasRequirementShape): "has_requirement",
    str(AIEFSH.RiskHasMitigationShape): "has_mitigation",
    str(AIEFSH.MitigationCategoryMatchShape): "mitigation_category_match",
}


def _local(iri) -> str:
    s = str(iri)
    return s.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def validate_assessment(doc: dict, shapes: rdflib.Graph) -> dict:
    """Validate one assessment; return per-risk pass/fail for the three shapes."""
    data = assessment_to_graph(doc, include_rule_table=True)
    risk_nodes = list(data.subjects(rdflib.RDF.type, AIEF.IdentifiedRisk))
    n_risks = len(risk_nodes)
    risks_with_category = {
        r for r in risk_nodes if data.value(r, AIEF.assessmentRiskCategory) is not None
    }
    n_with_cat = len(risks_with_category)
    if n_risks == 0:
        return {
            "n_risks": 0,
            "n_risks_with_category": 0,
            "has_requirement": 0,
            "has_mitigation": 0,
            "mitigation_category_match": 0,
            "violations": [],
            "conforms": True,
        }

    conforms, report_graph, _ = validate(
        data, shacl_graph=shapes, advanced=True, inference="none"
    )

    # Start assuming all pass; mark failures from the report
    failing = {key: set() for key in SHAPE_KEYS.values()}
    violations = []
    for result in report_graph.subjects(rdflib.RDF.type, SH.ValidationResult):
        focus = report_graph.value(result, SH.focusNode)
        source = report_graph.value(result, SH.sourceShape)
        # Property shapes nest under the NodeShape; walk up if needed
        source_str = str(source) if source else ""
        key = SHAPE_KEYS.get(source_str)
        if key is None and source is not None:
            # pyshacl may report the property shape blank node; match by message
            msg = str(report_graph.value(result, SH.resultMessage, default=""))
            if "no supporting requirement" in msg:
                key = "has_requirement"
            elif "no corresponding mitigation" in msg:
                key = "has_mitigation"
            elif "do not match the modelled mitigation" in msg:
                key = "mitigation_category_match"
        if key and focus is not None:
            failing[key].add(focus)
        violations.append(
            {
                "focus": _local(focus) if focus else "?",
                "shape": key or (_local(source) if source else "?"),
                "message": str(report_graph.value(result, SH.resultMessage, default="")),
            }
        )

    out = {
        "n_risks": n_risks,
        "n_risks_with_category": n_with_cat,
        "conforms": bool(conforms),
        "violations": violations,
        "has_requirement": n_risks - len(failing["has_requirement"]),
        "has_mitigation": n_risks - len(failing["has_mitigation"]),
        # Category-match denominator is risks that actually state a category
        "mitigation_category_match": n_with_cat
        - len(failing["mitigation_category_match"] & risks_with_category),
    }
    out["has_requirement_frac"] = out["has_requirement"] / n_risks
    out["has_mitigation_frac"] = out["has_mitigation"] / n_risks
    out["mitigation_category_match_frac"] = (
        out["mitigation_category_match"] / n_with_cat if n_with_cat else None
    )
    return out


def iter_assessment_jsons(directory: Path):
    for path in sorted(directory.glob("P*_full.json")):
        # Skip known failure / ablation artefacts
        if "FAILED" in path.name or "ablation" in path.name:
            continue
        yield path


def summarise_dir(directory: Path, shapes: rdflib.Graph) -> dict:
    totals = defaultdict(float)
    n_files = 0
    n_risks = 0
    n_with_cat = 0
    per_file = []
    for path in iter_assessment_jsons(directory):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        assessment = doc.get("assessment") or doc
        if not isinstance(assessment, dict):
            continue
        if assessment.get("error") or assessment.get("parse_error"):
            continue
        if "identified_risks" not in assessment:
            continue
        result = validate_assessment(doc, shapes)
        n_files += 1
        n_risks += result["n_risks"]
        n_with_cat += result["n_risks_with_category"]
        for key in ("has_requirement", "has_mitigation", "mitigation_category_match"):
            totals[key] += result[key]
        per_file.append({"file": path.name, **{k: v for k, v in result.items() if k != "violations"}})

    summary = {
        "directory": str(directory),
        "config": directory.name,
        "n_files": n_files,
        "n_risks": n_risks,
        "n_risks_with_category": n_with_cat,
        "has_requirement_frac": (totals["has_requirement"] / n_risks) if n_risks else None,
        "has_mitigation_frac": (totals["has_mitigation"] / n_risks) if n_risks else None,
        "mitigation_category_match_frac": (
            totals["mitigation_category_match"] / n_with_cat if n_with_cat else None
        ),
        "per_file": per_file,
    }
    return summary


def self_test(shapes: rdflib.Graph) -> None:
    """Deliberate broken case: PrivacyBreach mitigated only by StaffTraining."""
    broken = {
        "proposal_id": "TEST_MISMATCH",
        "assessment": {
            "overall_risk_level": "High",
            "identified_risks": [
                {
                    "risk": "Personal data leaked without protection",
                    "risk_category": "PrivacyBreach",
                    "severity": "High",
                    "explanation": "No technical data-protection measures.",
                }
            ],
            "applicable_requirements": [
                {
                    "requirement_id": "R071",
                    "requirement_text": "Describe security measures",
                    "framework": "REAMS",
                    "tier": "Tier 1 Mandatory",
                    "action_needed": "Add encryption",
                }
            ],
            "recommended_mitigations": [
                {
                    "mitigation": "StaffTraining",
                    "mitigation_id": "StaffTraining",
                    "priority": "High",
                    "from_taxonomy": True,
                }
            ],
        },
    }
    result = validate_assessment(broken, shapes)
    msgs = " ".join(v["message"] for v in result["violations"])
    assert result["n_risks"] == 1
    assert result["has_requirement"] == 1, "requirement citation should pass"
    assert result["has_mitigation"] == 1, "a mitigation is present (wrong class)"
    assert result["mitigation_category_match"] == 0, (
        "StaffTraining must NOT match PrivacyBreach"
    )
    assert "do not match the modelled mitigation" in msgs
    print("SELF-TEST PASSED: MitigationCategoryMatchShape fired on PrivacyBreach←StaffTraining")

    # Positive control: Encryption should pass
    ok = json.loads(json.dumps(broken))
    ok["assessment"]["recommended_mitigations"] = [
        {
            "mitigation": "Encryption",
            "mitigation_id": "Encryption",
            "priority": "High",
            "from_taxonomy": True,
        }
    ]
    result_ok = validate_assessment(ok, shapes)
    assert result_ok["mitigation_category_match"] == 1
    assert result_ok["conforms"] is True
    print("SELF-TEST PASSED: PrivacyBreach←Encryption conforms")

    # Missing requirement / mitigation shapes
    no_req = {
        "proposal_id": "TEST_NO_REQ",
        "assessment": {
            "identified_risks": [
                {"risk": "x", "risk_category": "Discrimination", "severity": "High"}
            ],
            "applicable_requirements": [],
            "recommended_mitigations": [
                {"mitigation_id": "StaffTraining", "mitigation": "StaffTraining"}
            ],
        },
    }
    r = validate_assessment(no_req, shapes)
    assert r["has_requirement"] == 0
    print("SELF-TEST PASSED: RiskHasRequirementShape fired")

    no_mit = {
        "proposal_id": "TEST_NO_MIT",
        "assessment": {
            "identified_risks": [
                {"risk": "x", "risk_category": "Discrimination", "severity": "High"}
            ],
            "applicable_requirements": [{"requirement_id": "R085"}],
            "recommended_mitigations": [],
        },
    }
    r = validate_assessment(no_mit, shapes)
    assert r["has_mitigation"] == 0
    print("SELF-TEST PASSED: RiskHasMitigationShape fired")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dirs",
        nargs="*",
        type=Path,
        default=None,
        help="Assessment result directories (default: common evaluation/results/*)",
    )
    parser.add_argument("--self-test", action="store_true", help="Run deliberate mismatch tests")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=HERE / "consistency_check_report.json",
        help="Write JSON report here",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max files per dir (smoke)")
    args = parser.parse_args()

    shapes = rdflib.Graph().parse(SHAPES_FILE, format="turtle")
    print(f"Loaded shapes: {SHAPES_FILE.name} ({len(shapes)} triples)")

    if args.self_test:
        self_test(shapes)

    dirs = args.dirs if args.dirs is not None else [d for d in DEFAULT_DIRS if d.is_dir()]
    if not dirs:
        print("No assessment directories found.")
        if args.self_test:
            return
        raise SystemExit(1)

    report = {"shapes": str(SHAPES_FILE), "configurations": []}
    print("\nConsistency check (fractions of identified risks):")
    print(f"{'config':<28} {'n':>5} {'has_req':>8} {'has_mit':>8} {'cat_match':>10}")
    for d in dirs:
        if not d.is_dir():
            print(f"  skip missing dir: {d}")
            continue
        summary = summarise_dir(d, shapes)
        if args.limit is not None:
            summary["per_file"] = summary["per_file"][: args.limit]
        report["configurations"].append(summary)

        def fmt(x):
            return f"{100 * x:6.1f}%" if x is not None else "   n/a"

        print(
            f"{summary['config']:<28} {summary['n_risks']:>5} "
            f"{fmt(summary['has_requirement_frac']):>8} "
            f"{fmt(summary['has_mitigation_frac']):>8} "
            f"{fmt(summary['mitigation_category_match_frac']):>10}"
        )

    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
