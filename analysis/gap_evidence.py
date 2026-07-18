"""For each harm-without-governance right: list its incidents, so each gap
can be manually verified against the four source framework documents."""
import requests, json

EP = "http://localhost:7200/repositories/ai-ethics-kg"
def q(query):
    r = requests.post(EP, data={"query": "PREFIX : <https://w3id.org/aief/>\n"+query},
                      headers={"Accept": "application/sparql-results+json"})
    return r.json()["results"]["bindings"]

gaps = q("""SELECT DISTINCT ?right WHERE {
  ?i a :Incident ; :impactsRight ?right .
  FILTER NOT EXISTS { ?req a :Requirement ; :mapsToRight ?right } }""")
report = {}
for b in gaps:
    right = b["right"]["value"].rsplit("/",1)[-1]
    print(f"\n### {right}")
    incs = []
    for inc in q(f"""SELECT ?id ?title WHERE {{
        ?i a :Incident ; :impactsRight <https://w3id.org/aief/{right}> ;
           :incidentID ?id ; :incidentTitle ?title }}"""):
        line = f"{inc['id']['value']}: {inc['title']['value']}"
        print(f"  {line}")
        incs.append({"id": inc["id"]["value"], "title": inc["title"]["value"]})
    report[right] = incs

out = __file__.replace("gap_evidence.py", "results/gap_evidence.json")
json.dump(report, open(out, "w"), indent=2)
print(f"\nSaved {out}")
