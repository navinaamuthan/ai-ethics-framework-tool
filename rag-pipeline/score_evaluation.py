import argparse
import glob
import json
import os

from synthetic_proposals import PROPOSALS

GROUND_TRUTH = {p["id"]: p for p in PROPOSALS}

ALL_REQ_IDS = (
    {f"R{str(i).zfill(3)}" for i in range(1, 88)}
    | {f"AI{str(i).zfill(3)}" for i in range(1, 31)}
    | {f"HE{str(i).zfill(3)}" for i in range(1, 53)}
    | {f"ACM{str(i).zfill(3)}" for i in range(1, 39)}
)


def normalize_requirement_id(req_id: str) -> str:
    """Normalize requirement IDs for comparison across frameworks."""
    if not req_id:
        return ""
    req_id = req_id.strip()
    for prefix in ("EUAIAct ", "EUAIAct-", "HorizonEurope ", "HorizonEurope-"):
        if prefix in req_id:
            req_id = req_id.split(prefix, 1)[-1]
    return req_id.strip()


def _get_retrieved_requirement_ids(data: dict) -> tuple[set[str], bool]:
    """
    Return the set of requirement IDs retrieved by the KG for this proposal.
    Prefers the full retrieved set; falls back to live KG lookup or sample.
    """
    metadata = data.get("assessment", {}).get("_retrieval_metadata", {})

    if metadata.get("requirements_retrieved_ids"):
        retrieved = {
            normalize_requirement_id(req_id)
            for req_id in metadata["requirements_retrieved_ids"]
        }
        return retrieved, True

    proposal_text = data.get("proposal_text", "")
    if proposal_text:
        try:
            from sparql_retrieval import retrieve_all_for_proposal

            reqs, _, _, _ = retrieve_all_for_proposal(proposal_text)
            retrieved = {normalize_requirement_id(r["id"]) for r in reqs}
            return retrieved, True
        except Exception:
            pass

    retrieved = {
        normalize_requirement_id(req_id)
        for req_id in metadata.get("requirements_sample", [])
    }
    return retrieved, False


def retrieval_recall(proposal: dict, output_file: str) -> dict:
    """
    Measure retrieval-level recall: did the KG surface expected requirements?

    Distinct from generation-level recall (whether the LLM cited them).
    Framing: Gao et al. (2023) "Retrieval-Augmented Generation for Large
    Language Models: A Survey" (arXiv:2312.10997) — retrieval quality and
    generation quality are separate evaluation dimensions.
    """
    with open(output_file) as f:
        data = json.load(f)

    expected_reqs = {
        normalize_requirement_id(req_id)
        for req_id in proposal["expected_requirements"]
    }
    retrieved_reqs, uses_full_set = _get_retrieved_requirement_ids(data)

    hits = expected_reqs & retrieved_reqs
    recall = len(hits) / len(expected_reqs) if expected_reqs else 1.0

    return {
        "retrieval_recall": round(recall, 2),
        "retrieval_hits": len(hits),
        "expected_count": len(expected_reqs),
        "retrieved_count": len(retrieved_reqs),
        "hit_reqs": sorted(hits),
        "missed_at_retrieval": sorted(expected_reqs - retrieved_reqs),
        "uses_full_retrieval_set": uses_full_set,
    }


def generation_recall(proposal: dict, assessment: dict) -> dict:
    """Measure generation-level recall: did the LLM cite expected requirements?"""
    predicted_reqs = {
        normalize_requirement_id(r.get("requirement_id", ""))
        for r in assessment.get("applicable_requirements", [])
        if r.get("requirement_id", "").startswith(("R", "AI", "HE", "ACM", "EUAIAct", "HorizonEurope"))
    }
    predicted_reqs.discard("")

    expected_reqs = {
        normalize_requirement_id(req_id)
        for req_id in proposal["expected_requirements"]
    }

    hits = expected_reqs & predicted_reqs
    recall = len(hits) / len(expected_reqs) if expected_reqs else 1.0
    precision = len(hits) / len(predicted_reqs) if predicted_reqs else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "req_precision": round(precision, 2),
        "req_recall": round(recall, 2),
        "req_f1": round(f1, 2),
        "predicted_reqs": sorted(predicted_reqs),
        "expected_reqs": sorted(expected_reqs),
        "missed_reqs": sorted(expected_reqs - predicted_reqs),
    }


