"""
sparql_retrieval.py
Handles all SPARQL queries against local GraphDB Desktop.
Endpoint: http://localhost:7200/repositories/ai-ethics-kg
Namespace: https://w3id.org/aief/

Phase 1: retrieves sectionReference + risk categories (:hasRisk / :demonstratesRisk)
Phase 3: Charter rights disambiguation (bias→Art21 vs Art11/Art22) + Art12/Art31 triggers
"""

import json
import math
import re
import requests
from pathlib import Path

GRAPHDB_URL = "http://localhost:7200/repositories/ai-ethics-kg"

# Local ontology fallback when GraphDB is unavailable (Phase 0+ testing)
_ONTOLOGY_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "ontology" / "ai-ethics-final.ttl",
    Path(__file__).resolve().parent.parent / "ai-ethics-final.ttl",
]
_local_graph = None
_use_local = None  # None=auto, True=force local, False=force GraphDB

# Precomputed global document frequency for RiskCategory IDF ranking.
# Regenerate via: python ontology/compute_risk_category_idf.py
_IDF_PATH = Path(__file__).resolve().parent.parent / "ontology" / "risk_category_doc_frequency.json"
if not _IDF_PATH.exists():
    raise FileNotFoundError(
        f"Missing risk-category IDF table at {_IDF_PATH}. "
        "Run: python ontology/compute_risk_category_idf.py"
    )
_DOC_FREQ: dict[str, int] = json.loads(_IDF_PATH.read_text())
if not _DOC_FREQ:
    raise ValueError(f"Empty risk-category IDF table at {_IDF_PATH}")
_TOTAL_DOCS: int = sum(_DOC_FREQ.values())


def _get_local_graph():
    global _local_graph
    if _local_graph is not None:
        return _local_graph
    from rdflib import Graph
    for path in _ONTOLOGY_CANDIDATES:
        if path.exists():
            g = Graph()
            g.parse(path, format="turtle")
            _local_graph = g
            print(f"  [OK] Loaded local ontology: {path} ({len(g)} triples)")
            return _local_graph
    raise FileNotFoundError("No local ai-ethics-final.ttl found for SPARQL fallback")


def set_retrieval_backend(mode: str = "auto"):
    """mode: 'auto' | 'graphdb' | 'local'"""
    global _use_local
    if mode == "local":
        _use_local = True
    elif mode == "graphdb":
        _use_local = False
    else:
        _use_local = None


PREFIX = """
PREFIX : <https://w3id.org/aief/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
"""

