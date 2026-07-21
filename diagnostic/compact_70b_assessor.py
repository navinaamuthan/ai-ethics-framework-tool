"""
Compact 70B assessor for diagnostic corpus expansion (P21–P40).

Uses a short risk+rights-only prompt (~1–2k tokens) so Groq free-tier TPD
can finish the expanded set. Writes evaluation/results/llama-3.3-70b/P##_full.json
with mode=compact_diagnostic. P01–P20 remain full-RAG variance seeds.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAG = ROOT.parent / "rag-pipeline"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

from llm_caller import call_groq, parse_json_response, test_groq_connection
from synthetic_proposals_extended import PROPOSALS

OUT = ROOT.parent / "evaluation" / "results" / "llama-3.3-70b"
VOCAB = sorted({a for p in PROPOSALS for a in p["expected_charter_articles"]})
MODEL = "llama-3.3-70b-versatile"


def has_risk(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        a = json.loads(path.read_text(encoding="utf-8")).get("assessment") or {}
        return isinstance(a, dict) and bool(a.get("overall_risk_level"))
    except Exception:
        return False


def build_prompt(p: dict) -> str:
    vocab = ", ".join(VOCAB)
    return f"""You are an AI ethics assessor. Read the research proposal and return ONLY JSON:
{{"overall_risk_level":"High|Medium|Low","charter_rights_at_risk":[{{"article":"<exact vocab string>","right_name":"...","relevance":"one sentence"}}]}}

Use ONLY article strings from this vocabulary: [{vocab}]

PROPOSAL ID: {p['id']}
TITLE: {p['title']}
TEXT:
{p['proposal_text']}
"""


def main() -> None:
    assert test_groq_connection(MODEL)
    OUT.mkdir(parents=True, exist_ok=True)
    need = [p for p in PROPOSALS if not has_risk(OUT / f"{p['id']}_full.json")]
    print(f"need {len(need)}: {[p['id'] for p in need]}", flush=True)

    for i, p in enumerate(need, 1):
        print(f"[{i}/{len(need)}] {p['id']}", flush=True)
        ok = False
        for attempt in range(1, 10):
            raw = call_groq(
                build_prompt(p),
                model=MODEL,
                temperature=0.2,
                max_tokens=600,
                max_retries=1,
            )
            if not raw:
                wait = 60 * attempt
                print(f"  empty/429 — sleep {wait}s", flush=True)
                time.sleep(wait)
                continue
            parsed = parse_json_response(raw)
            risk = parsed.get("overall_risk_level")
            rights = parsed.get("charter_rights_at_risk") or []
            if risk not in {"High", "Medium", "Low"}:
                print(f"  bad parse attempt {attempt}: {parsed.get('parse_error')}", flush=True)
                time.sleep(20)
                continue
            # filter rights to vocab
            cleaned = []
            for item in rights:
                if isinstance(item, dict):
                    art = item.get("article") or ""
                    if art in VOCAB:
                        cleaned.append(item)
                    else:
                        # try fuzzy: match ArtN_ prefix
                        for v in VOCAB:
                            if v.split("_")[0] in str(art) or str(art) in v:
                                item = dict(item)
                                item["article"] = v
                                cleaned.append(item)
                                break
            payload = {
                "proposal_id": p["id"],
                "mode": "compact_diagnostic",
                "llm_backend": "groq",
                "llm_model": MODEL,
                "note": (
                    "Compact risk+rights prompt for diagnostic corpus expansion "
                    "under Groq TPD limits; P01-P20 are full-RAG."
                ),
                "proposal_text": p["proposal_text"],
                "assessment": {
                    "overall_risk_level": risk,
                    "charter_rights_at_risk": cleaned,
                    "confidence_flag": "LOW",
                },
            }
            (OUT / f"{p['id']}_full.json").write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
            print(f"  OK risk={risk} rights={len(cleaned)}", flush=True)
            ok = True
            break
        if not ok:
            print(f"  GIVE UP {p['id']}", flush=True)
        time.sleep(3)
    left = [p["id"] for p in PROPOSALS if not has_risk(OUT / f"{p['id']}_full.json")]
    print(f"DONE remaining={left}", flush=True)


if __name__ == "__main__":
    main()
