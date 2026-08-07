"""Retrieval baseline comparison (RQ2, retrieval stage, no LLM):
ontology-driven SPARQL retrieval vs BM25 vs TF-IDF cosine over the same
207 requirement texts, scored as recall@k against expected_requirements.

Fairness protocol: SPARQL retrieval returns a variable-size set (~140-196);
baselines are scored both at fixed k in {10, 25, 50, 100} and at k matched
to the SPARQL set size for that proposal (recall@|SPARQL|).
"""
import json, sys, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from synthetic_proposals import PROPOSALS
from sparql_retrieval import retrieve_all_for_proposal

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_ONTOLOGY = Path(__file__).resolve().parent.parent / "ontology" / "ai-ethics-final.ttl"

def fetch_requirements():
    # Reads the ontology file directly rather than querying GraphDB. A
    # GraphDB instance, when running, cannot be trusted to hold the current
    # ontology without an explicit reload after every edit -- verified stale
    # here on 2026-08-07 (the loaded repository lacked dcterms:title, added
    # to the file in this session) -- so this benchmark is defined against
    # the file, the single source of truth, rather than against whichever
    # snapshot happens to be loaded in a running triple store.
    from rdflib import Graph, RDF, URIRef
    import owlrl
    g = Graph()
    g.parse(_ONTOLOGY, format="turtle")
    owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
    A = "https://w3id.org/aief/"
    seen, out = set(), []
    for r in g.subjects(RDF.type, URIRef(A + "Requirement")):
        rid = g.value(r, URIRef(A + "requirementID"))
        text = g.value(r, URIRef(A + "requirementText"))
        if rid is None or text is None:
            continue
        rid = str(rid)
        if rid not in seen:
            seen.add(rid); out.append((rid, str(text)))
    return out

def tok(s): return re.findall(r"[a-z]+", s.lower())

def main():
    from sparql_retrieval import set_retrieval_backend
    # Force the file-backed path on both sides of this comparison. GraphDB,
    # when running, is not guaranteed current (see fetch_requirements) and
    # "auto" mode would otherwise prefer it silently.
    set_retrieval_backend("local")
    reqs = fetch_requirements()
    ids = [r[0] for r in reqs]
    texts = [r[1] for r in reqs]
    print(f"Corpus: {len(reqs)} requirements\n")

    bm25 = BM25Okapi([tok(t) for t in texts])
    vec = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vec.fit_transform(texts)

    KS = [10, 25, 50, 100]
    agg = {("bm25", k): [] for k in KS} | {("tfidf", k): [] for k in KS}
    agg[("bm25", "matched")] = []; agg[("tfidf", "matched")] = []
    sparql_recalls, sparql_sizes = [], []

    for p in PROPOSALS:
        expected = set(p["expected_requirements"])
        text = p["proposal_text"]

        # condition 1: ontology-driven SPARQL (the system's retrieval)
        s_reqs, _, _, _, _, _ = retrieve_all_for_proposal(text)
        s_ids = {r["id"] for r in s_reqs}
        sparql_recalls.append(len(s_ids & expected) / len(expected))
        sparql_sizes.append(len(s_ids))

        # condition 2: BM25 ranking
        scores = bm25.get_scores(tok(text))
        bm_rank = [ids[i] for i in sorted(range(len(ids)), key=lambda i: -scores[i])]
        # condition 3: TF-IDF cosine ranking
        sims = cosine_similarity(vec.transform([text]), tfidf_matrix)[0]
        tf_rank = [ids[i] for i in sorted(range(len(ids)), key=lambda i: -sims[i])]

        for name, rank in (("bm25", bm_rank), ("tfidf", tf_rank)):
            for k in KS:
                agg[(name, k)].append(len(set(rank[:k]) & expected) / len(expected))
            agg[(name, "matched")].append(len(set(rank[:len(s_ids)]) & expected) / len(expected))

    n = len(PROPOSALS)
    mean = lambda xs: sum(xs) / len(xs)
    print(f"SPARQL (ontology-driven): recall={mean(sparql_recalls):.3f} at mean set size {mean(sparql_sizes):.0f}")
    print(f"{'condition':8s} " + " ".join(f"R@{k:<4}" for k in KS) + " R@|SPARQL|")
    for name in ("bm25", "tfidf"):
        row = " ".join(f"{mean(agg[(name,k)]):.3f}" for k in KS)
        print(f"{name:8s} {row}   {mean(agg[(name,'matched')]):.3f}")

    out = {
        "corpus_size": len(reqs), "n_proposals": n,
        "sparql": {"mean_recall": mean(sparql_recalls), "mean_set_size": mean(sparql_sizes),
                   "per_proposal_recall": sparql_recalls},
        **{f"{name}_recall_at_{k}": mean(agg[(name, k)]) for name in ("bm25", "tfidf") for k in KS},
        **{f"{name}_recall_matched_k": mean(agg[(name, "matched")]) for name in ("bm25", "tfidf")},
    }
    dst = Path(__file__).parent.parent / "evaluation/retrieval_baselines.json"
    json.dump(out, open(dst, "w"), indent=2)
    print(f"\nSaved {dst}")

if __name__ == "__main__":
    main()