# ── Keyword → Charter Right mapping ──────────────────────────────────────────
KEYWORD_TO_RIGHTS = {
    "bias":             ["Art21_NonDiscrimination", "Art23_GenderEquality", "Art20_EqualityBeforeLaw"],
    "discriminat":      ["Art21_NonDiscrimination", "Art23_GenderEquality", "Art26_DisabilityIntegration"],
    "privacy":          ["Art7_PrivateLife", "Art8_DataProtection"],
    # bare "data" removed — too broad (dataset/database/metadata); use personal data etc.
    "personal data":    ["Art8_DataProtection", "Art7_PrivateLife"],
    "consent":          ["Art3_RightToIntegrity", "Art7_PrivateLife"],
    "health":           ["Art35_HealthCare", "Art2_RightToLife"],
    "medical":          ["Art35_HealthCare", "Art2_RightToLife"],
    "diagnos":          ["Art35_HealthCare", "Art2_RightToLife"],
    "patient":          ["Art35_HealthCare", "Art2_RightToLife", "Art8_DataProtection"],
    "child":            ["Art24_RightsOfChild"],
    "minor":            ["Art24_RightsOfChild"],
    "student":          ["Art24_RightsOfChild", "Art8_DataProtection"],
    "school":           ["Art24_RightsOfChild", "Art8_DataProtection"],
    "autonomy":         ["Art6_RightToLiberty", "Art1_HumanDignity"],
    "harm":             ["Art1_HumanDignity", "Art2_RightToLife", "Art47_RightToEffectiveRemedy"],
    "surveil":          ["Art7_PrivateLife", "Art8_DataProtection", "Art6_RightToLiberty"],
    "monitor":          ["Art7_PrivateLife", "Art8_DataProtection"],
    "track":            ["Art7_PrivateLife", "Art8_DataProtection"],
    "environment":      ["Art37_EnvironmentalProtection"],
    "carbon":           ["Art37_EnvironmentalProtection"],
    "fairness":         ["Art20_EqualityBeforeLaw", "Art21_NonDiscrimination"],
    "transparen":       ["Art41_GoodAdministration", "Art47_RightToEffectiveRemedy"],
    "accountab":        ["Art41_GoodAdministration", "Art47_RightToEffectiveRemedy"],
    "explain":          ["Art41_GoodAdministration", "Art47_RightToEffectiveRemedy"],
    "safety":           ["Art2_RightToLife", "Art1_HumanDignity"],
    "employ":           ["Art31_FairWorkingConditions", "Art15_FreedomOfOccupation"],
    "hiring":           ["Art15_FreedomOfOccupation", "Art21_NonDiscrimination", "Art23_GenderEquality"],
    "recruit":          ["Art15_FreedomOfOccupation", "Art21_NonDiscrimination"],
    # Phase 3 — Art31 workplace triggers
    "employee":         ["Art31_FairWorkingConditions", "Art15_FreedomOfOccupation"],
    "staff":            ["Art31_FairWorkingConditions", "Art8_DataProtection"],
    "workplace":        ["Art31_FairWorkingConditions", "Art15_FreedomOfOccupation"],
    "working conditions": ["Art31_FairWorkingConditions"],
    "manipulat":        ["Art1_HumanDignity", "Art6_RightToLiberty"],
    "deception":        ["Art1_HumanDignity", "Art11_FreedomOfExpression"],
    "deepfake":         ["Art1_HumanDignity", "Art7_PrivateLife"],
    "facial recogn":    ["Art7_PrivateLife", "Art8_DataProtection", "Art21_NonDiscrimination"],
    "biometric":        ["Art7_PrivateLife", "Art8_DataProtection", "Art1_HumanDignity"],
    "prediction":       ["Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy"],
    "predict":          ["Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy"],
    "profil":           ["Art7_PrivateLife", "Art8_DataProtection", "Art21_NonDiscrimination"],
    "classif":          ["Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy"],
    # Art41 removed from scor — score/scoring is not administrative process
    "scor":             ["Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy"],
    "vulnerable":       ["Art1_HumanDignity", "Art24_RightsOfChild"],
    "minority":         ["Art21_NonDiscrimination", "Art22_CulturalDiversity"],
    "race":             ["Art21_NonDiscrimination"],
    "racial":           ["Art21_NonDiscrimination"],
    "gender":           ["Art21_NonDiscrimination", "Art23_GenderEquality"],
    "disabilit":        ["Art26_DisabilityIntegration"],
    "criminal":         ["Art6_RightToLiberty", "Art47_RightToEffectiveRemedy", "Art48_PresumptionOfInnocence"],
    "polic":            ["Art6_RightToLiberty", "Art21_NonDiscrimination", "Art7_PrivateLife"],
    "law enforce":      ["Art6_RightToLiberty", "Art48_PresumptionOfInnocence", "Art47_RightToEffectiveRemedy"],
    "autonomous":       ["Art2_RightToLife", "Art1_HumanDignity"],
    "self-driving":     ["Art2_RightToLife", "Art1_HumanDignity"],
    "weapon":           ["Art2_RightToLife", "Art1_HumanDignity"],
    "dual-use":         ["Art2_RightToLife", "Art1_HumanDignity", "Art11_FreedomOfExpression"],
    "content moder":    ["Art11_FreedomOfExpression", "Art21_NonDiscrimination"],
    "recommend":        ["Art11_FreedomOfExpression", "Art1_HumanDignity"],
    # Art41 removed from chatbot — conversational agent ≠ administrative process
    "chatbot":          ["Art1_HumanDignity"],
    "generat":          ["Art1_HumanDignity", "Art7_PrivateLife"],
    "emotion":          ["Art1_HumanDignity", "Art7_PrivateLife", "Art3_RightToIntegrity"],
    "sentiment":        ["Art7_PrivateLife", "Art11_FreedomOfExpression"],
    "social media":     ["Art7_PrivateLife", "Art8_DataProtection", "Art11_FreedomOfExpression"],
    "scraping":         ["Art7_PrivateLife", "Art8_DataProtection"],
    "cross-border":     ["Art8_DataProtection", "Art7_PrivateLife"],
    "transfer":         ["Art8_DataProtection"],
    # Phase 3 — Art12 assembly/association triggers
    "protest":          ["Art12_FreedomOfAssembly", "Art11_FreedomOfExpression"],
    "assembly":         ["Art12_FreedomOfAssembly"],
    "union":            ["Art12_FreedomOfAssembly", "Art31_FairWorkingConditions"],
    "organizing":       ["Art12_FreedomOfAssembly", "Art11_FreedomOfExpression"],
    "organisation":     ["Art12_FreedomOfAssembly", "Art11_FreedomOfExpression"],  # British spelling in P17
    "association":      ["Art12_FreedomOfAssembly"],
    "collective":       ["Art12_FreedomOfAssembly"],
    # Art41 — administrative / institutional decision-making only
    "admissions":       ["Art41_GoodAdministration"],
    "disciplinary":     ["Art41_GoodAdministration", "Art47_RightToEffectiveRemedy"],
    "reams":            ["Art41_GoodAdministration"],
    "welfare":          ["Art41_GoodAdministration", "Art21_NonDiscrimination"],
    "public sector":    ["Art41_GoodAdministration"],
    "administrative":   ["Art41_GoodAdministration"],
}