def print_confusion_matrix(results):
    """
    results: list of dicts with keys 'expected' and 'predicted'
    """
    levels = ["High", "Medium", "Low"]

    matrix = {a: {p: 0 for p in levels + ["N/A"]} for a in levels}
    for r in results:
        actual = r["expected"]
        predicted = r["predicted"]
        if actual in matrix:
            if predicted in matrix[actual]:
                matrix[actual][predicted] += 1
            else:
                matrix[actual]["N/A"] += 1

    print("\nCONFUSION MATRIX (Actual vs Predicted):")
    print(f"{'':12} {'Pred:High':>10} {'Pred:Med':>10} {'Pred:Low':>10} {'Pred:N/A':>10}")
    print("-" * 54)
    for actual in levels:
        row = matrix[actual]
        print(f"Act:{actual:<8} {row['High']:>10} {row['Medium']:>10} {row['Low']:>10} {row.get('N/A', 0):>10}")

    print("\nPER-CLASS METRICS:")
    print(f"{'Level':<10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print("-" * 44)
    for level in levels:
        tp = matrix[level][level]
        fp = sum(matrix[a][level] for a in levels if a != level)
        fn = sum(matrix[level][p] for p in levels if p != level)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        support = sum(matrix[level].values())
        print(f"{level:<10} {precision:>10.2f} {recall:>10.2f} {f1:>10.2f} {support:>10}")


def print_requirement_coverage(output_dir, all_requirement_ids):
    """
    all_requirement_ids: set of all 207 req IDs (e.g. {'R001', 'AI001', ...})
    Reads all *_full.json files and finds which reqs were cited at least once.
    """
    triggered = set()

    for filepath in glob.glob(os.path.join(output_dir, "*_full.json")):
        with open(filepath) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue
        assessment = data.get("assessment", {})
        for req in assessment.get("applicable_requirements", []):
            req_id = normalize_requirement_id(req.get("requirement_id", ""))
            if req_id:
                triggered.add(req_id)

    never_triggered = all_requirement_ids - triggered

    print("\nREQUIREMENT COVERAGE ANALYSIS:")
    print(f"  Total requirements in KG:   {len(all_requirement_ids)}")
    print(f"  Requirements triggered:     {len(triggered)} ({100 * len(triggered) / len(all_requirement_ids):.1f}%)")
    print(f"  Requirements never cited:   {len(never_triggered)} ({100 * len(never_triggered) / len(all_requirement_ids):.1f}%)")

    for prefix, name in [("R", "REAMS"), ("AI", "EU AI Act"), ("HE", "Horizon Europe"), ("ACM", "ACM/NeurIPS")]:
        fw_all = {r for r in all_requirement_ids if r.startswith(prefix)}
        fw_hit = {r for r in triggered if r.startswith(prefix)}
        pct = 100 * len(fw_hit) / len(fw_all) if fw_all else 0
        print(f"  {name:<20} {len(fw_hit):>3}/{len(fw_all):<3} triggered ({pct:.0f}%)")

    print("\n  Never-triggered requirement IDs:")
    for prefix, name in [("R", "REAMS"), ("AI", "EU AI Act"), ("HE", "Horizon Europe"), ("ACM", "ACM/NeurIPS")]:
        missed = sorted(r for r in never_triggered if r.startswith(prefix))
        if missed:
            print(f"    {name}: {', '.join(missed)}")


def score_all(output_dir: str = "outputs"):
    results = []
    results_for_matrix = []

    for proposal in PROPOSALS:
        pid = proposal["id"]
        output_file = os.path.join(output_dir, f"{pid}_full.json")

        if not os.path.exists(output_file):
            continue

        with open(output_file) as f:
            data = json.load(f)

        assessment = data.get("assessment", {})
        retrieval = retrieval_recall(proposal, output_file)
        generation = generation_recall(proposal, assessment)

        predicted_rights = set(
            r.get("article", "").replace("Article ", "Art").replace(" ", "_")
            for r in assessment.get("charter_rights_at_risk", [])
        )
        expected_rights = set(r.replace("_", "_") for r in proposal["expected_rights"])

        if expected_rights:
            right_tp = len(predicted_rights & expected_rights)
            right_recall = right_tp / len(expected_rights) if expected_rights else 0
        else:
            right_recall = 1.0

        risk_match = assessment.get("overall_risk_level", "").lower() == proposal["risk_level"].lower()
        expected_risk = proposal["risk_level"]
        predicted_risk = assessment.get("overall_risk_level") or "N/A"

        results_for_matrix.append({
            "expected": expected_risk,
            "predicted": predicted_risk,
        })

        results.append({
            "id": pid,
            "title": proposal["title"],
            "risk_level": proposal["risk_level"],
            "risk_match": risk_match,
            "retrieval_recall": retrieval["retrieval_recall"],
            "retrieval_hits": retrieval["retrieval_hits"],
            "retrieved_count": retrieval["retrieved_count"],
            "missed_at_retrieval": retrieval["missed_at_retrieval"],
            "uses_full_retrieval_set": retrieval["uses_full_retrieval_set"],
            "req_precision": generation["req_precision"],
            "req_recall": generation["req_recall"],
            "req_f1": generation["req_f1"],
            "right_recall": round(right_recall, 2),
            "predicted_reqs": generation["predicted_reqs"],
            "expected_reqs": generation["expected_reqs"],
            "missed_reqs": generation["missed_reqs"],
        })

    if not results:
        print(f"No output files found in {output_dir}/. Run run_evaluation.py first.")
        return

    print(f"\nScoring results from: {output_dir}/\n")
    print(f"{'ID':<6} {'Risk':<8} {'RiskOK':<8} {'Ret R':<8} {'Gen R':<8} {'Gen P':<8} {'Gen F1':<8} {'Right R':<8}")
    print("-" * 72)
    for r in results:
        print(
            f"{r['id']:<6} {r['risk_level']:<8} {'YES' if r['risk_match'] else 'NO':<8} "
            f"{r['retrieval_recall']:<8} {r['req_recall']:<8} {r['req_precision']:<8} "
            f"{r['req_f1']:<8} {r['right_recall']:<8}"
        )

    avg_retrieval_recall = sum(r["retrieval_recall"] for r in results) / len(results)
    avg_generation_recall = sum(r["req_recall"] for r in results) / len(results)
    avg_precision = sum(r["req_precision"] for r in results) / len(results)
    avg_f1 = sum(r["req_f1"] for r in results) / len(results)
    avg_right_recall = sum(r["right_recall"] for r in results) / len(results)
    risk_accuracy = sum(1 for r in results if r["risk_match"]) / len(results)

    print(f"\nAGGREGATE METRICS ({len(results)} proposals):")
    print(f"  Risk Level Accuracy:          {risk_accuracy:.0%}")
    print(f"  Retrieval Requirement Recall: {avg_retrieval_recall:.2f}  (KG surfaced expected reqs)")
    print(f"  Generation Requirement Recall:{avg_generation_recall:.2f}  (LLM cited expected reqs)")
    print(f"  Generation Requirement Precision:{avg_precision:.2f}")
    print(f"  Generation Requirement F1:    {avg_f1:.2f}")
    print(f"  Charter Rights Recall:        {avg_right_recall:.2f}")
    print(
        "\n  Retrieval vs generation recall separates KG retrieval quality from LLM citation "
        "behaviour (Gao et al., 2023, arXiv:2312.10997)."
    )

    print_confusion_matrix(results_for_matrix)
    print_requirement_coverage(output_dir, ALL_REQ_IDS)

    scores_path = os.path.join(output_dir, "precision_recall_scores.json")
    with open(scores_path, "w") as f:
        json.dump({
            "output_dir": output_dir,
            "aggregate": {
                "risk_accuracy": risk_accuracy,
                "retrieval_req_recall": avg_retrieval_recall,
                "generation_req_recall": avg_generation_recall,
                "generation_req_precision": avg_precision,
                "generation_req_f1": avg_f1,
                "right_recall": avg_right_recall,
            },
            "per_proposal": results,
        }, f, indent=2)

    print(f"\nSaved to {scores_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score evaluation outputs")
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory containing P*_full.json files (default: outputs)",
    )
    args = parser.parse_args()
    score_all(args.output_dir)
