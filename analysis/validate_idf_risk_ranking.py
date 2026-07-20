#!/usr/bin/env python3
"""
Validate IDF-weighted risk-category ranking against the allowlist baseline.

Runs retrieve_all_for_proposal() for all 20 synthetic proposals (no LLM) and
checks that Transparency still surfaces on ≥18/20 proposals, that P15/P20
correctly exclude it, and that at least one previously-unnamed rare category
now appears somewhere sensible.

Usage:
  python analysis/validate_idf_risk_ranking.py
  python analysis/validate_idf_risk_ranking.py --backend local
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "rag-pipeline"))

from synthetic_proposals import PROPOSALS  # noqa: E402
from sparql_retrieval import (  # noqa: E402
    _DOC_FREQ,
    retrieve_all_for_proposal,
    set_retrieval_backend,
)

# Categories the allowlist hardcoded — IDF must match/beat on Transparency.
ALLOWLIST_CATS = {"Transparency", "EnvironmentalHarm", "ChildrenRights"}
# Rare categories the allowlist never named — evidence IDF generalises.
RARE_UNNAMED = {
    "Surveillance",
    "DemocraticProcessHarm",
    "DualUseMisuse",
    "FalseIdentification",
    "AddictionRisk",
    "FunctionCreep",
    "Manipulation",
}


def main(backend: str = "local") -> None:
    set_retrieval_backend(backend)
    print(f"IDF table: {len(_DOC_FREQ)} categories, Transparency df={_DOC_FREQ.get('Transparency')}")
    print("=" * 72)

    transparency_hits = []
    rare_hits = []  # (pid, category)
    rows = []

    for p in PROPOSALS:
        pid = p["id"]
        _reqs, _incs, _rights, _kws, risk_cats = retrieve_all_for_proposal(p["proposal_text"])
        top = [c["id"] for c in risk_cats]
        scores = {c["id"]: c.get("idf_score") for c in risk_cats}
        has_t = "Transparency" in top
        if has_t:
            transparency_hits.append(pid)

        unnamed_here = [c for c in top if c in RARE_UNNAMED]
        for c in unnamed_here:
            rare_hits.append((pid, c))

        rows.append({"id": pid, "top": top, "transparency": has_t, "rare": unnamed_here, "scores": scores})
        flag = "T" if has_t else "-"
        print(f"{pid} [{flag}] {', '.join(top)}")

    print("=" * 72)
    n_t = len(transparency_hits)
    print(f"Transparency in top-10: {n_t}/20  → {transparency_hits}")

    p15 = next(r for r in rows if r["id"] == "P15")
    p20 = next(r for r in rows if r["id"] == "P20")
    print(f"P15 excludes Transparency: {not p15['transparency']}  (top={p15['top']})")
    print(f"P20 excludes Transparency: {not p20['transparency']}  (top={p20['top']})")

    # Generalisation: at least one rare unnamed category in some proposal's top-10
    rare_unique = sorted({c for _, c in rare_hits})
    print(f"Previously-unnamed rare cats surfaced: {rare_unique or '(none)'}")
    if rare_hits:
        examples = rare_hits[:8]
        print(f"  examples: {examples}")

    ok = True
    if n_t < 18:
        print(f"FAIL: Transparency coverage {n_t}/20 < 18")
        ok = False
    else:
        print(f"PASS: Transparency coverage {n_t}/20 ≥ 18")

    if p15["transparency"] or p20["transparency"]:
        print("FAIL: P15 and/or P20 incorrectly include Transparency")
        ok = False
    else:
        print("PASS: P15/P20 correctly exclude Transparency")

    if not rare_unique:
        print("FAIL: no previously-unnamed rare category surfaced")
        ok = False
    else:
        print(f"PASS: IDF generalises beyond allowlist ({', '.join(rare_unique)})")

    out = Path(__file__).parent / "results" / "idf_risk_ranking_validation.json"
    out.parent.mkdir(exist_ok=True)
    json.dump(
        {
            "transparency_count": n_t,
            "transparency_proposals": transparency_hits,
            "p15_excludes": not p15["transparency"],
            "p20_excludes": not p20["transparency"],
            "rare_unnamed_surfaced": rare_unique,
            "per_proposal": rows,
            "pass": ok,
        },
        open(out, "w"),
        indent=2,
    )
    print(f"\nWrote {out}")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="local", choices=["auto", "local", "graphdb"])
    args = ap.parse_args()
    main(backend=args.backend)
