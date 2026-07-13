"""
inter_rater_agreement.py
Compute inter-reviewer agreement when human evaluation responses are available.

Metrics:
  - Cohen's Kappa: categorical / binary agreement (risk level, requirement selection)
  - Spearman rho: ordinal agreement on risk ratings across proposals

Usage:
  python3 inter_rater_agreement.py
  python3 inter_rater_agreement.py path/to/reviewer_responses.json

Expected JSON format (see reviewer_responses.template.json):
  {
    "reviewers": ["R1", "R2"],
    "proposals": [
      {
        "id": "P01",
        "ratings": {
          "R1": {"risk_level": "High", "requirements": ["R042", "AI001"]},
          "R2": {"risk_level": "High", "requirements": ["R042", "R054"]}
        }
      }
    ]
  }
"""

from __future__ import annotations

import json
import os
import sys
from itertools import combinations

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

DEFAULT_RESPONSES_FILE = "reviewer_responses.json"
RISK_LEVEL_ORDER = {"low": 1, "medium": 2, "high": 3}


def _normalize_risk(risk: str) -> str:
    return (risk or "").strip().lower()


def _normalize_requirement_id(req_id: str) -> str:
    if not req_id:
        return ""
    req_id = req_id.strip()
    for prefix in ("EUAIAct ", "EUAIAct-", "HorizonEurope ", "HorizonEurope-"):
        if prefix in req_id:
            req_id = req_id.split(prefix, 1)[-1]
    return req_id.strip()


def _kappa_interpretation(kappa: float | None) -> str | None:
    """Landis & Koch (1977) interpretation bands."""
    if kappa is None or (isinstance(kappa, float) and np.isnan(kappa)):
        return None
    if kappa > 0.80:
        return "Almost Perfect Agreement"
    if kappa > 0.60:
        return "Substantial Agreement"
    if kappa > 0.40:
        return "Moderate Agreement"
    if kappa > 0.20:
        return "Fair Agreement"
    return "Slight Agreement"


def _collect_requirement_universe(proposals: list) -> list[str]:
    req_ids = set()
    for proposal in proposals:
        for reviewer_data in proposal.get("ratings", {}).values():
            for req_id in reviewer_data.get("requirements", []):
                normalized = _normalize_requirement_id(req_id)
                if normalized:
                    req_ids.add(normalized)
    return sorted(req_ids)


def _risk_level_vectors(proposals: list, reviewer_a: str, reviewer_b: str) -> tuple[list, list]:
    labels_a, labels_b = [], []
    for proposal in proposals:
        ratings = proposal.get("ratings", {})
        if reviewer_a not in ratings or reviewer_b not in ratings:
            continue
        risk_a = _normalize_risk(ratings[reviewer_a].get("risk_level", ""))
        risk_b = _normalize_risk(ratings[reviewer_b].get("risk_level", ""))
        if risk_a and risk_b:
            labels_a.append(risk_a)
            labels_b.append(risk_b)
    return labels_a, labels_b


def _risk_level_spearman(proposals: list, reviewer_a: str, reviewer_b: str) -> dict:
    values_a, values_b = [], []
    for proposal in proposals:
        ratings = proposal.get("ratings", {})
        if reviewer_a not in ratings or reviewer_b not in ratings:
            continue
        risk_a = _normalize_risk(ratings[reviewer_a].get("risk_level", ""))
        risk_b = _normalize_risk(ratings[reviewer_b].get("risk_level", ""))
        if risk_a in RISK_LEVEL_ORDER and risk_b in RISK_LEVEL_ORDER:
            values_a.append(RISK_LEVEL_ORDER[risk_a])
            values_b.append(RISK_LEVEL_ORDER[risk_b])

    if len(values_a) < 2:
        return {"spearman_rho": None, "p_value": None, "n_proposals": len(values_a)}

    if len(set(values_a)) == 1 and len(set(values_b)) == 1:
        return {"spearman_rho": None, "p_value": None, "n_proposals": len(values_a)}

    rho, p_value = spearmanr(values_a, values_b)
    if np.isnan(rho):
        return {"spearman_rho": None, "p_value": None, "n_proposals": len(values_a)}

    return {
        "spearman_rho": round(float(rho), 3),
        "p_value": round(float(p_value), 4),
        "n_proposals": len(values_a),
    }


