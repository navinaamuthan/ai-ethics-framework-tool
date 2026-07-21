"""Fill missing perturbation assessor outputs and write the report."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "rag-pipeline"))
sys.path.insert(0, str(ROOT))

import perturbation_generator as pg

VARIANTS = ROOT / "perturbation_variants.json"
ASSESSORS = ["SHACL", "LLM-8B", "LLM-70B", "keyword-baseline"]


def complete(ao: dict) -> bool:
    return all(ao.get(a) for a in ASSESSORS)


def main() -> None:
    variants = json.loads(VARIANTS.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in pg.PROPOSALS}

    # baselines once
    baselines = {}
    for pid in pg.SELECTED_IDS:
        text = by_id[pid]["proposal_text"]
        baselines[pid] = {
            "keyword-baseline": pg.run_keyword(text),
            "SHACL": pg.run_shacl(text),
        }
        for name, folder, model in [
            ("LLM-8B", "llama-3.1-8b", "llama-3.1-8b-instant"),
            ("LLM-70B", "llama-3.3-70b", "llama-3.3-70b-versatile"),
        ]:
            f = pg.EVAL / folder / f"{pid}_full.json"
            if f.exists():
                a = json.loads(f.read_text()).get("assessment") or {}
                baselines[pid][name] = a.get("overall_risk_level")
            else:
                baselines[pid][name] = pg.run_llm(text, f"{pid}_base", model)

    for i, v in enumerate(variants, 1):
        ao = dict(v.get("assessor_outputs") or {})
        if complete(ao):
            v["assessor_baselines"] = baselines[v["base_id"]]
            print(f"[{i}/45] {v['variant_id']} skip")
            continue
        text = v["variant_text"]
        vid = v["variant_id"]
        if not ao.get("keyword-baseline"):
            ao["keyword-baseline"] = pg.run_keyword(text)
        if not ao.get("SHACL"):
            ao["SHACL"] = pg.run_shacl(text)
        if not ao.get("LLM-8B"):
            ao["LLM-8B"] = pg.run_llm(text, vid + "_8b", "llama-3.1-8b-instant")
            time.sleep(1.0)
        if not ao.get("LLM-70B"):
            # Prefer compact risk-only (cheap tokens); full RAG only if compact fails.
            for attempt in range(1, 8):
                r = pg.run_llm_compact_risk(text, "llama-3.3-70b-versatile")
                if not r and attempt >= 4:
                    r = pg.run_llm(text, vid + "_70b", "llama-3.3-70b-versatile")
                if r:
                    ao["LLM-70B"] = r
                    break
                wait = 45 * attempt
                print(f"  70B fail {vid} attempt {attempt}, sleep {wait}s", flush=True)
                time.sleep(wait)
            time.sleep(1.0)
        v["assessor_outputs"] = ao
        v["assessor_baselines"] = baselines[v["base_id"]]
        print(f"[{i}/45] {vid}: {ao}", flush=True)
        VARIANTS.write_text(json.dumps(variants, indent=2), encoding="utf-8")

    still = [v["variant_id"] for v in variants if not complete(v.get("assessor_outputs") or {})]
    if still:
        print("STILL_MISSING", still)
        raise SystemExit(1)
    report = pg.score(variants)
    print(json.dumps(report["sensitivity_rates"], indent=2))
    print("persona κ", report["persona_inter_rater_kappa_on_direction"])
    print("DONE", pg.REPORT_PATH)


if __name__ == "__main__":
    main()
