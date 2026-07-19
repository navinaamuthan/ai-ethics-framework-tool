"""Ablation: regex bridge vs LLM-structured-extraction bridge, scored
identically via evaluate_shacl.py's methodology (SHACL precision/recall
against expected_rights). Reports both directions of the trade-off:
recall gained vs LLM-dependence reintroduced at the extraction stage.
"""
import json, sys, time
from pathlib import Path
import rdflib
from pyshacl import validate
from openai import OpenAI
import os
import re

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "rag-pipeline"))
from synthetic_proposals import PROPOSALS
import text_to_description as regex_bridge
import text_to_description_llm as llm_bridge

SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
AIEFSH = rdflib.Namespace("https://w3id.org/aief/shapes#")
shapes = rdflib.Graph().parse(HERE / "aief-risk-shapes.ttl", format="turtle")
dim_of = {s: shapes.value(s, AIEFSH.riskDimension)
          for s in shapes.subjects(rdflib.RDF.type, SH.NodeShape)}


def art(iri):
    m = re.search(r"Art(\d+)", str(iri))
    return f"Article{m.group(1)}" if m else None


def score(ttl_text, expected):
    data = rdflib.Graph().parse(data=ttl_text, format="turtle")
    _, rep, _ = validate(data, shacl_graph=shapes, advanced=True, inference="none")
    flagged = {art(dim_of.get(rep.value(r, SH.sourceShape)))
               for r in rep.subjects(rdflib.RDF.type, SH.ValidationResult)}
    flagged.discard(None)
    tp = len(flagged & expected)
    p = tp / len(flagged) if flagged else (1.0 if not expected else 0.0)
    r = tp / len(expected) if expected else 1.0
    return p, r, flagged


def main():
    client = OpenAI(api_key=os.environ["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
    rows = []
    for pid, gt in sorted(PROPOSALS_DICT().items()):
        text = gt["proposal_text"]
        expected = {a.replace("Art", "Article") if a.startswith("Art") and "_" not in a else a
                    for a in gt["expected_rights"]}
        # normalize expected_rights format (may be "Art21_NonDiscrimination" style)
        expected = {re.sub(r"^Art(\d+).*", r"Article\1", a) for a in gt["expected_rights"]}

        regex_ttl = regex_bridge.describe(text)
        rp, rr, _ = score(regex_ttl, expected)

        try:
            llm_facts = llm_bridge.extract(text, client)
            llm_ttl = llm_bridge.to_ttl(llm_facts)
            lp, lr, _ = score(llm_ttl, expected)
        except Exception as e:
            print(f"  [{pid}] LLM bridge failed: {e}")
            lp, lr = None, None
        time.sleep(2)

        rows.append((pid, rp, rr, lp, lr))
        print(f"{pid}  regex P={rp:.2f} R={rr:.2f}  |  llm P={lp if lp is None else f'{lp:.2f}'} R={lr if lr is None else f'{lr:.2f}'}")

    valid = [r for r in rows if r[3] is not None]
    n = len(valid)
    if n:
        print(f"\n=== AGGREGATE (n={n} with successful LLM extraction; {len(rows)-n} failed) ===")
        print(f"regex bridge: mean P={sum(r[1] for r in rows)/len(rows):.3f} R={sum(r[2] for r in rows)/len(rows):.3f} (n={len(rows)})")
        print(f"llm bridge:   mean P={sum(r[3] for r in valid)/n:.3f} R={sum(r[4] for r in valid)/n:.3f} (n={n})")
    json.dump([{"id": r[0], "regex_p": r[1], "regex_r": r[2], "llm_p": r[3], "llm_r": r[4]} for r in rows],
              open(HERE / "bridge_ablation_results.json", "w"), indent=2)


def PROPOSALS_DICT():
    return {p["id"]: p for p in PROPOSALS}


if __name__ == "__main__":
    main()
