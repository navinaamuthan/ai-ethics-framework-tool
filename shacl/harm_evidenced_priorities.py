"""Derive SHACL rule priorities from incident evidence in the KG."""
import requests, math

EP = "http://localhost:7200/repositories/ai-ethics-kg"
r = requests.post(EP, data={"query": """
PREFIX : <https://w3id.org/aief/>
SELECT ?right (COUNT(DISTINCT ?i) AS ?n) WHERE {
  ?i a :Incident ; :impactsRight ?right . } GROUP BY ?right ORDER BY DESC(?n)"""},
  headers={"Accept": "application/sparql-results+json"})
rows = r.json()["results"]["bindings"]

counts = {b["right"]["value"].rsplit("/",1)[-1]: int(b["n"]["value"]) for b in rows}
mx = max(counts.values())
# tiers: top third of incident evidence -> priority 1; middle -> 2; low/none -> 3
def tier(n): return 1 if n >= mx*2/3 else (2 if n >= mx/3 else 3)

print("% Harm-evidenced priorities — generated from incident in-degree, "
      f"max evidence = {mx} incidents")
print("@prefix aiefsh: <https://w3id.org/aief/shapes#> .")
print("@prefix aief:   <https://w3id.org/aief/> .\n")
for right, n in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"aief:{right} aiefsh:harmEvidence {n} ; aiefsh:evidencedPriority {tier(n)} .")
