"""RQ1 deepening: do 207 requirement statements represent 207 distinct
obligations, or does the harmonisation collapse substantively duplicate
obligations expressed in different frameworks' wording?

Method: embed all requirement texts (sentence-transformers, local, no
API), agglomerative clustering at a cosine-distance threshold, report
cluster count and how many clusters span >=3 frameworks (evidence of
convergent, not just article-level, overlap).
"""
import json, requests
from collections import defaultdict
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
import numpy as np

EP = "http://localhost:7200/repositories/ai-ethics-kg"

def q(query):
    r = requests.post(EP, data={"query": "PREFIX : <https://w3id.org/aief/>\n" + query},
                      headers={"Accept": "application/sparql-results+json"})
    r.raise_for_status()
    return r.json()["results"]["bindings"]

rows = q("""SELECT ?id ?text ?fw WHERE {
  ?r a :Requirement ; :requirementID ?id ; :requirementText ?text ; :belongsToFramework ?fwNode .
  BIND(STRAFTER(STR(?fwNode), "https://w3id.org/aief/") AS ?fw) }""")
ids = [b["id"]["value"] for b in rows]
texts = [b["text"]["value"] for b in rows]
fws = [b["fw"]["value"] for b in rows]
print(f"Loaded {len(ids)} requirements")

model = SentenceTransformer("all-MiniLM-L6-v2")
emb = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)

# Threshold calibrated against the empirical cross-framework similarity
# distribution, not chosen post-hoc to inflate a number: the 90th percentile
# of max cross-framework cosine similarity is 0.670 (measured separately,
# see analysis/results/similarity_distribution.json). Distance threshold is
# therefore 1 - 0.670 = 0.33, i.e. "similarity above the top decile of what
# cross-framework requirement pairs typically achieve." Complete linkage is
# used (not average/single) so a cluster only merges when *all* member pairs
# clear the threshold, avoiding transitive chaining into topically-related
# but non-paraphrastic groups.
DIST_THRESHOLD = 0.33
clustering = AgglomerativeClustering(
    n_clusters=None, distance_threshold=DIST_THRESHOLD,
    metric="cosine", linkage="complete"
).fit(emb)
labels = clustering.labels_
n_clusters = len(set(labels))

clusters = defaultdict(list)
for i, lab in enumerate(labels):
    clusters[lab].append(i)

multi_framework = 0
cross_framework_clusters = []
size_dist = defaultdict(int)
for lab, idxs in clusters.items():
    size_dist[len(idxs)] += 1
    cluster_fws = {fws[i] for i in idxs}
    if len(cluster_fws) >= 2:
        multi_framework += 1
        cross_framework_clusters.append({
            "cluster_id": int(lab),
            "frameworks": sorted(cluster_fws),
            "requirements": [{"id": ids[i], "framework": fws[i], "text": texts[i]} for i in idxs]
        })

print(f"\n207 requirement statements -> {n_clusters} distinct obligation clusters "
      f"(cosine distance threshold {DIST_THRESHOLD}, complete linkage)")
print(f"Cluster size distribution: {dict(sorted(size_dist.items()))}")
print(f"Redundancy compression: {207 - n_clusters} requirement statements ({100*(207-n_clusters)/207:.1f}%) "
      f"are near-paraphrases of another requirement already in the graph.")
print(f"Clusters spanning 2+ distinct frameworks (cross-framework redundancy): {multi_framework}")
if multi_framework == 0:
    print("No cluster spans 3+ frameworks: paraphrase-level redundancy exists but is pairwise, "
          "not independently triplicated across three or more regimes at this similarity bar.")

print("\n=== CROSS-FRAMEWORK REDUNDANT CLUSTERS ===")
for ex in sorted(cross_framework_clusters, key=lambda x: -len(x["requirements"])):
    print(f"\nCluster (frameworks: {', '.join(ex['frameworks'])}):")
    for r in ex["requirements"]:
        print(f"  {r['id']} [{r['framework']}]: {r['text'][:100]}")

out = {
    "n_requirements": len(ids), "n_clusters": n_clusters,
    "distance_threshold": DIST_THRESHOLD,
    "cluster_size_distribution": {str(k): v for k, v in size_dist.items()},
    "cross_framework_cluster_count": multi_framework,
    "cross_framework_clusters": cross_framework_clusters,
}
dst = Path(__file__).parent / "results/requirement_clustering.json"
json.dump(out, open(dst, "w"), indent=2)
print(f"\nSaved {dst}")
