"""SHACL condition evaluated on all 20 synthetic proposals:
per-dimension flags vs expected_rights -> precision/recall."""
import json, re, sys
from pathlib import Path
import rdflib
from pyshacl import validate

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "rag-pipeline"))
from text_to_description import describe
from synthetic_proposals import PROPOSALS

HERE = Path(__file__).parent
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
AIEFSH = rdflib.Namespace("https://w3id.org/aief/shapes#")
shapes = rdflib.Graph().parse(HERE / "aief-risk-shapes.ttl", format="turtle")
dim_of = {s: shapes.value(s, AIEFSH.riskDimension)
          for s in shapes.subjects(rdflib.RDF.type, SH.NodeShape)}

def art(iri):                       # Art8_DataProtection -> Article8
    m = re.search(r"Art(\d+)", str(iri)); return f"Article{m.group(1)}" if m else None

SRC = HERE.parent / "evaluation/results/llama-3.3-70b"
precs, recs, rows = [], [], []
for gt in sorted(PROPOSALS, key=lambda p: p["id"]):
    pid = gt["id"]
    f = SRC / f"{pid}_full.json"
    if not f.exists(): continue
    text = json.load(open(f))["proposal_text"]
    data = rdflib.Graph().parse(data=describe(text), format="turtle")
    _, rep, _ = validate(data, shacl_graph=shapes, advanced=True, inference="none")
    flagged = {art(dim_of.get(rep.value(r, SH.sourceShape)))
               for r in rep.subjects(rdflib.RDF.type, SH.ValidationResult)}
    flagged.discard(None)
    expected = {art(r) for r in gt["expected_rights"]} - {None}
    tp = len(flagged & expected)
    p = tp/len(flagged) if flagged else (1.0 if not expected else 0.0)
    r = tp/len(expected) if expected else 1.0
    precs.append(p); recs.append(r)
    rows.append((pid, sorted(flagged), f"P={p:.2f}", f"R={r:.2f}"))

for row in rows: print(*row, sep="  ")
print(f"\nSHACL condition: mean precision={sum(precs)/len(precs):.3f}, "
      f"mean recall={sum(recs)/len(recs):.3f} (n={len(precs)})")
print("Compare in the RQ2 table against RAG rights-coverage (recall-style) and note:")
print("SHACL recall is bounded by 27 rules (21 atomic + 6 compound) / 20 of 22 Charter")
print("dimensions in the KG. The 6 compound rules do not change this dimension-level")
print("P/R (they escalate priority within already-covered dimensions rather than adding")
print("new dimension coverage) -- their contribution is qualitative: auditable conjunctive")
print("escalation logic, demonstrated separately (see shacl/README.md and shacl/aief-risk-shapes.ttl).")
print("(Art13 Freedom of Arts/Science and Art20 Equality Before the Law are unruled --")
print("no reliable keyword signal distinguishes them from adjacent ruled dimensions).")
