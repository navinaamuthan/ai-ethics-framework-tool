"""Formal competency-question suite (Gruninger & Fox method).
20 CQs -> SPARQL, each with an explicit pass criterion:
  'nonzero'      : query must return >= 1 row
  ('count', n)   : query must return exactly n rows
  ('arts', {..}) : article numbers in results must equal the given set
Run against the live KG; prints pass/fail table + LaTeX rows.
"""
import re, requests

EP = "http://localhost:7200/repositories/ai-ethics-kg"
P = "PREFIX : <https://w3id.org/aief/>\nPREFIX owl: <http://www.w3.org/2002/07/owl#>\n"

def q(query):
    r = requests.post(EP, data={"query": P + query},
                      headers={"Accept": "application/sparql-results+json"})
    r.raise_for_status()
    return r.json()["results"]["bindings"]

CQS = [
 ("CQ1", "Which requirements govern consent?",
  """SELECT DISTINCT ?id WHERE { ?r a :Requirement ; :requirementID ?id ; :requirementText ?t .
     FILTER(CONTAINS(LCASE(?t), "consent")) }""", "nonzero"),
 ("CQ2", "Which incidents impact non-discrimination (Art 21)?",
  """SELECT DISTINCT ?i WHERE { ?i a :Incident ; :impactsRight ?rt .
     FILTER(CONTAINS(STR(?rt), "Art21")) }""", "nonzero"),
 ("CQ3", "Which requirements map to data protection (Art 8)?",
  """SELECT DISTINCT ?r WHERE { ?r a :Requirement ; :mapsToRight ?rt .
     FILTER(CONTAINS(STR(?rt), "Art8_")) }""", "nonzero"),
 ("CQ4", "Which incidents evidence requirement R085?",
  """SELECT ?i WHERE { ?i :supportsRequirement :R085 }""", "nonzero"),
 ("CQ5", "Which frameworks impose consent obligations?",
  """SELECT DISTINCT ?fw WHERE { ?r a :Requirement ; :belongsToFramework ?fw ; :requirementText ?t .
     FILTER(CONTAINS(LCASE(?t), "consent")) }""", "nonzero"),
 ("CQ6", "Which incident-impacted rights lack any requirement coverage?",
  """SELECT DISTINCT ?rt WHERE { ?i a :Incident ; :impactsRight ?rt .
     FILTER NOT EXISTS { ?r a :Requirement ; :mapsToRight ?rt } }""",
  ("arts", {"13", "15", "48"})),
 ("CQ7", "Which frameworks cover the rights of the child (Art 24)?",
  """SELECT DISTINCT ?fw WHERE { ?r a :Requirement ; :mapsToRight ?rt ; :belongsToFramework ?fw .
     FILTER(CONTAINS(STR(?rt), "Art24")) }""", ("count", 1)),
 ("CQ8", "How many mandatory requirements does each framework impose?",
  """SELECT ?fw (COUNT(?r) AS ?n) WHERE { ?r a :Requirement ; :isMandatory true ;
     :belongsToFramework ?fw } GROUP BY ?fw""", ("count", 4)),
 ("CQ9", "Which requirements demand a specific evidence artifact?",
  """SELECT DISTINCT ?r WHERE { ?r a :Requirement ; :requiresEvidence ?e }""", "nonzero"),
 ("CQ10", "Which incidents involve computer-vision capabilities?",
  """SELECT ?i WHERE { ?i a :Incident ; :aiCapability ?c . FILTER(CONTAINS(?c, "CV")) }""", "nonzero"),
 ("CQ11", "Which requirements cite a GDPR legal basis?",
  """SELECT ?r WHERE { ?r a :Requirement ; :legalBasis ?b . FILTER(CONTAINS(?b, "GDPR")) }""", "nonzero"),
 ("CQ12", "Which rights are impacted by three or more incidents?",
  """SELECT ?rt (COUNT(?i) AS ?n) WHERE { ?i a :Incident ; :impactsRight ?rt }
     GROUP BY ?rt HAVING(COUNT(?i) >= 3)""", "nonzero"),
 ("CQ13", "Which requirements escalate to a higher review level?",
  """SELECT ?r WHERE { ?r :triggersReviewLevel ?l }""", "nonzero"),
 ("CQ14", "Which rights are covered by all four frameworks?",
  """SELECT ?rt WHERE { ?r a :Requirement ; :mapsToRight ?rt ; :belongsToFramework ?fw }
     GROUP BY ?rt HAVING(COUNT(DISTINCT ?fw) = 4)""", ("count", 8)),
 ("CQ15", "Which single incident impacts the most rights?",
  """SELECT ?i (COUNT(?rt) AS ?n) WHERE { ?i a :Incident ; :impactsRight ?rt }
     GROUP BY ?i ORDER BY DESC(?n) LIMIT 1""", ("count", 1)),
 ("CQ16", "Which requirements both map to a right and demand evidence?",
  """SELECT DISTINCT ?r WHERE { ?r a :Requirement ; :mapsToRight ?rt ; :requiresEvidence ?e }""", "nonzero"),
 ("CQ17", "How many requirements are deontic obligations?",
  """SELECT (COUNT(DISTINCT ?r) AS ?n) WHERE { ?r a :Obligation ; :requirementID ?id }""", "nonzero"),
 ("CQ18", "Which Charter rights are aligned with DPV?",
  """SELECT DISTINCT ?c WHERE { ?c owl:equivalentClass ?d .
     FILTER(STRSTARTS(STR(?c), "https://w3id.org/aief/Art")) }""", ("count", 15)),
 ("CQ19", "Which risk categories do incidents demonstrate?",
  """SELECT DISTINCT ?risk WHERE { ?i a :Incident ; :demonstratesRisk ?risk }""", "nonzero"),
 ("CQ20", "Which requirements have documented incident support and Charter grounding?",
  """SELECT DISTINCT ?r WHERE { ?i :supportsRequirement ?r . ?r :mapsToRight ?rt }""", "nonzero"),
]

def article_set(rows):
    arts = set()
    for b in rows:
        for v in b.values():
            m = re.search(r"Art(\d+)", v.get("value", ""))
            if m: arts.add(m.group(1))
    return arts

passed = 0
lines = []
for cid, question, query, crit in CQS:
    try:
        rows = q(query)
        if crit == "nonzero":
            ok, detail = len(rows) >= 1, f"{len(rows)} rows"
        elif crit[0] == "count":
            ok, detail = len(rows) == crit[1], f"{len(rows)} rows (expected {crit[1]})"
        elif crit[0] == "arts":
            got = article_set(rows)
            ok, detail = got == crit[1], f"articles {sorted(got)} (expected {sorted(crit[1])})"
    except Exception as e:
        ok, detail = False, f"ERROR {e}"
    passed += ok
    lines.append((cid, question, "PASS" if ok else "FAIL", detail))
    print(f"{cid:5s} {'PASS' if ok else 'FAIL':4s}  {question}  [{detail}]")

print(f"\n{passed}/{len(CQS)} competency questions pass")
with open(__file__.replace("competency_questions.py", "results/cq_table.tex"), "w") as f:
    f.write("\\begin{tabular}{llp{7cm}l}\n\\toprule\n\\textbf{CQ} & \\textbf{Result} & \\textbf{Question} & \\textbf{Detail} \\\\\n\\midrule\n")
    for cid, question, res, detail in lines:
        f.write(f"{cid} & {res} & {question} & {detail} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
print("LaTeX table -> analysis/results/cq_table.tex")
