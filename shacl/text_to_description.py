"""Materialise a structured proposal description (TTL) from free text,
using the same keyword heuristics as the retrieval stage."""
import sys, re

RULES = [  # (regex on proposal text, triple to emit)
    (r"biometric|facial recogn|fingerprint", "aief:involvesDataCategory aief:BiometricData"),
    (r"health|medical|clinical|patient|mental", "aief:involvesDataCategory aief:HealthData"),
    (r"child|minor|school|under 18|adolescent", "aief:involvesPopulation aief:Children"),
    (r"student", "aief:involvesPopulation aief:Students"),
    (r"facial recogn", "aief:usesCapability aief:FacialRecognition"),
    (r"chatbot|conversational", "aief:usesCapability aief:ConversationalAgent"),
    (r"clinical decision|diagnos|triage", "aief:usesCapability aief:ClinicalDecisionSupport"),
    (r"monitor|surveil|cctv|track", "aief:usesCapability aief:ContinuousMonitoring"),
    (r"hiring|recruit|screening", "aief:usesCapability aief:AutomatedScreening"),
    # positive-evidence flags: only asserted when text states them
    (r"opt-in consent|informed consent obtained|consent will be obtained", "aief:hasConsentMechanism true"),
    (r"DPIA|data protection impact assessment (has been|was) conducted", "aief:hasDPIA true"),
    (r"bias audit|audited for.*bias", "aief:hasBiasAudit true"),
    (r"clinical (validation|trial) (is|has been|was) (planned|conducted)", "aief:hasClinicalValidation true"),
    (r"disclaimer|disclosed? (that|as) (an )?AI", "aief:disclosesAIUse true"),
    (r"opt-out", "aief:hasIndividualOptOut true"),
]

# Positive-evidence predicates: skip if the match is under naive negation
# (known limitation — regex, not NLU; same class as keyword retrieval).
_NEG = re.compile(r"\b(without|no|not|lack(?:ing)?|absent)\b.{0,40}$", re.I)

text = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
t = text.lower()
triples = set()
for rx, obj in RULES:
    m = re.search(rx, t)
    if not m:
        continue
    if obj.startswith("aief:has") or obj.startswith("aief:discloses"):
        prefix = t[max(0, m.start() - 40):m.start()]
        if _NEG.search(prefix):
            continue
    triples.add(obj)
triples = sorted(triples)
print("@prefix aief: <https://w3id.org/aief/> .\n")
print("aief:InputProposal a aief:ResearchProposal ;")
print(" ;\n".join(f"    {tr}" for tr in triples) + " .")
