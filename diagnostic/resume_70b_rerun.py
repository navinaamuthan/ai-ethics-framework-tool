#!/usr/bin/env python3
"""Resume post-wiring LLM-70B full-RAG re-run for proposals still on pre-wiring outputs.

Waits out Groq TPD 429s instead of falling back to compact/risk-only prompts.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOL = ROOT.parent
RAG = TOOL / "rag-pipeline"
OUT = TOOL / "evaluation" / "results" / "llama-3.3-70b"

sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

from ethics_rag import assess_proposal  # noqa: E402
from llm_caller import test_groq_connection  # noqa: E402
from sparql_retrieval import set_retrieval_backend, test_connection as test_sparql  # noqa: E402
from synthetic_proposals_extended import PROPOSALS  # noqa: E402

MODEL = "llama-3.3-70b-versatile"
MAX_REQ = 25
SLEEP_S = 15


def is_new_wired(path: Path) -> bool:
    if not path.exists():
        return False
    d = json.loads(path.read_text(encoding="utf-8"))
    a = d.get("assessment") or {}
    if not isinstance(a, dict) or not a.get("overall_risk_level"):
        return False
    if d.get("mode") != "full" or d.get("compact_prompt"):
        return False
    if d.get("context_max_requirements") != MAX_REQ:
        return False
    if d.get("llm_backend") != "groq" or d.get("llm_model") != MODEL:
        return False
    mits = a.get("recommended_mitigations") or []
    return any(m.get("from_taxonomy") for m in mits if isinstance(m, dict))


def wait_from_error(msg: str) -> int:
    m = re.search(r"try again in (\d+)m([\d.]+)s", msg)
    if m:
        return int(m.group(1)) * 60 + int(float(m.group(2))) + 30
    m = re.search(r"try again in ([\d.]+)s", msg)
    if m:
        return int(float(m.group(1))) + 30
    return 35 * 60


def main() -> None:
    set_retrieval_backend("local")
    assert test_sparql()
    assert test_groq_connection(MODEL)

    targets = [p for p in PROPOSALS if not is_new_wired(OUT / f"{p['id']}_full.json")]
    print(f"Remaining: {len(targets)} / 40", flush=True)
    for i, p in enumerate(targets, 1):
        dest = OUT / f"{p['id']}_full.json"
        print(f"[{i}/{len(targets)}] {p['id']} full RAG (max_req={MAX_REQ})...", flush=True)
        while True:
            result = assess_proposal(
                proposal=p["proposal_text"],
                proposal_id=p["id"],
                mode="full",
                backend="groq",
                model=MODEL,
                max_requirements=MAX_REQ,
                output_dir=str(OUT),
            )
            a = result.get("assessment") or {}
            if isinstance(a, dict) and a.get("overall_risk_level") and "error" not in a:
                if is_new_wired(dest):
                    print(
                        f"  OK risk={a['overall_risk_level']} "
                        f"rights={len(a.get('charter_rights_at_risk') or [])}",
                        flush=True,
                    )
                    break
                print("  WARN: saved but not taxonomy-wired; retrying once...", flush=True)
            # Outer backoff when call_groq exhausted its internal TPD waits.
            wait = 70 * 60
            print(f"  FAIL — sleeping {wait}s then retry full assess", flush=True)
            time.sleep(wait)
        if i < len(targets):
            time.sleep(SLEEP_S)

    remaining = [p["id"] for p in PROPOSALS if not is_new_wired(OUT / f"{p['id']}_full.json")]
    print(f"DONE remaining_unwired={len(remaining)} {remaining}", flush=True)
    if remaining:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
