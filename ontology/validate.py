from rdflib import Graph
g = Graph()
g.parse("ai-ethics-final.ttl", format="turtle")
print(f"Valid. Total triples: {len(g)}")
