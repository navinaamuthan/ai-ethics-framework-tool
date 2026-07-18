"""Score second-annotator agreement once SECOND is filled from annotation_sheet.md."""
from collections import Counter
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from synthetic_proposals import PROPOSALS

# Fill in from the returned sheet (ArtNN or ArticleNN both OK):
SECOND = {
    # "P01": {"risk": "High", "rights": {"Article21", "Article8", "Article35"}},
}

GT = {p["id"]: p for p in PROPOSALS}


def to_art(s):
    import re
    m = re.search(r"(?:Article\s*|Art)(\d+)", str(s))
    return f"Article{m.group(1)}" if m else None


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return float("nan")
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n**2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


if not SECOND:
    print("SECOND dict is empty — paste annotator answers into annotator_agreement.py then re-run.")
    sys.exit(0)

ALL_ARTS = sorted(
    {to_art(a) for g in PROPOSALS for a in g["expected_rights"]}
    | {to_art(a) for s in SECOND.values() for a in s["rights"]}
    - {None}
)

risk_pairs = [(GT[p]["risk_level"], SECOND[p]["risk"]) for p in SECOND]
print(f"Risk-label Cohen's kappa (n={len(risk_pairs)}): {kappa(risk_pairs):.3f}")

rights_pairs = [
    (art in {to_art(x) for x in GT[p]["expected_rights"]}, art in {to_art(x) for x in SECOND[p]["rights"]})
    for p in SECOND
    for art in ALL_ARTS
]
print(f"Rights binary kappa ({len(rights_pairs)} decisions): {kappa(rights_pairs):.3f}")
