#!/usr/bin/env python3
"""Re-score LLM-8B on all 45 perturbation variants via local Ollama (post-mitigation)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "rag-pipeline"))
sys.path.insert(0, str(ROOT))

import perturbation_generator as pg  # noqa: E402
from sparql_retrieval import set_retrieval_backend  # noqa: E402

VARIANTS = ROOT / "perturbation_variants.json"
CACHE = ROOT / "results" / "perturbation_assessor_cache" / "llama3.1_8b"


def main() -> None:
    set_retrieval_backend("local")
    CACHE.mkdir(parents=True, exist_ok=True)
    # Drop old Groq-8B caches so run_llm does not reuse pre-mitigation labels
    old = ROOT / "results" / "perturbation_assessor_cache" / "llama-3.1-8b-instant"
    if old.exists():
        for f in old.glob("*.json"):
            f.unlink()

    variants = json.loads(VARIANTS.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in pg.PROPOSALS}

    # Refresh 8B baselines from the new full-corpus assessments
    for v in variants:
        pid = v["base_id"]
        bl = dict(v.get("assessor_baselines") or {})
        f = pg.EVAL / "llama-3.1-8b" / f"{pid}_full.json"
        if f.exists():
            a = json.loads(f.read_text()).get("assessment") or {}
            bl["LLM-8B"] = a.get("overall_risk_level")
        v["assessor_baselines"] = bl

    for i, v in enumerate(variants, 1):
        ao = dict(v.get("assessor_outputs") or {})
        text = v["variant_text"]
        vid = v["variant_id"]
        existing = pg._normalize_risk(ao.get("LLM-8B"))
        if existing:
            ao["LLM-8B"] = existing
            v["assessor_outputs"] = ao
            print(f"[{i}/45] {vid} skip (LLM-8B={existing})", flush=True)
            continue
        print(f"[{i}/45] {vid} ...", flush=True)
        risk = pg.run_llm(
            text, vid + "_8b", model="llama3.1:8b", backend="ollama"
        )
        ao["LLM-8B"] = risk
        # Ensure non-LLM assessors still present
        if not ao.get("keyword-baseline"):
            ao["keyword-baseline"] = pg.run_keyword(text)
        if not ao.get("SHACL"):
            ao["SHACL"] = pg.run_shacl(text)
        v["assessor_outputs"] = ao
        print(f"  → {ao}", flush=True)
        VARIANTS.write_text(json.dumps(variants, indent=2), encoding="utf-8")

    report = pg.score(variants)
    print(json.dumps(report["sensitivity_rates"], indent=2))
    print("DONE", pg.REPORT_PATH)


if __name__ == "__main__":
    main()
