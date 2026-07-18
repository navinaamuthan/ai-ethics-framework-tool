"""Exact McNemar test: 8B vs 70B risk-label correctness (synthetic_proposals GT)."""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from synthetic_proposals import PROPOSALS

ROOT = Path(__file__).parent.parent / "evaluation/results"
b = c = 0  # b: 8B right & 70B wrong; c: 70B right & 8B wrong
for gt in PROPOSALS:
    pid = gt["id"]
    exp = gt["risk_level"]
    p8 = json.load(open(ROOT / "llama-3.1-8b" / f"{pid}_full.json"))["assessment"]["overall_risk_level"]
    p70 = json.load(open(ROOT / "llama-3.3-70b" / f"{pid}_full.json"))["assessment"]["overall_risk_level"]
    ok8, ok70 = (p8 == exp), (p70 == exp)
    if ok8 and not ok70: b += 1
    if ok70 and not ok8: c += 1
    if ok8 != ok70:
        print(f"  discordant {pid}: exp={exp} 8B={p8} 70B={p70}")

n = b + c
p = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / 2**n * 2 if n else 1.0
print(f"\nMcNemar exact p = {min(p,1):.4f} (discordant pairs: b={b} 8B+/70B- vs c={c} 70B+/8B-)")
print("Report as directional-trend caveat when p is not significant.")