# Invert for per-right scoring
RIGHT_TO_KEYWORDS: dict[str, list] = {}
for _kw, _rights in KEYWORD_TO_RIGHTS.items():
    for _right in _rights:
        RIGHT_TO_KEYWORDS.setdefault(_right, []).append(_kw)

# Personal/identifiable data signals for conditional Art8 (excludes bare "data")
_ART8_PERSONAL_DATA_KEYWORDS = {
    "privacy", "personal data", "biometric", "patient", "consent",
    "surveil", "monitor", "track", "profil", "scraping", "cross-border",
    "facial recogn", "health", "medical", "diagnos",
}

# Rights-matching hyperparameters
_RIGHTS_TOP_K = 8                 # max rights passed downstream
_RIGHTS_MIN_TYPES = 1             # at least one distinct keyword type
_RIGHTS_MIN_OCCURRENCES = 2       # or ≥2 occurrences of triggering keywords
_RIGHTS_MIN_SCORE = 1.15          # density-adjusted score floor
_SHORT_STEM_MAX_LEN = 5           # stems shorter than this use word-boundary match

# Bias/discrimination keywords that may incorrectly default to Art21
_BIAS_KEYWORDS = {"bias", "discriminat", "fairness"}

# SHACL-style structural signals: identifiable individual/group treatment → Art21
_INDIVIDUAL_TREATMENT_PATTERNS = [
    r"\bpatient(s)?\b",
    r"\bdefendant(s)?\b",
    r"\bapplicant(s)?\b",
    r"\bcandidate(s)?\b",
    r"\bemployee(s)?\b",
    r"\bstudent(s)?\b",
    r"\bhiring\b",
    r"\brecruit",
    r"\bsentenc",
    r"\bbail\b",
    r"\bparole\b",
    r"\bcare management\b",
    r"\bindividual(s)?\b.{0,40}\b(decision|score|referral|grade|screening)",
    r"\b(decision|score|referral|grade|screening).{0,40}\bindividual",
    r"\bprotected characteristic",
    r"\brace as a\b",
    r"\bracial bias\b",
    r"\bgender bias\b",
]

# Systemic / population / information-quality signals → Art11 / Art22 (not Art21)
_SYSTEMIC_INFO_PATTERNS = [
    r"\bbibliometric",
    r"\bliterature\b",
    r"\bpublication(s)?\b",
    r"\bcitation network",
    r"\btopic modell",
    r"\bopen access\b",
    r"\bmetadata\b",
    r"\bresearch direction",
    r"\bgaps in the .+ literature",
    r"\bpublicly available metadata",
    r"\bno personal data\b",
    r"\bno ai systems will be developed",
    r"\bpopulation-level\b",
    r"\bsystemic\b",
    r"\brepresentativeness\b",
    r"\bcorpus of\b",
    r"\bdataset bias\b",  # dataset-level without individual decisions
]


