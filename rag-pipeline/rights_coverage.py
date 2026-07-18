"""Fundamental Rights Coverage — the research plan's primary metric.
coverage = |rights addressed by system ∩ expected rights| / |expected rights|

Uses synthetic_proposals.PROPOSALS (same GT as score_evaluation), not ragas_metrics.
"""
import json, re, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from synthetic_proposals import PROPOSALS

SRC = Path(__file__).parent.parent / "evaluation/results/llama-3.3-70b"

def to_article(s):
    """Art8_DataProtection / Article 8 / Article8 -> Article8"""
    m = re.search(r"(?:Article\s*|Art)(\d+)", str(s))
    return f"Article{m.group(1)}" if m else None

rows, covs = [], []
for gt in sorted(PROPOSALS, key=lambda p: p["id"]):
    pid = gt["id"]
    f = SRC / f"{pid}_full.json"
    if not f.exists(): continue
    d = json.load(open(f))
    addressed = {to_article(r.get("article","")) for r in d["assessment"].get("charter_rights_at_risk", [])} - {None}
    expected = {to_article(r) for r in gt["expected_rights"]} - {None}
    if not expected:
        rows.append((pid, "n/a (no rights expected)", sorted(addressed))); continue
    cov = len(addressed & expected) / len(expected)
    covs.append(cov)
    missed = expected - addressed
    rows.append((pid, f"{cov:.2f}", f"missed: {sorted(missed)}" if missed else "full"))

for r in rows: print(*r, sep="  |  ")
mean = sum(covs)/len(covs)
print(f"\nMean Fundamental Rights Coverage: {mean:.3f} (n={len(covs)})")
boot = [sum(random.choices(covs, k=len(covs)))/len(covs) for _ in range(10000)]
boot.sort()
print(f"95% bootstrap CI: [{boot[249]:.3f}, {boot[9749]:.3f}]")
print("Plan benchmark was >=0.85 vs baseline documentation; report against reference annotations with that caveat.")
