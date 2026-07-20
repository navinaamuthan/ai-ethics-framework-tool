#!/usr/bin/env python3
"""
Compute global document frequency for every RiskCategory subclass.

Counts assertions of :hasRisk (Requirements) and :demonstratesRisk (Incidents)
combined, then writes ontology/risk_category_doc_frequency.json.

Regenerate only after ontology risk-category assertions change
(e.g. after a Phase-0-style edit) — not on every pipeline run.

Usage:
  python ontology/compute_risk_category_idf.py
  python ontology/compute_risk_category_idf.py --backend local
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "rag-pipeline"))

from sparql_retrieval import set_retrieval_backend, sparql_query  # noqa: E402

OUT = Path(__file__).resolve().parent / "risk_category_doc_frequency.json"

# Round-2 hasRisk-only audit (pre-incident merge). Combined counts will be
# ≥ these for high-volume categories; Transparency is hasRisk-only so exact.
_REGRESSION = {
    "Transparency": 5,       # exact — no demonstratesRisk uses this class
    "Accountability": 90,    # hasRisk floor; incidents may add more
    "PrivacyBreach": 60,
    "Discrimination": 21,
}


def fetch_category_names() -> list[str]:
    rows = sparql_query("""
    SELECT DISTINCT ?catLocal WHERE {
        ?cat rdfs:subClassOf :RiskCategory .
        BIND(STRAFTER(STR(?cat), "/aief/") AS ?catLocal)
        FILTER(BOUND(?catLocal) && STRLEN(?catLocal) > 0)
    }
    ORDER BY ?catLocal
    """)
    names = []
    for r in rows:
        name = r.get("catLocal", {}).get("value", "")
        if name and name not in names:
            names.append(name)
    return names


def count_assertions(category: str) -> int:
    """Count :hasRisk + :demonstratesRisk triples targeting this category."""
    query = f"""
    SELECT (COUNT(*) AS ?n) WHERE {{
        {{ ?s :hasRisk :{category} }}
        UNION
        {{ ?s :demonstratesRisk :{category} }}
    }}
    """
    rows = sparql_query(query)
    if not rows:
        return 0
    return int(rows[0].get("n", {}).get("value", "0"))


def main(backend: str = "auto") -> None:
    set_retrieval_backend(backend)
    cats = fetch_category_names()
    if not cats:
        raise SystemExit("No RiskCategory subclasses found — check KG connection / ontology.")

    freq: dict[str, int] = {}
    for cat in cats:
        freq[cat] = count_assertions(cat)
        print(f"  {cat}: {freq[cat]}")

    # Regression checks
    print("\n=== Regression checks (Round 2 audit) ===")
    ok = True
    if "Transparency" not in freq or freq["Transparency"] != _REGRESSION["Transparency"]:
        print(f"  FAIL Transparency: got {freq.get('Transparency')} expected {_REGRESSION['Transparency']}")
        ok = False
    else:
        print(f"  OK Transparency={freq['Transparency']}")

    for cat, floor in (("Accountability", 90), ("PrivacyBreach", 60), ("Discrimination", 21)):
        got = freq.get(cat, 0)
        # Combined count must be ≥ hasRisk-only Round-2 floor
        if got < floor:
            print(f"  FAIL {cat}: got {got} < floor {floor}")
            ok = False
        else:
            print(f"  OK {cat}={got} (≥ {floor} hasRisk floor)")

    n = len(freq)
    print(f"\n  Categories written: {n}")
    if n < 27:
        print(f"  FAIL expected ≥27 RiskCategory subclasses, got {n}")
        ok = False
    else:
        print(f"  OK ≥27 categories present")

    OUT.write_text(json.dumps(freq, indent=2, sort_keys=True) + "\n")
    print(f"\nWrote {OUT}")
    if not ok:
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="local", choices=["auto", "local", "graphdb"])
    args = ap.parse_args()
    main(backend=args.backend)
