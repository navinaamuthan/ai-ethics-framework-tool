"""Find Charter rights with more than one IRI (dual-IRI artifacts)."""
import requests, re
from collections import defaultdict
EP = "http://localhost:7200/repositories/ai-ethics-kg"
rows = requests.post(EP, data={"query":"""PREFIX : <https://w3id.org/aief/>
SELECT DISTINCT ?r WHERE { { ?x :mapsToRight ?r } UNION { ?x :impactsRight ?r } }"""},
  headers={"Accept":"application/sparql-results+json"}).json()["results"]["bindings"]
byart = defaultdict(list)
for b in rows:
    local = b["r"]["value"].rsplit("/",1)[-1]
    m = re.match(r"Art(\d+)", local)
    if m: byart[m.group(1)].append(local)
print("=== Dual-IRI scan ===")
dups = 0
for art, names in sorted(byart.items(), key=lambda x:int(x[0])):
    uniq = sorted(set(names))
    if len(uniq) > 1:
        dups += 1
        print(f"Article {art}: DUPLICATE IRIs -> {uniq}")
    else:
        print(f"Article {art}: ok -> {uniq[0]}")
print(f"\nDuplicate articles: {dups}")
