#!/usr/bin/env python3
"""
Diagnose Charter-rights matching before/after the weighted-relevance fix.

Captures, for all 20 synthetic proposals:
  (a) which keywords fired (+ occurrence counts in after-mode)
  (b) which rights came from keywords vs Art8/Art41 injection
  (c) matched-rights count per proposal

The "before" baseline is the pre-fix binary presence matcher (substring hit
= right matched; soft Art8/Art41 inject on any data/admin signal keyword),
frozen here so before/after stays reproducible after the live code changes.

Usage:
  python analysis/diagnose_rights_matching.py              # before + after
  python analysis/diagnose_rights_matching.py --mode before
  python analysis/diagnose_rights_matching.py --mode after
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "rag-pipeline"))

from sparql_retrieval import (  # noqa: E402
    KEYWORD_TO_RIGHTS,
    extract_keywords,
    get_matched_rights,
)
from synthetic_proposals import PROPOSALS  # noqa: E402

OUT = Path(__file__).parent / "results" / "rights_matching_diagnosis.json"

# Frozen pre-fix keyword map (includes bare "data" + Art41 on scor/chatbot)
_BEFORE_KEYWORD_TO_RIGHTS = {
    "bias": ["Art21_NonDiscrimination", "Art23_GenderEquality", "Art20_EqualityBeforeLaw"],
    "discriminat": ["Art21_NonDiscrimination", "Art23_GenderEquality", "Art26_DisabilityIntegration"],
    "privacy": ["Art7_PrivateLife", "Art8_DataProtection"],
    "data": ["Art8_DataProtection", "Art7_PrivateLife"],
    "personal data": ["Art8_DataProtection", "Art7_PrivateLife"],
    "consent": ["Art3_RightToIntegrity", "Art7_PrivateLife"],
    "health": ["Art35_HealthCare", "Art2_RightToLife"],
    "medical": ["Art35_HealthCare", "Art2_RightToLife"],
    "diagnos": ["Art35_HealthCare", "Art2_RightToLife"],
    "patient": ["Art35_HealthCare", "Art2_RightToLife", "Art8_DataProtection"],
    "child": ["Art24_RightsOfChild"],
    "minor": ["Art24_RightsOfChild"],
    "student": ["Art24_RightsOfChild", "Art8_DataProtection"],
    "school": ["Art24_RightsOfChild", "Art8_DataProtection"],
    "autonomy": ["Art6_RightToLiberty", "Art1_HumanDignity"],
    "harm": ["Art1_HumanDignity", "Art2_RightToLife", "Art47_RightToEffectiveRemedy"],
    "surveil": ["Art7_PrivateLife", "Art8_DataProtection", "Art6_RightToLiberty"],
    "monitor": ["Art7_PrivateLife", "Art8_DataProtection"],
    "track": ["Art7_PrivateLife", "Art8_DataProtection"],
    "environment": ["Art37_EnvironmentalProtection"],
    "carbon": ["Art37_EnvironmentalProtection"],
    "fairness": ["Art20_EqualityBeforeLaw", "Art21_NonDiscrimination"],
    "transparen": ["Art41_GoodAdministration", "Art47_RightToEffectiveRemedy"],
    "accountab": ["Art41_GoodAdministration", "Art47_RightToEffectiveRemedy"],
    "explain": ["Art41_GoodAdministration", "Art47_RightToEffectiveRemedy"],
    "safety": ["Art2_RightToLife", "Art1_HumanDignity"],
    "employ": ["Art31_FairWorkingConditions", "Art15_FreedomOfOccupation"],
    "hiring": ["Art15_FreedomOfOccupation", "Art21_NonDiscrimination", "Art23_GenderEquality"],
    "recruit": ["Art15_FreedomOfOccupation", "Art21_NonDiscrimination"],
    "employee": ["Art31_FairWorkingConditions", "Art15_FreedomOfOccupation"],
    "staff": ["Art31_FairWorkingConditions", "Art8_DataProtection"],
    "workplace": ["Art31_FairWorkingConditions", "Art15_FreedomOfOccupation"],
    "working conditions": ["Art31_FairWorkingConditions"],
    "manipulat": ["Art1_HumanDignity", "Art6_RightToLiberty"],
    "deception": ["Art1_HumanDignity", "Art11_FreedomOfExpression"],
    "deepfake": ["Art1_HumanDignity", "Art7_PrivateLife"],
    "facial recogn": ["Art7_PrivateLife", "Art8_DataProtection", "Art21_NonDiscrimination"],
    "biometric": ["Art7_PrivateLife", "Art8_DataProtection", "Art1_HumanDignity"],
    "prediction": ["Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy"],
    "predict": ["Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy"],
    "profil": ["Art7_PrivateLife", "Art8_DataProtection", "Art21_NonDiscrimination"],
    "classif": ["Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy"],
    "scor": ["Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy", "Art41_GoodAdministration"],
    "vulnerable": ["Art1_HumanDignity", "Art24_RightsOfChild"],
    "minority": ["Art21_NonDiscrimination", "Art22_CulturalDiversity"],
    "race": ["Art21_NonDiscrimination"],
    "racial": ["Art21_NonDiscrimination"],
    "gender": ["Art21_NonDiscrimination", "Art23_GenderEquality"],
    "disabilit": ["Art26_DisabilityIntegration"],
    "criminal": ["Art6_RightToLiberty", "Art47_RightToEffectiveRemedy", "Art48_PresumptionOfInnocence"],
    "polic": ["Art6_RightToLiberty", "Art21_NonDiscrimination", "Art7_PrivateLife"],
    "law enforce": ["Art6_RightToLiberty", "Art48_PresumptionOfInnocence", "Art47_RightToEffectiveRemedy"],
    "autonomous": ["Art2_RightToLife", "Art1_HumanDignity"],
    "self-driving": ["Art2_RightToLife", "Art1_HumanDignity"],
    "weapon": ["Art2_RightToLife", "Art1_HumanDignity"],
    "dual-use": ["Art2_RightToLife", "Art1_HumanDignity", "Art11_FreedomOfExpression"],
    "content moder": ["Art11_FreedomOfExpression", "Art21_NonDiscrimination"],
    "recommend": ["Art11_FreedomOfExpression", "Art1_HumanDignity"],
    "chatbot": ["Art1_HumanDignity", "Art41_GoodAdministration"],
    "generat": ["Art1_HumanDignity", "Art7_PrivateLife"],
    "emotion": ["Art1_HumanDignity", "Art7_PrivateLife", "Art3_RightToIntegrity"],
    "sentiment": ["Art7_PrivateLife", "Art11_FreedomOfExpression"],
    "social media": ["Art7_PrivateLife", "Art8_DataProtection", "Art11_FreedomOfExpression"],
    "scraping": ["Art7_PrivateLife", "Art8_DataProtection"],
    "cross-border": ["Art8_DataProtection", "Art7_PrivateLife"],
    "transfer": ["Art8_DataProtection"],
    "protest": ["Art12_FreedomOfAssembly", "Art11_FreedomOfExpression"],
    "assembly": ["Art12_FreedomOfAssembly"],
    "union": ["Art12_FreedomOfAssembly", "Art31_FairWorkingConditions"],
    "organizing": ["Art12_FreedomOfAssembly", "Art11_FreedomOfExpression"],
    "organisation": ["Art12_FreedomOfAssembly", "Art11_FreedomOfExpression"],
    "association": ["Art12_FreedomOfAssembly"],
    "collective": ["Art12_FreedomOfAssembly"],
}

# Frozen Phase-3 soft-inject signal sets (pre-weighted-relevance)
_BEFORE_DATA_SIGNALS = {
    "privacy", "data", "personal data", "consent", "biometric",
    "surveil", "monitor", "track", "patient", "student", "scraping",
    "transfer", "cross-border", "profil",
}
_BEFORE_ADMIN_SIGNALS = {"transparen", "accountab", "explain", "chatbot", "scor"}


def _before_extract(proposal: str) -> list:
    text = proposal.lower()
    return [term for term in _BEFORE_KEYWORD_TO_RIGHTS if term in text]


def _before_matched(proposal: str) -> dict:
    """Reproduce pre-fix binary matching + soft Art8/Art41 inject."""
    keywords = _before_extract(proposal)
    from_keywords: set[str] = set()
    for kw in keywords:
        from_keywords.update(_BEFORE_KEYWORD_TO_RIGHTS.get(kw, []))

    injected: set[str] = set()
    if any(k in _BEFORE_DATA_SIGNALS for k in keywords):
        injected.add("Art8_DataProtection")
    if any(k in _BEFORE_ADMIN_SIGNALS for k in keywords):
        injected.add("Art41_GoodAdministration")

    net_injected = injected - from_keywords
    all_rights = sorted(from_keywords | injected)
    return {
        "keywords": keywords,
        "keyword_counts": {k: 1 for k in keywords},
        "rights_from_keywords": sorted(from_keywords),
        "rights_injected": sorted(net_injected),
        "rights_injected_requested": sorted(injected),
        "matched_rights": all_rights,
        "n_keywords": len(keywords),
        "n_rights": len(all_rights),
    }


def _after_matched(proposal: str) -> dict:
    """Live weighted matcher (post-fix)."""
    # Prefer rich hit dict if available
    hits = None
    if hasattr(extract_keywords, "with_counts"):
        hits = extract_keywords.with_counts(proposal)  # type: ignore[attr-defined]
    keywords = extract_keywords(proposal)
    rights = get_matched_rights(keywords, proposal=proposal)

    meta = getattr(get_matched_rights, "last_match_meta", {}) or {}
    return {
        "keywords": keywords,
        "keyword_counts": hits or meta.get("keyword_counts") or {k: 1 for k in keywords},
        "rights_from_keywords": meta.get("rights_from_keywords", rights),
        "rights_injected": meta.get("rights_injected", []),
        "rights_injected_requested": meta.get("rights_injected_requested", []),
        "matched_rights": rights,
        "n_keywords": len(keywords),
        "n_rights": len(rights),
        "right_scores": meta.get("right_scores", {}),
        "disambiguation": getattr(get_matched_rights, "last_disambiguation", "n/a"),
    }


def _print_table(rows: list, label: str) -> None:
    print(f"\n{'=' * 88}")
    print(f"{label}")
    print(f"{'=' * 88}")
    print(f"{'PID':4}  {'#kw':>4}  {'#rights':>7}  {'Art8':>4}  {'Art41':>5}  {'injected':>18}  keywords (top)")
    print("-" * 88)
    art8_n = art41_n = 0
    for r in rows:
        rights = set(r["matched_rights"])
        a8 = "Art8_DataProtection" in rights
        a41 = "Art41_GoodAdministration" in rights
        art8_n += int(a8)
        art41_n += int(a41)
        inj = ",".join(r.get("rights_injected") or []) or "-"
        kws = ", ".join(r["keywords"][:6])
        if len(r["keywords"]) > 6:
            kws += f" (+{len(r['keywords'])-6})"
        print(
            f"{r['id']:4}  {r['n_keywords']:4d}  {r['n_rights']:7d}  "
            f"{'Y' if a8 else '-':>4}  {'Y' if a41 else '-':>5}  {inj:>18}  {kws}"
        )
    print("-" * 88)
    print(f"Art8 in {art8_n}/20 | Art41 in {art41_n}/20 | "
          f"mean rights={sum(r['n_rights'] for r in rows)/len(rows):.1f} | "
          f"mean kw={sum(r['n_keywords'] for r in rows)/len(rows):.1f}")
    wide = [r for r in rows if r["n_keywords"] >= 10]
    thin = [r for r in rows if r["n_keywords"] <= 2]
    if wide:
        print(f"Wide keyword matches (≥10): {[r['id'] for r in wide]}")
    if thin:
        print(f"Thin keyword matches (≤2): {[r['id'] for r in thin]}")


def main(mode: str = "both") -> None:
    before_rows, after_rows = [], []
    for p in PROPOSALS:
        if mode in ("before", "both"):
            b = _before_matched(p["proposal_text"])
            b["id"] = p["id"]
            before_rows.append(b)
        if mode in ("after", "both"):
            a = _after_matched(p["proposal_text"])
            a["id"] = p["id"]
            after_rows.append(a)

    if before_rows:
        _print_table(before_rows, "BEFORE — binary keyword presence + soft Art8/Art41 inject")
    if after_rows:
        _print_table(after_rows, "AFTER — weighted / density-scored rights matching")

    if before_rows and after_rows:
        print(f"\n{'=' * 88}")
        print("DELTA (before → after)")
        print(f"{'=' * 88}")
        for b, a in zip(before_rows, after_rows):
            dropped = sorted(set(b["matched_rights"]) - set(a["matched_rights"]))
            added = sorted(set(a["matched_rights"]) - set(b["matched_rights"]))
            print(
                f"{b['id']}: {b['n_rights']}→{a['n_rights']} rights  "
                f"kw {b['n_keywords']}→{a['n_keywords']}"
                + (f"  dropped={dropped}" if dropped else "")
                + (f"  added={added}" if added else "")
            )

    OUT.parent.mkdir(exist_ok=True)
    payload = {"before": before_rows, "after": after_rows}
    if before_rows and after_rows:
        payload["summary"] = {
            "before_mean_rights": sum(r["n_rights"] for r in before_rows) / 20,
            "after_mean_rights": sum(r["n_rights"] for r in after_rows) / 20,
            "before_art8": sum("Art8_DataProtection" in r["matched_rights"] for r in before_rows),
            "after_art8": sum("Art8_DataProtection" in r["matched_rights"] for r in after_rows),
            "before_art41": sum("Art41_GoodAdministration" in r["matched_rights"] for r in before_rows),
            "after_art41": sum("Art41_GoodAdministration" in r["matched_rights"] for r in after_rows),
        }
    json.dump(payload, open(OUT, "w"), indent=2)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["before", "after", "both"], default="both")
    args = ap.parse_args()
    main(mode=args.mode)
