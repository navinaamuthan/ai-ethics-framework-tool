"""Re-run LLM-70B P21–P40 through full RAG (overwrite compact/llm_only outputs)."""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "rag-pipeline"))
sys.path.insert(0, str(ROOT))

from ethics_rag import assess_proposal
from sparql_retrieval import test_connection as test_sparql
from llm_caller import test_groq_connection
from synthetic_proposals_extended import PROPOSALS

OUT = ROOT.parent / "evaluation" / "results" / "llama-3.3-70b"
BACKUP = OUT / "compact_backups"
MODEL = "llama-3.3-70b-versatile"
MAX_REQ = 10


def needs_rerun(path: Path) -> bool:
    if not path.exists():
        return True
    data = json.loads(path.read_text(encoding="utf-8"))
    mode = data.get("mode") or ""
    if mode in {"compact_diagnostic", "llm_only"} or data.get("compact_prompt"):
        return True
    a = data.get("assessment") or {}
    return not (isinstance(a, dict) and a.get("overall_risk_level"))


def main() -> None:
    assert test_sparql()
    assert test_groq_connection(MODEL)
    BACKUP.mkdir(parents=True, exist_ok=True)
    targets = [p for p in PROPOSALS if int(p["id"][1:]) >= 21]
    for i, p in enumerate(targets, 1):
        dest = OUT / f"{p['id']}_full.json"
        if not needs_rerun(dest) and p["id"] != "P21":
            # P21 already re-run in smoke; skip if full
            data = json.loads(dest.read_text())
            if data.get("mode") == "full" and (data.get("assessment") or {}).get(
                "overall_risk_level"
            ):
                print(f"[{i}/20] {p['id']} skip (already full RAG)")
                continue
        if dest.exists():
            shutil.copy2(dest, BACKUP / f"{p['id']}_full.json")
        print(f"[{i}/20] {p['id']} full RAG...", flush=True)
        ok = False
        for attempt in range(1, 6):
            r = assess_proposal(
                p["proposal_text"],
                p["id"],
                mode="full",
                backend="groq",
                model=MODEL,
                max_requirements=MAX_REQ,
                output_dir=str(OUT),
            )
            a = r.get("assessment") or {}
            if isinstance(a, dict) and a.get("overall_risk_level") and "error" not in a:
                # stamp compact_prompt false explicitly
                saved = json.loads(dest.read_text())
                saved["compact_prompt"] = False
                saved["mode"] = "full"
                dest.write_text(json.dumps(saved, indent=2), encoding="utf-8")
                print(
                    f"  OK risk={a['overall_risk_level']} "
                    f"rights={len(a.get('charter_rights_at_risk') or [])}",
                    flush=True,
                )
                ok = True
                break
            wait = 90 * attempt
            print(f"  fail attempt {attempt}, sleep {wait}s", flush=True)
            time.sleep(wait)
        if not ok:
            print(f"  QUOTA/FAIL {p['id']} — leaving backup; mark compact_prompt", flush=True)
            # restore backup and mark
            bak = BACKUP / f"{p['id']}_full.json"
            if bak.exists():
                data = json.loads(bak.read_text())
                data["compact_prompt"] = True
                dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
        time.sleep(2)
    # summary
    full = compact = 0
    for p in targets:
        data = json.loads((OUT / f"{p['id']}_full.json").read_text())
        if data.get("mode") == "full" and not data.get("compact_prompt"):
            full += 1
        else:
            compact += 1
            data["compact_prompt"] = True
            (OUT / f"{p['id']}_full.json").write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
    print(f"DONE full_rag={full} still_compact={compact}", flush=True)


if __name__ == "__main__":
    main()
