"""
frame_annotation.py
Simulate four annotator perspectives × 3 independent runs × 40 proposals
(= 480 records) for the diagnostic methodology reliability study.

Thesis pinned: An evaluation protocol that scores an automated assessor
against reference labels is itself a measurement instrument, and its validity
depends on conditions — chiefly, the reliability of those reference labels —
that are not currently checked before such protocols are used.

Persona prompts are used VERBATIM (do not paraphrase).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAG = ROOT.parent / "rag-pipeline"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(ROOT))

from llm_caller import call_llm, parse_json_response  # noqa: E402
from synthetic_proposals_extended import PROPOSALS  # noqa: E402

PERSONAS = {
    "technical": (
        "You are a senior machine learning engineer reviewing this "
        "research proposal for an internal risk assessment. Focus on what is "
        "technically verifiable: data provenance, model validation, measurable "
        "failure modes. You are skeptical of claims that cannot be checked against "
        "the described methodology."
    ),
    "legal": (
        "You are an EU data protection and fundamental rights lawyer "
        "reviewing this proposal against the EU Charter of Fundamental Rights and "
        "GDPR. Identify which Charter articles are engaged and how severely, "
        "based on established case law and regulatory guidance where relevant."
    ),
    "ethics": (
        "You are a member of a university research ethics committee "
        "reviewing this proposal. Focus on consent, power imbalances, vulnerable "
        "populations, and whether affected people have any way to contest or "
        "opt out of the described system."
    ),
    "lay": (
        "You are a person with no technical or legal training who would "
        "be directly affected by the system described in this proposal (e.g. a "
        "patient, defendant, student, or employee, whichever applies). Judge the "
        "proposal based on how it would feel to be subject to this system, "
        "without using technical or legal jargon."
    ),
}

CHARTER_VOCAB = sorted(
    {a for p in PROPOSALS for a in p["expected_charter_articles"]}
)

OUTPUT_PATH = ROOT / "frame_annotations.json"
SKIP_LOG_PATH = ROOT / "results" / "frame_annotation_skips.json"


def build_user_prompt(proposal: dict) -> str:
    vocab = ", ".join(CHARTER_VOCAB)
    return f"""Task: Annotate the research proposal below.

Return a single JSON object with exactly these keys:
  "risk_level": one of "High", "Medium", "Low"
  "charter_articles": a JSON array of zero or more strings, each MUST be drawn
      from this vocabulary (copy spelling exactly): [{vocab}]
  "info_sufficiency": an integer from 1 to 5 meaning how much information you
      needed versus how much you were given (5 = fully sufficient to judge
      confidently; 1 = genuinely under-specified)

Do not invent article names outside the vocabulary. Do not include commentary
outside the JSON object.

