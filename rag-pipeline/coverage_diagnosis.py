"""Classify every missed expected right: retrieval-stage vs generation-stage.
Uses synthetic_proposals.PROPOSALS (same GT as score_evaluation)."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from synthetic_proposals import PROPOSALS

SRC = Path(__file__).parent.parent / "evaluation/results/llama-3.3-70b"

def to_article(s):
    m = re.search(r"(?:Article\s*|Art)(\d+)", str(s))
    return f"Article{m.group(1)}" if m else None

ret_miss, gen_miss = [], []
sample = json.load(open(SRC / "P01_full.json"))
print("DEBUG matched_rights sample:", sample.get("matched_rights"), "\n")

for gt in sorted(PROPOSALS, key=lambda p: p["id"]):
    pid = gt["id"]
    f = SRC / f"{pid}_full.json"
    if not f.exists(): continue
    d = json.load(open(f))
    retrieved = {to_article(r) for r in d.get("matched_rights", [])} - {None}
    cited = {to_article(r.get("article")) for r in d["assessment"].get("charter_rights_at_risk", [])} - {None}
    expected = {to_article(r) for r in gt["expected_rights"]} - {None}
    for exp in expected - cited:
        (gen_miss if exp in retrieved else ret_miss).append((pid, exp))

t = len(ret_miss) + len(gen_miss)
print(f"Total misses: {t}")
print(f"  retrieval-stage (never matched): {len(ret_miss)} ({100*len(ret_miss)//max(t,1)}%) -> {ret_miss}")
print(f"  generation-stage (matched, not cited): {len(gen_miss)} ({100*len(gen_miss)//max(t,1)}%) -> {gen_miss}")
