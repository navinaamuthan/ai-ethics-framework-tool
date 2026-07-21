"""Resume only the assessor-scoring phase of perturbation_generator."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "rag-pipeline"))
sys.path.insert(0, str(ROOT))

import perturbation_generator as pg

VARIANTS = ROOT / "perturbation_variants.json"


def main() -> None:
    variants = json.loads(VARIANTS.read_text(encoding="utf-8"))
    assert len(variants) == 45

    incomplete_persona = [v for v in variants if len(v.get("persona_predictions") or {}) < 4]
    if incomplete_persona:
        print(f"Finishing persona prelabel for {len(incomplete_persona)}...")
        variants = pg.persona_prelabel(variants)

    for v in variants:
        ao = v.get("assessor_outputs") or {}
        if not all(ao.get(a) for a in ["SHACL", "LLM-8B", "LLM-70B", "keyword-baseline"]):
            v.pop("assessor_outputs", None)
    VARIANTS.write_text(json.dumps(variants, indent=2), encoding="utf-8")

    print("Assessing variants...")
    variants = pg.assess_variants(variants)
    report = pg.score(variants)
    print(json.dumps(report["sensitivity_rates"], indent=2))
    print("persona κ", report["persona_inter_rater_kappa_on_direction"])
    print("DONE", pg.REPORT_PATH)


if __name__ == "__main__":
    main()
