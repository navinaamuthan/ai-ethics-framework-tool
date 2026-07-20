"""Score second-annotator agreement from the two returned annotation sheets.

Computes three kappas:
  1. Annotator A (Aditya Rajput)              vs. ground truth
  2. Annotator B (Shravani Chandrasekhar Chougule) vs. ground truth
  3. Annotator A                              vs. Annotator B  (true inter-rater reliability)
"""
from collections import Counter
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from synthetic_proposals import PROPOSALS

# --- Annotator A: Aditya Rajput, 19.06.2026 ---
SECOND_A = {
    "P01": {"risk": "High", "rights": {"Article21", "Article35", "Article8", "Article47"}},
    "P02": {"risk": "High", "rights": {"Article21", "Article48", "Article8"}},
    "P03": {"risk": "High", "rights": {"Article7", "Article8", "Article21", "Article47"}},
    "P04": {"risk": "High", "rights": {"Article21", "Article15", "Article8"}},
    "P05": {"risk": "High", "rights": {"Article35", "Article21", "Article8"}},
    "P06": {"risk": "High", "rights": {"Article24", "Article7", "Article8", "Article21"}},
    "P07": {"risk": "Low", "rights": {"Article8"}},
    "P08": {"risk": "High", "rights": {"Article35", "Article8", "Article7"}},
    "P09": {"risk": "Medium", "rights": {"Article14", "Article8"}},
    "P10": {"risk": "High", "rights": {"Article11", "Article7", "Article8"}},
    "P11": {"risk": "High", "rights": {"Article14", "Article21", "Article47"}},
    "P12": {"risk": "High", "rights": {"Article35", "Article21", "Article8"}},
    "P13": {"risk": "Low", "rights": set()},
    "P14": {"risk": "Low", "rights": set()},
    "P15": {"risk": "Low", "rights": set()},
    "P16": {"risk": "Low", "rights": set()},
    "P17": {"risk": "Medium", "rights": {"Article11", "Article12"}},
    "P18": {"risk": "High", "rights": {"Article7", "Article8", "Article17", "Article47"}},
    "P19": {"risk": "High", "rights": {"Article7", "Article8", "Article35"}},
    "P20": {"risk": "High", "rights": {"Article7", "Article8", "Article31", "Article1"}},
}

# --- Annotator B: Shravani Chandrasekhar Chougule, 17.06.2026 ---
SECOND_B = {
    "P01": {"risk": "High", "rights": {"Article21", "Article35", "Article8", "Article47"}},
    "P02": {"risk": "High", "rights": {"Article21", "Article35", "Article8", "Article47"}},
    "P03": {"risk": "High", "rights": {"Article7", "Article8", "Article21", "Article47"}},
    "P04": {"risk": "High", "rights": {"Article21", "Article15", "Article34", "Article8"}},
    "P05": {"risk": "High", "rights": {"Article35", "Article21", "Article8"}},
    "P06": {"risk": "High", "rights": {"Article24", "Article7", "Article8", "Article21"}},
    "P07": {"risk": "Medium", "rights": {"Article8", "Article21"}},
    "P08": {"risk": "High", "rights": {"Article35", "Article8", "Article7"}},
    "P09": {"risk": "Medium", "rights": {"Article8", "Article21", "Article14"}},
    "P10": {"risk": "High", "rights": {"Article11", "Article7", "Article8"}},
    "P11": {"risk": "High", "rights": {"Article14", "Article21", "Article47"}},
    "P12": {"risk": "High", "rights": {"Article35", "Article21", "Article8"}},
    "P13": {"risk": "Low", "rights": set()},
    "P14": {"risk": "Low", "rights": set()},
    "P15": {"risk": "Low", "rights": set()},
    "P16": {"risk": "Low", "rights": set()},
    "P17": {"risk": "Medium", "rights": {"Article11", "Article12", "Article21"}},
    "P18": {"risk": "High", "rights": {"Article7", "Article8", "Article17", "Article47"}},
    "P19": {"risk": "High", "rights": {"Article8", "Article7", "Article21", "Article35"}},
    "P20": {"risk": "High", "rights": {"Article7", "Article8", "Article31", "Article1"}},
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


def risk_kappa(annot, label):
    pairs = [(GT[p]["risk_level"], annot[p]["risk"]) for p in annot]
    k = kappa(pairs)
    print(f"  Risk-label Cohen's kappa ({label}, n={len(pairs)}): {k:.3f}")
    return k


def rights_kappa(annot_a, annot_b, label):
    """Binary per-article agreement between two rights sets, keyed by proposal id.

    annot_b may be an annotator dict (each value has a "rights" set) or GT
    (each value has "expected_rights" — pass the module-level GT dict directly).
    """
    is_gt = annot_b is GT

    all_arts = set()
    for g in PROPOSALS:
        all_arts |= {to_art(a) for a in g["expected_rights"]}
    for s in annot_a.values():
        all_arts |= {to_art(a) for a in s["rights"]}
    if not is_gt:
        for s in annot_b.values():
            all_arts |= {to_art(a) for a in s["rights"]}
    all_arts.discard(None)
    all_arts = sorted(all_arts)

    pairs = []
    for pid in annot_a:
        if pid not in annot_b and not is_gt:
            continue
        a_set = {to_art(x) for x in annot_a[pid]["rights"]}
        b_set = {to_art(x) for x in GT[pid]["expected_rights"]} if is_gt else {to_art(x) for x in annot_b[pid]["rights"]}
        for art in all_arts:
            pairs.append((art in a_set, art in b_set))

    k = kappa(pairs)
    print(f"  Rights binary kappa ({label}, {len(pairs)} decisions): {k:.3f}")
    return k


if not SECOND_A and not SECOND_B:
    print("SECOND_A / SECOND_B are empty — paste annotator answers into annotator_agreement.py then re-run.")
    sys.exit(0)

print("=== Annotator A (Aditya Rajput) vs. ground truth ===")
risk_kappa(SECOND_A, "A vs GT")
rights_kappa(SECOND_A, GT, "A vs GT")

print("\n=== Annotator B (Shravani Chandrasekhar Chougule) vs. ground truth ===")
risk_kappa(SECOND_B, "B vs GT")
rights_kappa(SECOND_B, GT, "B vs GT")

print("\n=== Annotator A vs. Annotator B (inter-rater reliability) ===")
risk_pairs_ab = [(SECOND_A[p]["risk"], SECOND_B[p]["risk"]) for p in SECOND_A if p in SECOND_B]
print(f"  Risk-label Cohen's kappa (A vs B, n={len(risk_pairs_ab)}): {kappa(risk_pairs_ab):.3f}")
rights_kappa(SECOND_A, SECOND_B, "A vs B")
