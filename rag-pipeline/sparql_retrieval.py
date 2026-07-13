"""
sparql_retrieval.py
Handles all SPARQL queries against local GraphDB Desktop.
Endpoint: http://localhost:7200/repositories/ai-ethics-kg
Namespace: https://w3id.org/aief/
"""

import requests

GRAPHDB_URL = "http://localhost:7200/repositories/ai-ethics-kg"

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
}


def sparql_query(query: str) -> list:
    """Execute a SPARQL query against local GraphDB and return bindings."""
    full_query = PREFIX + query
    try:
        response = requests.get(
            GRAPHDB_URL,
            headers={"Accept": "application/sparql-results+json"},
            params={"query": full_query},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["results"]["bindings"]
        else:
            print(f"  [SPARQL ERROR] Status {response.status_code}: {response.text[:200]}")
            return []
    except requests.exceptions.ConnectionError:
        print("  [SPARQL ERROR] Cannot connect to GraphDB at http://localhost:7200")
        print("  Make sure GraphDB Desktop is running.")
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


def get_matched_rights(keywords: list) -> list:
    """Map extracted keywords to Charter article IRIs."""
    rights = set()
    # Always include core governance rights
    rights.add("Art41_GoodAdministration")
    rights.add("Art8_DataProtection")
    for kw in keywords:
        if kw in KEYWORD_TO_RIGHTS:
            rights.update(KEYWORD_TO_RIGHTS[kw])
    return sorted(list(rights))


def retrieve_requirements_by_right(charter_article: str) -> list:
    """Get all requirements mapped to a given Charter right."""
    query = f"""
    SELECT ?reqID ?text ?framework ?tier ?mandatory WHERE {{
        ?req :mapsToRight :{charter_article} ;
             :requirementID ?reqID ;
             :requirementText ?text ;
             :belongsToFramework ?fw ;
             :hasTier ?tierNode ;
             :isMandatory ?mandatory .
        BIND(STRAFTER(STR(?fw), "/aief/") AS ?framework)
        BIND(STRAFTER(STR(?tierNode), "/aief/") AS ?tier)
    }}
    ORDER BY ?reqID
    """
    return sparql_query(query)


def retrieve_incidents_by_right(charter_article: str, limit: int = 3) -> list:
    """Get incidents impacting a given Charter right."""
    query = f"""
    SELECT ?incID ?title WHERE {{
        ?inc a :Incident ;
             :incidentID ?incID ;
             :incidentTitle ?title ;
             :impactsRight :{charter_article} .
    }}
    LIMIT {limit}
    """
    return sparql_query(query)


def retrieve_all_for_proposal(proposal: str):
    """
    Full retrieval pipeline for a proposal.
    Returns: (requirements_list, incidents_list, matched_rights, keywords)
    """
    # Step 1: Extract keywords
    keywords = extract_keywords(proposal)

    # Step 2: Map to rights
    matched_rights = get_matched_rights(keywords)

    # Step 3: Retrieve requirements for each right
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
                    "mandatory": r.get("mandatory", {}).get("value", "")
                })

    # Step 4: Retrieve incidents for top rights (limit to avoid overload)
    all_incidents = []
    seen_incidents = set()
    for right in matched_rights[:6]:  # top 6 rights
        incidents = retrieve_incidents_by_right(right, limit=3)
        for inc in incidents:
            inc_id = inc.get("incID", {}).get("value", "")
            if inc_id and inc_id not in seen_incidents:
                seen_incidents.add(inc_id)
                all_incidents.append({
                    "id": inc_id,
                    "title": inc.get("title", {}).get("value", "")
                })

    # Cap incidents at 8 to keep prompt manageable
    all_incidents = all_incidents[:8]

    return all_reqs, all_incidents, matched_rights, keywords


# ── SELF-TEST ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("SPARQL Retrieval Module — Self-Test")
    print("=" * 60)

    print("\n1. Testing connection...")
    if not test_connection():
        exit(1)

    print("\n2. Testing keyword extraction...")
    test_text = "facial recognition system for hiring with personal data"
    kws = extract_keywords(test_text)
    print(f"  Keywords: {kws}")

    print("\n3. Testing rights mapping...")
    rights = get_matched_rights(kws)
    print(f"  Rights: {rights}")

    print("\n4. Testing requirement retrieval...")
    reqs = retrieve_requirements_by_right("Art21_NonDiscrimination")
    print(f"  Requirements for Art21: {len(reqs)}")
    if reqs:
        print(f"  Sample: {reqs[0].get('reqID', {}).get('value', '')}: {reqs[0].get('text', {}).get('value', '')[:80]}...")

    print("\n5. Testing incident retrieval...")
    incs = retrieve_incidents_by_right("Art21_NonDiscrimination")
    print(f"  Incidents for Art21: {len(incs)}")
    if incs:
        for i in incs:
            print(f"  - {i.get('incID', {}).get('value', '')}: {i.get('title', {}).get('value', '')}")

    print("\n6. Testing full retrieval pipeline...")
    all_reqs, all_incs, all_rights, all_kws = retrieve_all_for_proposal(test_text)
    print(f"  Keywords: {all_kws}")
    print(f"  Rights matched: {len(all_rights)}")
    print(f"  Requirements retrieved: {len(all_reqs)}")
    print(f"  Incidents retrieved: {len(all_incs)}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED" if all_reqs else "SOME TESTS FAILED")
    print("=" * 60)
