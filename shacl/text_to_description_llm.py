"""LLM-structured-extraction bridge: an alternative to text_to_description.py's
regex bridge, using Groq to extract the same structured predicates as JSON.

Ablation purpose: text_to_description.py is disclosed throughout the
dissertation as "naive regex, not NLU". This module tests whether replacing
it with LLM-based structured extraction measurably improves SHACL recall,
at the cost of reintroducing LLM dependency at the extraction stage --
undermining the "zero LLM involvement" claim for the SHACL layer specifically
in exchange for coverage. Both directions of that trade-off are reported,
not just the recall number.
"""
import json, os, re, sys, time
from openai import OpenAI

PREDICATES = {
    "involvesDataCategory": ["BiometricData", "HealthData"],
    "usesCapability": [
        "FacialRecognition", "ConversationalAgent", "ClinicalDecisionSupport",
        "ContinuousMonitoring", "AutomatedScreening", "CriminalJusticeRiskScoring",
        "LibertyAffectingDecision", "SafetyCriticalControl", "InvasiveIntervention",
        "ContentModeration", "UnlicensedDataUse", "LanguageProcessing",
        "WorkplaceMonitoring", "HighComputeTraining", "PublicSectorDecision",
    ],
    "involvesPopulation": ["Children", "Students", "GenderMinorities", "PeopleWithDisabilities"],
    "hasConsentMechanism": "boolean -- true only if proposal explicitly states consent IS obtained",
    "hasDPIA": "boolean -- true only if a DPIA has been conducted",
    "hasBiasAudit": "boolean -- true only if independent bias auditing has occurred",
    "hasClinicalValidation": "boolean -- true only if clinical validation is planned/done",
    "disclosesAIUse": "boolean -- true only if users are told they're interacting with AI",
    "hasIndividualOptOut": "boolean -- true only if an individual opt-out exists",
    "hasAppealMechanism": "boolean -- true only if an appeal/contest process exists",
    "hasAccessibilityDesign": "boolean -- true only if accessibility design is stated",
    "hasEnvironmentalAssessment": "boolean -- true only if an environmental assessment exists",
    "hasDataLicensing": "boolean -- true only if data licensing/rightsholder consent is stated",
}

PROMPT = """Extract structured facts from this AI research proposal description.
Return ONLY a JSON object with these keys (omit keys with no evidence):
- involvesDataCategory: list, subset of {data_cats}
- usesCapability: list, subset of {caps}
- involvesPopulation: list, subset of {pops}
- hasConsentMechanism, hasDPIA, hasBiasAudit, hasClinicalValidation, disclosesAIUse,
  hasIndividualOptOut, hasAppealMechanism, hasAccessibilityDesign,
  hasEnvironmentalAssessment, hasDataLicensing: boolean, TRUE ONLY if the proposal
  explicitly states this safeguard EXISTS (absence or silence = omit the key, do not
  set false)

Proposal:
{text}

JSON only, no prose:"""


def extract(text, client, model="llama-3.3-70b-versatile"):
    prompt = PROMPT.format(
        data_cats=PREDICATES["involvesDataCategory"],
        caps=PREDICATES["usesCapability"],
        pops=PREDICATES["involvesPopulation"],
        text=text[:2500],
    )
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
        temperature=0.0, max_tokens=400,
    )
    raw = resp.choices[0].message.content or "{}"
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


def to_ttl(facts):
    triples = []
    for cat in facts.get("involvesDataCategory", []):
        triples.append(f"aief:involvesDataCategory aief:{cat}")
    for cap in facts.get("usesCapability", []):
        triples.append(f"aief:usesCapability aief:{cap}")
    for pop in facts.get("involvesPopulation", []):
        triples.append(f"aief:involvesPopulation aief:{pop}")
    for key in ["hasConsentMechanism", "hasDPIA", "hasBiasAudit", "hasClinicalValidation",
                "disclosesAIUse", "hasIndividualOptOut", "hasAppealMechanism",
                "hasAccessibilityDesign", "hasEnvironmentalAssessment", "hasDataLicensing"]:
        if facts.get(key) is True:
            triples.append(f"aief:{key} true")
    triples = sorted(set(triples))
    return ("@prefix aief: <https://w3id.org/aief/> .\n\n"
            "aief:InputProposal a aief:ResearchProposal ;\n"
            + " ;\n".join(f"    {t}" for t in triples) + " .")


def describe(text, client=None):
    client = client or OpenAI(api_key=os.environ["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
    facts = extract(text, client)
    return to_ttl(facts)


if __name__ == "__main__":
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    print(describe(text))
