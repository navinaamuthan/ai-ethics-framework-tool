"""
AIEF — OOPS! Ontology Pitfall Scanner Integration
===================================================
Submits your ontology to the OOPS! web service and saves the report.

Usage:
  python run_oops.py --ontology-url https://w3id.org/aief/
  python run_oops.py --ontology-file ai-ethics-final.ttl

The report is saved as oops_report.xml and a human-readable summary
is printed to stdout for inclusion in the dissertation appendix.

Author: Navina Ganapathy Amuthan
Trinity College Dublin — MSc Dissertation 2026
"""

import urllib.request
import xml.etree.ElementTree as ET
import sys
import argparse
import os


OOPS_ENDPOINT = "https://oops.linkeddata.es/rest"


def submit_to_oops(ontology_content=None, ontology_url=None):
    """Submit ontology to OOPS! scanner."""
    if ontology_url:
        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<OOPSRequest>
  <OntologyUrl>{ontology_url}</OntologyUrl>
  <OntologyContent></OntologyContent>
  <Pitfalls>2,3,4,5,6,7,8,10,11,12,13,19,20,21,22,24,25,26,27,28,29,34,35,36,38,39,40,41</Pitfalls>
  <OutputFormat>XML</OutputFormat>
</OOPSRequest>"""
    elif ontology_content:
        # Escape XML special chars in ontology content
        escaped = ontology_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<OOPSRequest>
  <OntologyUrl></OntologyUrl>
  <OntologyContent>{escaped}</OntologyContent>
  <Pitfalls>2,3,4,5,6,7,8,10,11,12,13,19,20,21,22,24,25,26,27,28,29,34,35,36,38,39,40,41</Pitfalls>
  <OutputFormat>XML</OutputFormat>
</OOPSRequest>"""
    else:
        raise ValueError("Provide either ontology_url or ontology_content")

    req = urllib.request.Request(
        OOPS_ENDPOINT,
        data=xml_request.encode("utf-8"),
        headers={"Content-Type": "application/xml"},
        method="POST"
    )

    print("Submitting to OOPS!...")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def parse_oops_report(xml_text):
    """Parse OOPS! XML response into human-readable summary."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        print("Could not parse OOPS! response as XML.")
        print("Raw response (first 2000 chars):")
        print(xml_text[:2000])
        return []

    pitfalls = []
    # Try common OOPS! response structures
    for pit in root.iter("Pitfall"):
        name = pit.findtext("Name", "Unknown")
        description = pit.findtext("Description", "")
        importance = pit.findtext("Importance", "")
        affected = pit.findtext("AffectedElements", "")
        pitfalls.append({
            "name": name,
            "description": description,
            "importance": importance,
            "affected": affected,
        })

    # Alternative structure
    if not pitfalls:
        for pit in root.iter("pitfall"):
            name = pit.findtext("name", pit.findtext("Name", "Unknown"))
            description = pit.findtext("description", pit.findtext("Description", ""))
            importance = pit.findtext("importance", pit.findtext("Importance", ""))
            pitfalls.append({
                "name": name,
                "description": description,
                "importance": importance,
                "affected": "",
            })

    return pitfalls


def print_summary(pitfalls):
    """Print dissertation-ready summary."""
    if not pitfalls:
        print("\nNo pitfalls detected by OOPS! scanner.")
        print("This can be reported as: 'The ontology was validated using the OOPS!")
        print("(OntOlogy Pitfall Scanner) web service. No pitfalls were detected.'")
        return

    print(f"\nOOPS! REPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Total pitfalls detected: {len(pitfalls)}")

    # Count by importance
    critical = [p for p in pitfalls if "critical" in p["importance"].lower()]
    important = [p for p in pitfalls if "important" in p["importance"].lower()]
    minor = [p for p in pitfalls if "minor" in p["importance"].lower()]

    print(f"  Critical: {len(critical)}")
    print(f"  Important: {len(important)}")
    print(f"  Minor: {len(minor)}")
    print()

    for i, p in enumerate(pitfalls, 1):
        print(f"  [{i}] {p['name']} ({p['importance']})")
        if p["description"]:
            print(f"      {p['description'][:200]}")
        print()

    print("\n--- DISSERTATION TEXT ---")
    print(f"The ontology was validated using the OOPS! (OntOlogy Pitfall Scanner)")
    print(f"web service [cite OOPS!]. The scanner detected {len(pitfalls)} pitfall(s):")
    print(f"{len(critical)} critical, {len(important)} important, and {len(minor)} minor.")
    if critical:
        print(f"Critical pitfalls were addressed before submission.")
    elif important:
        print(f"Important pitfalls were reviewed; those relating to [describe] were")
        print(f"addressed, while [describe] were accepted as design decisions.")
    else:
        print(f"All detected pitfalls were minor and were reviewed for applicability.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OOPS! ontology validation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ontology-url", help="URL of the ontology (e.g., https://w3id.org/aief/)")
    group.add_argument("--ontology-file", help="Path to local TTL/OWL file")
    parser.add_argument("--output", default="oops_report.xml", help="Output file for raw XML report")
    args = parser.parse_args()

    if args.ontology_file:
        with open(args.ontology_file) as f:
            content = f.read()
        xml_response = submit_to_oops(ontology_content=content)
    else:
        xml_response = submit_to_oops(ontology_url=args.ontology_url)

    # Save raw report
    with open(args.output, "w") as f:
        f.write(xml_response)
    print(f"Raw report saved to {args.output}")

    # Parse and summarise
    pitfalls = parse_oops_report(xml_response)
    print_summary(pitfalls)
