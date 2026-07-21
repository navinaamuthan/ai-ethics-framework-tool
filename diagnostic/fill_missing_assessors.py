"""Fill missing assessor outputs for P21–P40 (and any gaps)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "rag-pipeline"))
sys.path.insert(0, str(ROOT))

from ethics_rag import assess_proposal
from llm_caller import test_connection, test_groq_connection
from sparql_retrieval import test_connection as test_sparql
from synthetic_proposals_extended import PROPOSALS

EVAL = ROOT.parent / "evaluation" / "results"


def has_risk(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        a = json.loads(path.read_text(encoding="utf-8")).get("assessment") or {}
        return isinstance(a, dict) and bool(a.get("overall_risk_level"))
    except Exception:
        return False


def missing(out_dir: Path) -> list[dict]:
    return [p for p in PROPOSALS if not has_risk(out_dir / f"{p['id']}_full.json")]


def run_batch(label, backend, model, out_dir: Path, max_req: int, sleep_s: float):
    out_dir.mkdir(parents=True, exist_ok=True)
    need = missing(out_dir)
    print(f"\n=== {label}: need {len(need)} → {[p['id'] for p in need]}", flush=True)
    if not need:
        return
    if backend == "groq":
        assert test_groq_connection(model)
    else:
        assert test_connection(model)

    for i, p in enumerate(need, 1):
        print(f"[{i}/{len(need)}] {p['id']} {p['title'][:45]}", flush=True)
        ok = False
        for attempt in range(1, 5):
            result = assess_proposal(
                proposal=p["proposal_text"],
                proposal_id=p["id"],
                mode="full",
                backend=backend,
                model=model,
                max_requirements=max_req,
                output_dir=str(out_dir),
            )
            a = result.get("assessment") or {}
            if isinstance(a, dict) and a.get("overall_risk_level"):
                print(
                    f"  OK risk={a['overall_risk_level']} "
                    f"rights={len(a.get('charter_rights_at_risk') or [])}",
                    flush=True,
                )
                ok = True
                break
            wait = 60 * attempt
            print(f"  attempt {attempt} failed — sleep {wait}s", flush=True)
            time.sleep(wait)
        if not ok:
            print(f"  GIVE UP {p['id']}", flush=True)
        elif backend == "groq":
            time.sleep(sleep_s)
    print(f"=== {label} remaining: {[p['id'] for p in missing(out_dir)]}", flush=True)


def main():
    assert test_sparql()
    # 8B gaps via Ollama (reliable; no Groq TPM).
    run_batch(
        "LLM-8B/ollama",
        "ollama",
        "llama3.1:8b",
        EVAL / "llama-3.1-8b",
        max_req=12,
        sleep_s=0,
    )
    # 70B via Groq with small context to stay under TPM/TPD.
    run_batch(
        "LLM-70B/groq",
        "groq",
        "llama-3.3-70b-versatile",
        EVAL / "llama-3.3-70b",
        max_req=5,
        sleep_s=3,
    )


if __name__ == "__main__":
    main()
