"""
sparql_retrieval.py
Handles all SPARQL queries against local GraphDB Desktop.
Endpoint: http://localhost:7200/repositories/ai-ethics-kg
Namespace: https://w3id.org/aief/

Phase 1: retrieves sectionReference + risk categories (:hasRisk / :demonstratesRisk)
Phase 3: Charter rights disambiguation (bias→Art21 vs Art11/Art22) + Art12/Art31 triggers
"""

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
    "data":             ["Art8_DataProtection", "Art7_PrivateLife"],
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
    "scor":             ["Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy", "Art41_GoodAdministration"],
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
    "chatbot":          ["Art1_HumanDignity", "Art41_GoodAdministration"],
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
}

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


def extract_keywords(proposal: str) -> list:
    """Extract risk keywords from proposal text."""
    proposal_lower = proposal.lower()
    found = []
    for term in KEYWORD_TO_RIGHTS.keys():
        if term in proposal_lower:
            found.append(term)
    return found


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
    # also catch 'discriminat' substring keys
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

    # Ambiguous: prefer systemic downgrade when no clear individual harm mechanism
    # (addresses Delaram P13 critique — bibliometric "fairness" without individual treatment)
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
    """Map extracted keywords to Charter article IRIs, with Phase 3 disambiguation."""
    rights = set()
    # Soft defaults: only inject when relevant signal present (Phase 3 fix —
    # previously always injected Art41 + Art8, driving the Art21/governance skew)
    data_signals = {"privacy", "data", "personal data", "consent", "biometric",
                    "surveil", "monitor", "track", "patient", "student", "scraping",
                    "transfer", "cross-border", "profil"}
    admin_signals = {"transparen", "accountab", "explain", "chatbot", "scor"}
    if any(k in data_signals for k in keywords):
        rights.add("Art8_DataProtection")
    if any(k in admin_signals for k in keywords):
        rights.add("Art41_GoodAdministration")

    for kw in keywords:
        if kw in KEYWORD_TO_RIGHTS:
            rights.update(KEYWORD_TO_RIGHTS[kw])

    audit_path = "not_applicable"
    if proposal:
        rights, audit_path = disambiguate_bias_rights(proposal, rights, keywords)

    # Stash last audit path for callers (retrieve_all_for_proposal reads this)
    get_matched_rights.last_disambiguation = audit_path  # type: ignore[attr-defined]
    return sorted(list(rights))


get_matched_rights.last_disambiguation = "not_applicable"  # type: ignore[attr-defined]


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


def retrieve_risk_categories_for_proposal(reqs: list, incidents: list, top_n: int = 10) -> list:
    """
    Aggregate RiskCategory instances from retrieved requirements and incidents,
    with definitions. Scoped to this proposal's evidence (not the full taxonomy
    dump).

    High-recall proposals (e.g. those matching many Charter articles) can pull
    in most/all 27 RiskCategory subclasses simply because many requirements are
    retrieved. To keep the "risk categories in scope" list actually scoped to
    the proposal (rather than degenerating into the full taxonomy), categories
    are ranked by frequency of occurrence across matched requirements +
    incidents and only the top `top_n` are returned for use in the prompt.
    """
    from collections import Counter

    counts: Counter = Counter()
    for r in reqs:
        for cat in r.get("risk_categories", []) or []:
            counts[cat] += 1
    for inc in incidents:
        for cat in inc.get("risk_categories", []) or []:
            counts[cat] += 1

    # Stable order: highest frequency first, ties broken by first-seen order.
    first_seen = {}
    order = 0
    for r in reqs:
        for cat in r.get("risk_categories", []) or []:
            if cat not in first_seen:
                first_seen[cat] = order
                order += 1
    for inc in incidents:
        for cat in inc.get("risk_categories", []) or []:
            if cat not in first_seen:
                first_seen[cat] = order
                order += 1

    ranked = sorted(counts, key=lambda c: (-counts[c], first_seen[c]))

    # Frequency-based ranking structurally favors high-occurrence categories
    # (e.g. Accountability, PrivacyBreach) over rare-but-important ones
    # (e.g. Transparency), causing the latter to be crowded out of the top_n
    # cutoff even when they were genuinely retrieved for this proposal. An
    # expert reviewer specifically flagged this class of category as
    # systematically under-surfaced. To fix this without just hardcoding
    # these categories into every proposal, we guarantee inclusion only for
    # categories that were ACTUALLY retrieved (count > 0, i.e. present in
    # this proposal's matched requirements/incidents) and that belong to a
    # small allowlist of categories known to be under-surfaced by raw
    # frequency ranking. Remaining slots are still filled by frequency.
    ALWAYS_SURFACE_IF_PRESENT = {
        "Transparency",
        "EnvironmentalHarm",
        "Sustainability",
        "ChildrenRights",
    }

    guaranteed = [c for c in ranked if c in ALWAYS_SURFACE_IF_PRESENT]
    remainder = [c for c in ranked if c not in ALWAYS_SURFACE_IF_PRESENT]

    top = list(guaranteed)
    for c in remainder:
        if len(top) >= top_n:
            break
        top.append(c)
    # Preserve overall rank order (frequency, then first-seen) in final output
    top = [c for c in ranked if c in set(top)]

    return retrieve_risk_category_definitions(top)


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