def sparql_query(query: str) -> list:
    """Execute a SPARQL query against GraphDB, with local rdflib fallback."""
    global _use_local
    full_query = PREFIX + query

    def _local_results():
        g = _get_local_graph()
        rows = g.query(full_query)
        bindings = []
        for row in rows:
            b = {}
            for var in rows.vars:
                val = row[var]
                if val is None:
                    continue
                key = str(var)
                if getattr(val, "datatype", None) is not None or val.__class__.__name__ == "Literal":
                    b[key] = {"type": "literal", "value": str(val)}
                else:
                    b[key] = {"type": "uri", "value": str(val)}
            bindings.append(b)
        return bindings

    if _use_local is True:
        return _local_results()

    if _use_local is not False:
        # auto: try GraphDB first
        try:
            response = requests.get(
                GRAPHDB_URL,
                headers={"Accept": "application/sparql-results+json"},
                params={"query": full_query},
                timeout=5,
            )
            if response.status_code == 200:
                return response.json()["results"]["bindings"]
            print(f"  [SPARQL ERROR] Status {response.status_code}: {response.text[:200]}")
        except requests.exceptions.ConnectionError:
            print("  [SPARQL] GraphDB unreachable — falling back to local ontology TTL")
            _use_local = True
            return _local_results()
        except Exception as e:
            print(f"  [SPARQL ERROR] {e} — falling back to local ontology TTL")
            _use_local = True
            return _local_results()

    # force graphdb failed path
    try:
        response = requests.get(
            GRAPHDB_URL,
            headers={"Accept": "application/sparql-results+json"},
            params={"query": full_query},
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()["results"]["bindings"]
        print(f"  [SPARQL ERROR] Status {response.status_code}: {response.text[:200]}")
        return []
    except Exception as e:
        print(f"  [SPARQL ERROR] {e}")
        return []


def test_connection() -> bool:
    """Test if GraphDB is reachable and has data."""
    results = sparql_query("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")
    if results:
        count = results[0]["n"]["value"]
        print(f"  [OK] GraphDB connected. Total triples: {count}")
        return True
    else:
        print("  [FAIL] Cannot connect to GraphDB.")
        return False


def _count_keyword(text: str, term: str) -> int:
    """Count keyword occurrences; short stems use word-boundary prefix matching."""
    if " " in term or len(term) > _SHORT_STEM_MAX_LEN:
        return text.count(term)
    # Short stems (e.g. scor, harm, track): match as word-prefix to avoid
    # substring false positives inside unrelated tokens where possible.
    return len(re.findall(rf"\b{re.escape(term)}\w*", text))


def extract_keyword_counts(proposal: str) -> dict:
    """Return {keyword: occurrence_count} for KEYWORD_TO_RIGHTS terms found."""
    text = proposal.lower()
    hits = {}
    # Longer phrases first so diagnostics prefer "personal data" over fragments
    for term in sorted(KEYWORD_TO_RIGHTS.keys(), key=len, reverse=True):
        n = _count_keyword(text, term)
        if n > 0:
            hits[term] = n
    return hits


def extract_keywords(proposal: str) -> list:
    """Extract risk keywords from proposal text (occurrence-weighted presence)."""
    hits = extract_keyword_counts(proposal)
    # Stable order: most frequent first, then alpha
    return sorted(hits.keys(), key=lambda k: (-hits[k], k))


extract_keywords.with_counts = extract_keyword_counts  # type: ignore[attr-defined]


def score_rights_for_proposal(proposal: str, hits: dict) -> dict:
    """
    Score each Charter right by distinct keyword-type count and occurrence density.

    score = n_types + 100 * (total_occurrences / word_count)

    A right barely triggered by one incidental mention scores near 1.0; a right
    central to the proposal (multiple keyword types and/or dense repeats) scores
    higher and survives the top-K / threshold cut in get_matched_rights().
    """
    words = max(len(proposal.split()), 1)
    scores = {}
    for right, kws in RIGHT_TO_KEYWORDS.items():
        fired = [kw for kw in kws if kw in hits]
        if not fired:
            continue
        n_types = len(fired)
        n_occ = sum(hits[kw] for kw in fired)
        density = n_occ / words
        scores[right] = {
            "score": n_types + 100.0 * density,
            "n_types": n_types,
            "n_occ": n_occ,
            "density": density,
            "keywords": fired,
        }
    return scores


def _right_passes_threshold(info: dict) -> bool:
    """Salience gate: enough distinct types, or enough occurrences, and min score."""
    if info["score"] < _RIGHTS_MIN_SCORE:
        return False
    if info["n_types"] >= 2:
        return True
    if info["n_types"] >= _RIGHTS_MIN_TYPES and info["n_occ"] >= _RIGHTS_MIN_OCCURRENCES:
        return True
    # Single keyword type with a single occurrence: reject (incidental mention)
    return False


def disambiguate_bias_rights(proposal: str, rights: set, keywords: list) -> tuple[set, str]:
    """
    Phase 3 SHACL-style structural check for bias/discrimination keywords.

    If bias/fairness/discrimination fired, decide whether the risk affects an
    identifiable individual/group's treatment (→ keep Art21) or information
    quality / representativeness at a population/systemic level (→ Art11/Art22).

    Returns (rights, audit_path) where audit_path is one of:
      'not_applicable' | 'individual_treatment→Art21' | 'systemic_info→Art11/Art22'
    """
    bias_fired = any(kw in _BIAS_KEYWORDS or kw.startswith("discriminat") for kw in keywords)
    if not bias_fired:
        bias_fired = any(k in keywords for k in ("bias", "discriminat", "fairness"))
    if not bias_fired:
        return rights, "not_applicable"

    text = proposal.lower()
    individual = any(re.search(p, text) for p in _INDIVIDUAL_TREATMENT_PATTERNS)
    systemic = any(re.search(p, text) for p in _SYSTEMIC_INFO_PATTERNS)

    art21_family = {
        "Art21_NonDiscrimination",
        "Art23_GenderEquality",
        "Art20_EqualityBeforeLaw",
        "Art26_DisabilityIntegration",
    }

    if systemic and not individual:
        rights -= art21_family
        rights.add("Art11_FreedomOfExpression")
        rights.add("Art22_CulturalDiversity")
        path = "systemic_info→Art11/Art22"
        print(f"  [DISAMBIGUATION] bias keywords → {path} (removed Art21 family)")
        return rights, path

    if individual:
        rights.add("Art21_NonDiscrimination")
        path = "individual_treatment→Art21"
        print(f"  [DISAMBIGUATION] bias keywords → {path}")
        return rights, path

    if systemic:
        rights -= art21_family
        rights.add("Art11_FreedomOfExpression")
        path = "systemic_info→Art11/Art22"
        print(f"  [DISAMBIGUATION] bias keywords → {path} (ambiguous+systemic)")
        return rights, path

    path = "individual_treatment→Art21"
    print(f"  [DISAMBIGUATION] bias keywords → {path} (default keep)")
    return rights, path


def get_matched_rights(keywords: list, proposal: str = "") -> list:
    """
    Map proposal text to Charter article IRIs via density-weighted keyword scoring.

    Unlike the old binary matcher (keyword present → all associated rights),
    each right is scored by distinct keyword-type count and occurrence density,
    then filtered by a salience threshold and capped at top-K. Art8 injects only
    when personal/identifiable-data keywords fire; Art41 is never unconditionally
    injected (matched only via admin-process keywords that survive scoring).
    """
    text = proposal or ""
    hits = extract_keyword_counts(text) if text else {k: 1 for k in keywords}
    # Honour caller-supplied keyword list as a filter when proposal is empty
    if not text and keywords:
        hits = {k: hits.get(k, 1) for k in keywords if k in KEYWORD_TO_RIGHTS}

    scored = score_rights_for_proposal(text or " ".join(hits), hits) if hits else {}

    # Salience filter
    eligible = {
        right: info for right, info in scored.items()
        if _right_passes_threshold(info)
    }

    # Top-K by score
    ranked = sorted(eligible.items(), key=lambda kv: (-kv[1]["score"], kv[0]))
    rights = {right for right, _ in ranked[:_RIGHTS_TOP_K]}
    rights_from_keywords = set(rights)

    # Conditional Art8: personal/identifiable data only (not bare "data")
    injected: set[str] = set()
    art8_hits = {k: hits[k] for k in _ART8_PERSONAL_DATA_KEYWORDS if k in hits}
    if art8_hits and sum(art8_hits.values()) >= 1:
        # Require the personal-data signal itself to be non-incidental when it's
        # the sole Art8 path (already in rights_from_keywords is fine).
        if "Art8_DataProtection" not in rights:
            if sum(art8_hits.values()) >= 2 or len(art8_hits) >= 2:
                rights.add("Art8_DataProtection")
                injected.add("Art8_DataProtection")
            elif sum(art8_hits.values()) >= 1 and any(
                k in art8_hits for k in (
                    "personal data", "biometric", "privacy", "patient",
                    "facial recogn", "health", "medical",
                )
            ):
                # Strong personal-data terms: allow single occurrence
                rights.add("Art8_DataProtection")
                injected.add("Art8_DataProtection")

    # Art41: no soft inject — only via scored admin keywords (transparen/
    # accountab/explain/admissions/disciplinary/reams/welfare/public sector/
    # administrative) that already survived the threshold+top-K cut.

    audit_path = "not_applicable"
    kw_list = list(hits.keys())
    if text:
        rights, audit_path = disambiguate_bias_rights(text, rights, kw_list)

    # Re-cap after disambiguation may have added Art11/Art22
    if len(rights) > _RIGHTS_TOP_K:
        # Keep highest-scoring among current set; always keep disambiguation adds
        score_map = {r: scored.get(r, {}).get("score", 0.0) for r in rights}
        # Boost freshly added disambiguation rights so they survive the cut
        for r in rights:
            if r not in eligible and r not in injected:
                score_map[r] = max(score_map.get(r, 0.0), 2.0)
        rights = set(sorted(rights, key=lambda r: -score_map.get(r, 0.0))[:_RIGHTS_TOP_K])

    get_matched_rights.last_disambiguation = audit_path  # type: ignore[attr-defined]
    get_matched_rights.last_match_meta = {  # type: ignore[attr-defined]
        "keyword_counts": hits,
        "right_scores": {
            r: {
                "score": round(info["score"], 3),
                "n_types": info["n_types"],
                "n_occ": info["n_occ"],
                "density": round(info["density"], 5),
                "keywords": info["keywords"],
            }
            for r, info in scored.items()
        },
        "rights_from_keywords": sorted(rights_from_keywords),
        "rights_injected": sorted(injected),
        "rights_injected_requested": sorted(injected),
        "top_k": _RIGHTS_TOP_K,
        "threshold": _RIGHTS_MIN_SCORE,
    }
    return sorted(rights)


get_matched_rights.last_disambiguation = "not_applicable"  # type: ignore[attr-defined]
get_matched_rights.last_match_meta = {}  # type: ignore[attr-defined]


def retrieve_requirements_by_right(charter_article: str) -> list:
    """Get all requirements mapped to a given Charter right (incl. section + risks)."""
    # Two-step friendly query: fetch req fields, then risks separately in Python
    # (GROUP_CONCAT + OPTIONAL is unreliable under rdflib).
    query = f"""
    SELECT DISTINCT ?reqID ?text ?framework ?tier ?mandatory ?sectionReference ?riskLocal
    WHERE {{
        ?req :mapsToRight :{charter_article} ;
             :requirementID ?reqID ;
             :requirementText ?text ;
             :belongsToFramework ?fw ;
             :hasTier ?tierNode ;
             :isMandatory ?mandatory .
        OPTIONAL {{ ?req :sectionReference ?sectionReference }}
        OPTIONAL {{
            ?req :hasRisk ?risk .
            BIND(STRAFTER(STR(?risk), "/aief/") AS ?riskLocal)
        }}
        BIND(STRAFTER(STR(?fw), "/aief/") AS ?framework)
        BIND(STRAFTER(STR(?tierNode), "/aief/") AS ?tier)
    }}
    ORDER BY ?reqID
    """
    rows = sparql_query(query)
    # Collapse multi-risk rows into one binding with riskCategories CSV
    by_id = {}
    for r in rows:
        req_id = r.get("reqID", {}).get("value", "")
        if not req_id:
            continue
        if req_id not in by_id:
            by_id[req_id] = {
                "reqID": r.get("reqID", {}),
                "text": r.get("text", {}),
                "framework": r.get("framework", {}),
                "tier": r.get("tier", {}),
                "mandatory": r.get("mandatory", {}),
                "sectionReference": r.get("sectionReference", {}),
                "riskCategories": {"type": "literal", "value": ""},
                "_risks": [],
            }
        risk = r.get("riskLocal", {}).get("value", "")
        if risk and risk not in by_id[req_id]["_risks"]:
            by_id[req_id]["_risks"].append(risk)
    out = []
    for item in by_id.values():
        risks = item.pop("_risks")
        item["riskCategories"] = {"type": "literal", "value": ",".join(risks)}
        out.append(item)
    return out


def retrieve_incidents_by_right(charter_article: str, limit: int = 3) -> list:
    """Get incidents impacting a given Charter right (incl. demonstrated risks)."""
    query = f"""
    SELECT DISTINCT ?incID ?title ?riskLocal WHERE {{
        ?inc a :Incident ;
             :incidentID ?incID ;
             :incidentTitle ?title ;
             :impactsRight :{charter_article} .
        OPTIONAL {{
            ?inc :demonstratesRisk ?risk .
            BIND(STRAFTER(STR(?risk), "/aief/") AS ?riskLocal)
        }}
    }}
    """
    rows = sparql_query(query)
    by_id = {}
    for r in rows:
        inc_id = r.get("incID", {}).get("value", "")
        if not inc_id:
            continue
        if inc_id not in by_id:
            by_id[inc_id] = {
                "incID": r.get("incID", {}),
                "title": r.get("title", {}),
                "riskCategories": {"type": "literal", "value": ""},
                "_risks": [],
            }
        risk = r.get("riskLocal", {}).get("value", "")
        if risk and risk not in by_id[inc_id]["_risks"]:
            by_id[inc_id]["_risks"].append(risk)
    out = []
    for item in list(by_id.values())[:limit]:
        risks = item.pop("_risks")
        item["riskCategories"] = {"type": "literal", "value": ",".join(risks)}
        out.append(item)
    return out


def _parse_risk_list(binding: dict) -> list:
    raw = binding.get("riskCategories", {}).get("value", "")
    if not raw:
        return []
    return [r.strip() for r in raw.split(",") if r.strip()]


def retrieve_risk_category_definitions(category_names: list) -> list:
    """Fetch rdfs:comment definitions for RiskCategory IRIs."""
    if not category_names:
        return []
    values = " ".join(f":{c}" for c in category_names)
    query = f"""
    SELECT ?catLocal ?label ?comment WHERE {{
        VALUES ?cat {{ {values} }}
        OPTIONAL {{ ?cat rdfs:label ?label }}
        OPTIONAL {{ ?cat rdfs:comment ?comment }}
        BIND(STRAFTER(STR(?cat), "/aief/") AS ?catLocal)
    }}
    """
    results = sparql_query(query)
    out = []
    for r in results:
        out.append({
            "id": r.get("catLocal", {}).get("value", ""),
            "label": r.get("label", {}).get("value", ""),
            "definition": r.get("comment", {}).get("value", ""),
        })
    # Preserve order of category_names; fill gaps if SPARQL miss
    by_id = {c["id"]: c for c in out if c["id"]}
    ordered = []
    for name in category_names:
        if name in by_id:
            ordered.append(by_id[name])
        else:
            ordered.append({"id": name, "label": name, "definition": ""})
    return ordered


def _idf_weight(category: str, total_docs: int = _TOTAL_DOCS) -> float:
    """Smoothed IDF: rare categories score higher than ubiquitous ones."""
    df = _DOC_FREQ.get(category, 1)  # avoid div-by-zero if table is stale
    return math.log((total_docs + 1) / (df + 1)) + 1


def rank_risk_categories(
    per_proposal_counts: dict,
    total_docs: int = _TOTAL_DOCS,
    top_n: int = 10,
    primary_slots: int = 6,
) -> list:
    """
    Two-pool IDF ranking over categories present in this proposal's evidence.

    Pool A (primary_slots): highest per-proposal term frequency — keeps the
    categories the retrieval actually hit hardest (Accountability, Discrimination,
    PrivacyBreach, …).

    Pool B (remaining slots to top_n): highest IDF among categories not already
    selected — surfaces rare-but-retrieved categories (Transparency,
    FalseIdentification, …) that raw TF ranking crowds out.

    Pure TF×IDF fails here because Phase-0 seeding put low-df labels on many
    requirements, so high-recall proposals retrieve nearly the full taxonomy and
    raw TF lets Accountability (tf≈90) dominate while binary IDF promotes every
    ultra-rare seed label. Two-pool ranking is the standard IR coverage pattern
    (relevance pool + novelty/rarity pool) and needs no category allowlist.

    Returns list of (category, score) in final order. Score is TF for pool A
    and IDF for pool B (for auditability).
    """
    if not per_proposal_counts:
        return []

    by_tf = sorted(
        per_proposal_counts.items(),
        key=lambda kv: (-kv[1], kv[0]),
    )
    by_idf = sorted(
        per_proposal_counts.keys(),
        key=lambda c: (-_idf_weight(c, total_docs), -per_proposal_counts[c], c),
    )

    selected: list[tuple[str, float]] = []
    seen: set[str] = set()
    slots_a = min(primary_slots, top_n)
    for cat, tf in by_tf:
        if len(selected) >= slots_a:
            break
        selected.append((cat, float(tf)))
        seen.add(cat)
    for cat in by_idf:
        if len(selected) >= top_n:
            break
        if cat in seen:
            continue
        selected.append((cat, _idf_weight(cat, total_docs)))
        seen.add(cat)
    return selected


def retrieve_risk_categories_for_proposal(reqs: list, incidents: list, top_n: int = 10) -> list:
    """
    Aggregate RiskCategory instances from retrieved requirements and incidents,
    with definitions. Scoped to this proposal's evidence (not the full taxonomy
    dump).

    Categories are ranked by a two-pool TF + IDF scheme over the global document
    frequencies in ontology/risk_category_doc_frequency.json (see
    rank_risk_categories). This replaces the previous ALWAYS_SURFACE_IF_PRESENT
    allowlist with a generalizable statistical rule.
    """
    from collections import Counter

    counts: Counter = Counter()
    for r in reqs:
        for cat in r.get("risk_categories", []) or []:
            counts[cat] += 1
    for inc in incidents:
        for cat in inc.get("risk_categories", []) or []:
            counts[cat] += 1

    if not counts:
        return []

    ranked = rank_risk_categories(dict(counts), top_n=top_n)
    top = [cat for cat, _score in ranked]

    defs = retrieve_risk_category_definitions(top)
    score_by_id = {cat: score for cat, score in ranked}
    for d in defs:
        d["idf_score"] = round(_idf_weight(d["id"]), 4)
        d["rank_score"] = round(score_by_id.get(d["id"], 0.0), 4)
        d["tf"] = int(counts.get(d["id"], 0))
        d["df"] = int(_DOC_FREQ.get(d["id"], 0))
    return defs


def requirement_ids_for_risk_category(category: str, candidate_ids: list) -> list:
    """
    Given a RiskCategory local name and a list of candidate requirement IDs
    (typically the requirements actually retrieved/cited for a proposal),
    return the subset of those IDs whose ontology assertion (:hasRisk) names
    this category. Used for real provenance in generated documentation,
    instead of citing the category label as its own fake source.
    """
    if not category or not candidate_ids:
        return []
    values = " ".join(f'"{c}"' for c in candidate_ids)
    query = f"""
    SELECT ?rid WHERE {{
        VALUES ?rid {{ {values} }}
        ?req :requirementID ?rid .
        ?req :hasRisk :{category} .
    }}
    """
    results = sparql_query(query)
    found = {r.get("rid", {}).get("value", "") for r in results}
    # Preserve candidate order for deterministic output.
    return [c for c in candidate_ids if c in found]


def retrieve_all_for_proposal(proposal: str):
    """
    Full retrieval pipeline for a proposal.
    Returns: (requirements_list, incidents_list, matched_rights, keywords, risk_categories)
    """
    keywords = extract_keywords(proposal)
    matched_rights = get_matched_rights(keywords, proposal=proposal)
    disambiguation_path = get_matched_rights.last_disambiguation  # type: ignore[attr-defined]

    all_reqs = []
    seen_reqs = set()
    for right in matched_rights:
        reqs = retrieve_requirements_by_right(right)
        for r in reqs:
            req_id = r.get("reqID", {}).get("value", "")
            if req_id and req_id not in seen_reqs:
                seen_reqs.add(req_id)
                all_reqs.append({
                    "id": req_id,
                    "text": r.get("text", {}).get("value", ""),
                    "framework": r.get("framework", {}).get("value", ""),
                    "tier": r.get("tier", {}).get("value", ""),
                    "mandatory": r.get("mandatory", {}).get("value", ""),
                    "section_reference": r.get("sectionReference", {}).get("value", ""),
                    "risk_categories": _parse_risk_list(r),
                })

    all_incidents = []
    seen_incidents = set()
    for right in matched_rights[:6]:
        incidents = retrieve_incidents_by_right(right, limit=3)
        for inc in incidents:
            inc_id = inc.get("incID", {}).get("value", "")
            if inc_id and inc_id not in seen_incidents:
                seen_incidents.add(inc_id)
                all_incidents.append({
                    "id": inc_id,
                    "title": inc.get("title", {}).get("value", ""),
                    "risk_categories": _parse_risk_list(inc),
                })

    all_incidents = all_incidents[:8]
    risk_categories = retrieve_risk_categories_for_proposal(all_reqs, all_incidents)

    # Attach audit metadata on the risk_categories list object for callers that want it
    retrieve_all_for_proposal.last_disambiguation = disambiguation_path  # type: ignore[attr-defined]

    return all_reqs, all_incidents, matched_rights, keywords, risk_categories


retrieve_all_for_proposal.last_disambiguation = "not_applicable"  # type: ignore[attr-defined]


# ── SELF-TEST ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("SPARQL Retrieval Module — Self-Test (Phase 1+3)")
    print("=" * 60)

    print("\n1. Testing connection...")
    if not test_connection():
        exit(1)

    print("\n2. Testing keyword extraction...")
    test_text = "facial recognition system for hiring with personal data and employee staff workplace"
    kws = extract_keywords(test_text)
    print(f"  Keywords: {kws}")

    print("\n3. Testing rights mapping + Art31...")
    rights = get_matched_rights(kws, proposal=test_text)
    print(f"  Rights: {rights}")
    assert "Art31_FairWorkingConditions" in rights, "Art31 should fire for employee/staff/workplace"

    print("\n3b. Testing Art12 protest keywords...")
    protest = "Campus protest monitoring of student assembly and union organizing"
    pk = extract_keywords(protest)
    pr = get_matched_rights(pk, proposal=protest)
    print(f"  Keywords: {pk}")
    print(f"  Rights: {pr}")
    assert "Art12_FreedomOfAssembly" in pr, "Art12 should fire for protest/assembly"

    print("\n3c. Testing P13-style bias disambiguation (bibliometric)...")
    p13 = (
        "bibliometric analysis of peer-reviewed publications on AI ethics and algorithmic fairness. "
        "All data is publicly available metadata. No personal data. No AI systems will be developed."
    )
    k13 = extract_keywords(p13)
    r13 = get_matched_rights(k13, proposal=p13)
    print(f"  Keywords: {k13}")
    print(f"  Rights: {r13}")
    print(f"  Path: {get_matched_rights.last_disambiguation}")
    assert "Art21_NonDiscrimination" not in r13, "P13 should not surface Art21"

    print("\n4. Testing requirement retrieval (section + risk)...")
    reqs = retrieve_requirements_by_right("Art21_NonDiscrimination")
    print(f"  Requirements for Art21: {len(reqs)}")
    if reqs:
        sample = reqs[0]
        print(f"  Sample ID: {sample.get('reqID', {}).get('value', '')}")
        print(f"  sectionReference: {sample.get('sectionReference', {}).get('value', '')}")
        print(f"  riskCategories: {sample.get('riskCategories', {}).get('value', '')}")

    print("\n5. Testing full retrieval pipeline...")
    all_reqs, all_incs, all_rights, all_kws, all_risks = retrieve_all_for_proposal(test_text)
    print(f"  Keywords: {all_kws}")
    print(f"  Rights matched: {len(all_rights)}")
    print(f"  Requirements retrieved: {len(all_reqs)}")
    print(f"  Incidents retrieved: {len(all_incs)}")
    print(f"  Risk categories in scope: {[c['id'] for c in all_risks]}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED" if all_reqs else "SOME TESTS FAILED")
    print("=" * 60)