PROPOSAL ID: {proposal["id"]}
TITLE: {proposal["title"]}
PROPOSAL TEXT:
{proposal["proposal_text"]}
"""


def _extract_record(parsed: dict, proposal_id: str, perspective: str, run: int):
    if "parse_error" in parsed:
        return None, f"parse_error: {parsed.get('parse_error')}"

    risk = parsed.get("risk_level")
    if risk not in {"High", "Medium", "Low"}:
        return None, f"bad risk_level: {risk!r}"

    arts = parsed.get("charter_articles")
    if not isinstance(arts, list):
        return None, f"charter_articles not a list: {arts!r}"
    cleaned = []
    vocab = set(CHARTER_VOCAB)
    for a in arts:
        a = str(a).strip()
        if a in vocab:
            cleaned.append(a)
        # silently drop invents; empty list is allowed

    info = parsed.get("info_sufficiency")
    try:
        info = int(info)
    except (TypeError, ValueError):
        return None, f"bad info_sufficiency: {info!r}"
    if not 1 <= info <= 5:
        return None, f"info_sufficiency out of range: {info}"

    return {
        "proposal_id": proposal_id,
        "perspective": perspective,
        "run": run,
        "risk_level": risk,
        "charter_articles": cleaned,
        "info_sufficiency": info,
    }, None


def _call_with_backoff(
    prompt: str,
    backend: str,
    model: str | None,
    temperature: float,
    max_tokens: int = 800,
    rate_limit_waits: int = 4,
) -> str:
    """Call LLM; on empty response (often 429), wait and retry before giving up."""
    for wait_i in range(rate_limit_waits + 1):
        raw = call_llm(
            prompt,
            backend=backend,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=1,
        )
        if raw:
            return raw
        if wait_i < rate_limit_waits:
            delay = 75 * (wait_i + 1)
            print(f"  empty response — sleeping {delay}s (rate-limit backoff)...")
            time.sleep(delay)
    return ""


def annotate_one(
    proposal: dict,
    perspective: str,
    run: int,
    backend: str,
    model: str | None,
    temperature: float,
) -> tuple[dict | None, str | None]:
    system = PERSONAS[perspective]
    user = build_user_prompt(proposal)
    # llm_caller has no separate system role for ollama; prepend persona.
    prompt = f"SYSTEM PERSONA (stay in role):\n{system}\n\nUSER TASK:\n{user}"

    raw = _call_with_backoff(prompt, backend, model, temperature)
    if not raw:
        return None, "empty LLM response"

    parsed = parse_json_response(raw)
    rec, err = _extract_record(parsed, proposal["id"], perspective, run)
    if rec is not None:
        return rec, None

    # Retry once on parse/schema failure (fresh call).
    raw2 = _call_with_backoff(
        prompt + "\n\nYour previous answer was invalid. Return ONLY valid JSON.",
        backend,
        model,
        temperature,
    )
    if not raw2:
        return None, f"retry empty after: {err}"
    parsed2 = parse_json_response(raw2)
    rec2, err2 = _extract_record(parsed2, proposal["id"], perspective, run)
    if rec2 is not None:
        return rec2, None
    return None, f"skip after retry: {err2 or err}"


def load_existing() -> list[dict]:
    if OUTPUT_PATH.exists():
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    return []


def record_key(r: dict) -> tuple:
    return (r["proposal_id"], r["perspective"], int(r["run"]))


def run_annotation(
    backend: str = "groq",
    model: str | None = None,
    temperature: float = 0.7,
    resume: bool = True,
) -> None:
    assert len(PROPOSALS) == 40, len(PROPOSALS)

    existing = load_existing() if resume else []
    done = {record_key(r) for r in existing}
    records = list(existing)
    skips: list[dict] = []

    total = 4 * 3 * 40
    planned = [
        (persp, run, prop)
        for persp in PERSONAS
        for run in (1, 2, 3)
        for prop in PROPOSALS
    ]

    print(f"Frame annotation: {total} target records; {len(done)} already done.")
    print(f"Backend={backend} model={model or 'default'} temperature={temperature}")

    for i, (persp, run, prop) in enumerate(planned, 1):
        key = (prop["id"], persp, run)
        if key in done:
            continue
        print(f"[{i}/{total}] {prop['id']} {persp} run={run} ...", flush=True)
        rec, err = annotate_one(prop, persp, run, backend, model, temperature)
        if rec is None:
            print(f"  SKIP: {err}")
            skips.append(
                {
                    "proposal_id": prop["id"],
                    "perspective": persp,
                    "run": run,
                    "error": err,
                }
            )
        else:
            records.append(rec)
            done.add(key)
            print(
                f"  OK risk={rec['risk_level']} arts={len(rec['charter_articles'])} "
                f"info={rec['info_sufficiency']}"
            )

        # Checkpoint every 10 new writes.
        if len(records) % 10 == 0:
            OUTPUT_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")

        # Gentle rate limit for Groq free tier.
        if backend == "groq":
            time.sleep(0.35)

    OUTPUT_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
    SKIP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SKIP_LOG_PATH.write_text(json.dumps(skips, indent=2), encoding="utf-8")

    skip_count = len(skips)
    print(f"\nWrote {OUTPUT_PATH} with {len(records)} records.")
    print(f"Skip count: {skip_count} (logged to {SKIP_LOG_PATH})")

    if skip_count >= 24:
        # Diagnose systematic failure by persona/run.
        from collections import Counter

        by = Counter((s["perspective"], s["run"]) for s in skips)
        raise SystemExit(
            f"HALT: skip count {skip_count} >= 24 (≥5% of 480). "
            f"Failures by (persona, run): {by.most_common()}"
        )

    # Soft assert on expected size.
    if len(records) < 456:
        raise SystemExit(
            f"HALT: only {len(records)} records (need ≥456 = 480−24)."
        )
    print(f"Acceptance OK: {len(records)}/480 records (skips={skip_count}).")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="groq", choices=["groq", "ollama"])
    parser.add_argument(
        "--model",
        default=None,
        help="Default for groq: llama-3.1-8b-instant (70B TPD often exhausted).",
    )
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Annotate only P01×technical×run1 then exit.",
    )
    args = parser.parse_args()

    model = args.model
    if model is None and args.backend == "groq":
        model = "llama-3.1-8b-instant"

    if args.smoke:
        prop = PROPOSALS[0]
        rec, err = annotate_one(
            prop, "technical", 1, args.backend, model, args.temperature
        )
        print(json.dumps({"record": rec, "error": err}, indent=2))
        return

    run_annotation(
        backend=args.backend,
        model=model,
        temperature=args.temperature,
        resume=not args.no_resume,
    )


if __name__ == "__main__":
    main()