def _requirement_binary_vectors(
    proposals: list,
    reviewer_a: str,
    reviewer_b: str,
    requirement_ids: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    vector_a = []
    vector_b = []

    for proposal in proposals:
        ratings = proposal.get("ratings", {})
        if reviewer_a not in ratings or reviewer_b not in ratings:
            continue

        reqs_a = {
            _normalize_requirement_id(req_id)
            for req_id in ratings[reviewer_a].get("requirements", [])
        }
        reqs_b = {
            _normalize_requirement_id(req_id)
            for req_id in ratings[reviewer_b].get("requirements", [])
        }

        for req_id in requirement_ids:
            vector_a.append(1 if req_id in reqs_a else 0)
            vector_b.append(1 if req_id in reqs_b else 0)

    return np.array(vector_a), np.array(vector_b)


def calculate_pair_agreement(
    proposals: list,
    reviewer_a: str,
    reviewer_b: str,
) -> dict:
    """Calculate Cohen's Kappa and Spearman rho for one reviewer pair."""
    risk_labels_a, risk_labels_b = _risk_level_vectors(proposals, reviewer_a, reviewer_b)
    risk_kappa = None
    if risk_labels_a and (
        len(set(risk_labels_a)) > 1 or len(set(risk_labels_b)) > 1
    ):
        score = cohen_kappa_score(risk_labels_a, risk_labels_b)
        if not np.isnan(score):
            risk_kappa = round(float(score), 3)

    requirement_ids = _collect_requirement_universe(proposals)
    req_kappa = None
    if requirement_ids:
        req_a, req_b = _requirement_binary_vectors(
            proposals, reviewer_a, reviewer_b, requirement_ids
        )
        if len(req_a) > 0 and (np.any(req_a) or np.any(req_b)):
            score = cohen_kappa_score(req_a, req_b)
            if not np.isnan(score):
                req_kappa = round(float(score), 3)

    spearman = _risk_level_spearman(proposals, reviewer_a, reviewer_b)

    return {
        "reviewer_a": reviewer_a,
        "reviewer_b": reviewer_b,
        "risk_level_kappa": risk_kappa,
        "requirement_selection_kappa": req_kappa,
        "risk_level_spearman_rho": spearman["spearman_rho"],
        "risk_level_spearman_p_value": spearman["p_value"],
        "n_proposals": spearman["n_proposals"],
    }


def _divergence_note(pair_result: dict) -> str | None:
    """Explain likely reasons when Kappa and Spearman diverge."""
    kappa = pair_result.get("risk_level_kappa")
    rho = pair_result.get("risk_level_spearman_rho")

    if kappa is None or rho is None:
        return None

    if abs(kappa - rho) < 0.15:
        return None

    notes = []
    if kappa > rho + 0.15:
        notes.append(
            "Cohen's Kappa is higher than Spearman rho, suggesting reviewers often "
            "use the same risk labels but rank proposals differently in severity."
        )
    if rho > kappa + 0.15:
        notes.append(
            "Spearman rho is higher than Cohen's Kappa, suggesting reviewers preserve "
            "ordinal ordering while disagreeing on exact risk labels."
        )

    return " ".join(notes) if notes else None


def calculate_all_pairs(data: dict) -> dict:
    reviewers = data.get("reviewers", [])
    proposals = data.get("proposals", [])

    if len(reviewers) < 2:
        raise ValueError("At least two reviewers are required.")

    pair_results = []
    for reviewer_a, reviewer_b in combinations(reviewers, 2):
        result = calculate_pair_agreement(proposals, reviewer_a, reviewer_b)
        result["risk_level_kappa_interpretation"] = _kappa_interpretation(
            result["risk_level_kappa"]
        )
        result["requirement_kappa_interpretation"] = _kappa_interpretation(
            result["requirement_selection_kappa"]
        )
        result["divergence_note"] = _divergence_note(result)
        pair_results.append(result)

    return {
        "reviewers": reviewers,
        "proposal_count": len(proposals),
        "pairs": pair_results,
    }


def print_report(report: dict):
    print("\n" + "=" * 72)
    print("INTER-REVIEWER AGREEMENT REPORT")
    print("=" * 72)
    print(f"Reviewers: {', '.join(report['reviewers'])}")
    print(f"Proposals rated: {report['proposal_count']}")

    for pair in report["pairs"]:
        print("\n" + "-" * 72)
        print(f"Pair: {pair['reviewer_a']} vs {pair['reviewer_b']}  (n={pair['n_proposals']})")
        print(f"  Risk Level Cohen's Kappa:          {pair['risk_level_kappa'] or 'N/A (insufficient label variation)'}")
        if pair["risk_level_kappa_interpretation"]:
            print(f"    -> {pair['risk_level_kappa_interpretation']}")
        print(
            f"  Requirement Selection Cohen's Kappa: "
            f"{pair['requirement_selection_kappa'] or 'N/A'}"
        )
        if pair["requirement_kappa_interpretation"]:
            print(f"    -> {pair['requirement_kappa_interpretation']}")
        rho = pair["risk_level_spearman_rho"]
        p_value = pair["risk_level_spearman_p_value"]
        if rho is None:
            print("  Risk Level Spearman rho:           N/A (insufficient ordinal variation)")
        else:
            print(f"  Risk Level Spearman rho:           {rho} (p={p_value})")
        if pair["divergence_note"]:
            print(f"  Divergence note: {pair['divergence_note']}")

    print("\n" + "=" * 72)


def main():
    responses_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RESPONSES_FILE

    if not os.path.exists(responses_file):
        print(f"No reviewer responses found at '{responses_file}'.")
        print("Add ratings using reviewer_responses.template.json, then re-run.")
        return 1

    with open(responses_file) as f:
        data = json.load(f)

    if not data.get("proposals"):
        print(f"'{responses_file}' exists but contains no proposal ratings yet.")
        return 1

    report = calculate_all_pairs(data)
    print_report(report)

    output_path = os.path.join("outputs", "inter_rater_agreement.json")
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
