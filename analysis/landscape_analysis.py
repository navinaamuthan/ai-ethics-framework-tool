"""RQ1 landscape analysis over the AIEF knowledge graph."""
import json, re, requests, os
from collections import defaultdict

EP = "http://localhost:7200/repositories/ai-ethics-kg"
A = "https://w3id.org/aief/"
OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)

def q(query):
    r = requests.post(EP, data={"query": "PREFIX : <%s>\n" % A + query},
                      headers={"Accept": "application/sparql-results+json"})
    r.raise_for_status()
    return r.json()["results"]["bindings"]

def local(iri): return iri.rsplit("/", 1)[-1]

# 1. Coverage matrix: requirements per right per framework
rows = q("""SELECT ?right ?fw (COUNT(DISTINCT ?r) AS ?n) WHERE {
  ?r a :Requirement ; :mapsToRight ?right ; :belongsToFramework ?fw .
} GROUP BY ?right ?fw""")
matrix = defaultdict(dict)
for b in rows:
    matrix[local(b["right"]["value"])][local(b["fw"]["value"])] = int(b["n"]["value"])

# 2. Incident evidence per right
rows = q("""SELECT ?right (COUNT(DISTINCT ?i) AS ?n) WHERE {
  ?i a :Incident ; :impactsRight ?right . } GROUP BY ?right""")
incident_evidence = {local(b["right"]["value"]): int(b["n"]["value"]) for b in rows}

# 3. THE GAP: rights with incidents but NO requirement coverage
rows = q("""SELECT ?right (COUNT(DISTINCT ?i) AS ?n) WHERE {
  ?i a :Incident ; :impactsRight ?right .
  FILTER NOT EXISTS { ?req a :Requirement ; :mapsToRight ?right }
} GROUP BY ?right ORDER BY DESC(?n)""")
harm_without_governance = [(local(b["right"]["value"]), int(b["n"]["value"])) for b in rows]

# 4. Reverse gap: covered rights with zero incident evidence
rows = q("""SELECT ?right (COUNT(DISTINCT ?req) AS ?n) WHERE {
  ?req a :Requirement ; :mapsToRight ?right .
  FILTER NOT EXISTS { ?i a :Incident ; :impactsRight ?right }
} GROUP BY ?right ORDER BY DESC(?n)""")
governance_without_harm = [(local(b["right"]["value"]), int(b["n"]["value"])) for b in rows]

# 5. Overlap distribution: rights covered by k frameworks
fw_count = {r: len(fws) for r, fws in matrix.items()}
overlap = defaultdict(list)
for r, k in fw_count.items(): overlap[k].append(r)

# 6. Top harm-evidenced requirements
rows = q("""SELECT ?req ?id (COUNT(DISTINCT ?i) AS ?n) WHERE {
  ?i a :Incident ; :supportsRequirement ?req . ?req :requirementID ?id .
} GROUP BY ?req ?id ORDER BY DESC(?n) LIMIT 15""")
top_evidenced_reqs = [(b["id"]["value"], int(b["n"]["value"])) for b in rows]

FWS = ["REAMS", "EUAIAct", "HorizonEurope", "ACMConference"]
report = {
    "coverage_matrix": {r: {fw: matrix[r].get(fw, 0) for fw in FWS} for r in sorted(matrix)},
    "incident_evidence_per_right": dict(sorted(incident_evidence.items(), key=lambda x: -x[1])),
    "harm_without_governance": harm_without_governance,
    "governance_without_harm": governance_without_harm,
    "overlap_distribution": {str(k): sorted(v) for k, v in sorted(overlap.items())},
    "top_harm_evidenced_requirements": top_evidenced_reqs,
}
json.dump(report, open(f"{OUT}/landscape_report.json", "w"), indent=2)

# Console summary + LaTeX table
print("=== HARM WITHOUT GOVERNANCE (rights with incidents, zero requirements) ===")
for r, n in harm_without_governance: print(f"  {r}: {n} incident(s), 0 requirements")
print("\n=== GOVERNANCE WITHOUT DOCUMENTED HARM ===")
for r, n in governance_without_harm: print(f"  {r}: {n} requirement(s), 0 incidents")
print("\n=== OVERLAP: rights covered by k frameworks ===")
for k, rights in sorted(overlap.items()): print(f"  {k}/4 frameworks: {len(rights)} rights -> {', '.join(sorted(rights))}")
print("\n=== TOP HARM-EVIDENCED REQUIREMENTS ===")
for rid, n in top_evidenced_reqs[:10]: print(f"  {rid}: supported by {n} incidents")

with open(f"{OUT}/coverage_matrix.tex", "w") as f:
    f.write("\\begin{tabular}{lrrrrr}\n\\toprule\n\\textbf{Charter right} & \\textbf{REAMS} & \\textbf{AI Act} & \\textbf{Horizon} & \\textbf{ACM} & \\textbf{Incidents} \\\\\n\\midrule\n")
    for r in sorted(matrix, key=lambda x: int(re.search(r'Art(\d+)', x).group(1)) if re.search(r'Art(\d+)', x) else 99):
        c = report["coverage_matrix"][r]
        f.write(f"{r.replace('_', ' ')} & {c['REAMS']} & {c['EUAIAct']} & {c['HorizonEurope']} & {c['ACMConference']} & {incident_evidence.get(r, 0)} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
print(f"\nSaved: {OUT}/landscape_report.json and coverage_matrix.tex")
