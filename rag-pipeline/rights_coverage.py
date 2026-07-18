"""Fundamental Rights Coverage — the research plan's primary metric.
coverage = |rights addressed by system ∩ expected rights| / |expected rights|"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ragas_metrics import GROUND_TRUTH_DATA

SRC = Path(__file__).parent.parent / "evaluation/results/llama-3.3-70b"
norm = lambda s: re.sub(r"\s+", "", s)  # "Article 8" -> "Article8"

rows, covs = [], []
for pid, gt in sorted(GROUND_TRUTH_DATA.items()):
    f = SRC / f"{pid}_full.json"
    if not f.exists(): continue
    d = json.load(open(f))
    addressed = {norm(r.get("article","")) for r in d["assessment"].get("charter_rights_at_risk", [])}
    expected = set(gt["expected_rights"])
    if not expected:
        rows.append((pid, "n/a (no rights expected)", addressed)); continue
    cov = len(addressed & expected) / len(expected)
    covs.append(cov)
    missed = expected - addressed
    rows.append((pid, f"{cov:.2f}", f"missed: {sorted(missed)}" if missed else "full"))

for r in rows: print(*r, sep="  |  ")
print(f"\nMean Fundamental Rights Coverage: {sum(covs)/len(covs):.3f} (n={len(covs)})")
print("Plan benchmark was >=0.85 vs baseline documentation; report against reference annotations with that caveat.")
