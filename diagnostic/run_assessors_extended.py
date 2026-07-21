"""
run_assessors_extended.py
Run LLM assessors (8B / 70B via Groq) over the full 40-proposal diagnostic corpus.

Writes P##_full.json into evaluation/results/{llama-3.1-8b|llama-3.3-70b}/,
reusing existing files unless --force is set.

Requires GraphDB (SPARQL) + GROQ_API_KEY.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOL = ROOT.parent
RAG = TOOL / "rag-pipeline"
EVAL = TOOL / "evaluation" / "results"

sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

from synthetic_proposals_extended import PROPOSALS  # noqa: E402
from ethics_rag import assess_proposal  # noqa: E402
from llm_caller import test_groq_connection  # noqa: E402
from sparql_retrieval import test_connection as test_sparql  # noqa: E402

MODELS = {
    # Both via Groq; keep max_requirements≤12 so 8B stays under free-tier TPM.
    "8b": ("groq", "llama-3.1-8b-instant", EVAL / "llama-3.1-8b"),
    "70b": ("groq", "llama-3.3-70b-versatile", EVAL / "llama-3.3-70b"),
}


def run_model(
    key: str,
    force: bool,
    sleep_s: float,
    only: list[str] | None,
    max_requirements: int,
) -> None:
    backend, model, out_dir = MODELS[key]
    out_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"\n=== Assessor {key} backend={backend} model={model} "
        f"max_req={max_requirements} → {out_dir} ==="
    )
    if backend == "groq":
        if not test_groq_connection(model):
            raise SystemExit(f"Groq unavailable for {model}")
    else:
        from llm_caller import test_connection as test_ollama

        if not test_ollama(model):
            raise SystemExit(f"Ollama unavailable for {model}")

    selected = [p for p in PROPOSALS if only is None or p["id"] in only]
    done = skipped = failed = 0
    for i, p in enumerate(selected, 1):
        out = out_dir / f"{p['id']}_full.json"
        if out.exists() and not force:
            try:
                data = json.loads(out.read_text(encoding="utf-8"))
                a = data.get("assessment") or {}
                if isinstance(a, dict) and a.get("overall_risk_level"):
                    print(f"[{i}/{len(selected)}] {p['id']} skip (exists)")
                    skipped += 1
                    continue
            except Exception:
                pass

        print(f"[{i}/{len(selected)}] {p['id']} {p['title'][:50]} ...", flush=True)
        result = assess_proposal(
            proposal=p["proposal_text"],
            proposal_id=p["id"],
            mode="full",
            backend=backend,
            model=model,
            max_requirements=max_requirements,
            output_dir=str(out_dir),
        )
        assessment = result.get("assessment") or {}
        if "parse_error" in assessment or not assessment.get("overall_risk_level"):
            print(f"  FAIL/parse: {assessment.get('parse_error') or 'no risk level'}")
            failed += 1
        else:
            print(
                f"  OK risk={assessment.get('overall_risk_level')} "
                f"rights={len(assessment.get('charter_rights_at_risk') or [])}"
            )
            done += 1
        if backend == "groq" and i < len(selected):
            time.sleep(sleep_s)

    print(f"Done {key}: new={done} skipped={skipped} failed={failed}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="8b,70b", help="Comma list: 8b,70b")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--sleep", type=float, default=2.0)
    parser.add_argument("--only", nargs="*", default=None, help="Optional proposal IDs")
    parser.add_argument(
        "--max-requirements",
        type=int,
        default=12,
        help="Cap KG requirements in prompt (smaller = fits Groq TPM).",
    )
    args = parser.parse_args()

    if not test_sparql():
        raise SystemExit("GraphDB/SPARQL not reachable — start GraphDB first.")

    for key in [k.strip() for k in args.models.split(",") if k.strip()]:
        if key not in MODELS:
            raise SystemExit(f"Unknown model key {key}")
        run_model(
            key,
            force=args.force,
            sleep_s=args.sleep,
            only=args.only,
            max_requirements=args.max_requirements,
        )


if __name__ == "__main__":
    main()
