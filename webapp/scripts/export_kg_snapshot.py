# export_kg_snapshot.py — run from ~/Dissertation/ethics-rag/ with GraphDB Desktop running.
# Copy this file there, then:  python export_kg_snapshot.py
# Then copy the output to aief-app/lib/kg-snapshot.json
import json
from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT = "http://localhost:7200/repositories/ai-ethics"
AIEF = "https://w3id.org/aief/"

def query(q):
    sw = SPARQLWrapper(ENDPOINT)
    sw.setQuery(q)
    sw.setReturnFormat(JSON)
    return sw.query().convert()["results"]["bindings"]

def get_all_requirements():
    rows = query(f"""
    PREFIX aief: <{AIEF}>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?id ?text ?framework ?tier (GROUP_CONCAT(DISTINCT ?art; separator="|") AS ?arts)
           (GROUP_CONCAT(DISTINCT ?tag; separator="|") AS ?tags)
    WHERE {{
      ?req a aief:Requirement ;
           aief:requirementID ?id ;
           aief:requirementText ?text ;
           aief:belongsToFramework ?fw ;
           aief:hasTier ?tierNode .
      ?fw rdfs:label ?framework .
      ?tierNode rdfs:label ?tier .
      OPTIONAL {{ ?req aief:mapsToRight ?right . ?right aief:articleNumber ?art . }}
      OPTIONAL {{ ?req aief:hasKeyword ?tag . }}
    }} GROUP BY ?id ?text ?framework ?tier
    """)
    # NOTE: adjust property names above to match your ontology exactly
    fw_map = {"REAMS": "REAMS", "EU AI Act": "EUAIAct", "Horizon Europe": "HorizonEurope", "ACM/NeurIPS": "ACMConference"}
    out = []
    for r in rows:
        out.append({
            "id": r["id"]["value"],
            "text": r["text"]["value"],
            "framework": fw_map.get(r["framework"]["value"], r["framework"]["value"]),
            "tier": r["tier"]["value"],
            "charter_articles": [a for a in r.get("arts", {}).get("value", "").split("|") if a],
            "tags": [t for t in r.get("tags", {}).get("value", "").split("|") if t],
        })
    return out

def get_all_incidents():
    rows = query(f"""
    PREFIX aief: <{AIEF}>
    SELECT ?id ?title ?desc (GROUP_CONCAT(DISTINCT ?tag; separator="|") AS ?tags)
    WHERE {{
      ?inc a aief:AIIncident ;
           aief:incidentID ?id ;
           aief:incidentTitle ?title ;
           aief:incidentDescription ?desc .
      OPTIONAL {{ ?inc aief:hasKeyword ?tag . }}
    }} GROUP BY ?id ?title ?desc
    """)
    return [{
        "id": r["id"]["value"],
        "title": r["title"]["value"],
        "description": r["desc"]["value"],
        "tags": [t for t in r.get("tags", {}).get("value", "").split("|") if t],
    } for r in rows]

if __name__ == "__main__":
    snapshot = {"requirements": get_all_requirements(), "incidents": get_all_incidents()}
    with open("kg-snapshot.json", "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Exported {len(snapshot['requirements'])} requirements, {len(snapshot['incidents'])} incidents")
