"""
corpus_expansion.py
Grow the evaluation corpus from 20 to 40 proposals, targeting gaps in the
existing set (Medium/Low under-representation, contested Charter cases,
non-Western contexts, framework-tension cases).

Thesis pinned: An evaluation protocol that scores an automated assessor
against reference labels is itself a measurement instrument, and its validity
depends on conditions — chiefly, the reliability of those reference labels —
that are not currently checked before such protocols are used.

The diagnostic methodology checks that condition. This script only expands
the labelled corpus the diagnostic will later use.

Usage:
  python corpus_expansion.py            # validate + write synthetic_proposals_extended.py
  python corpus_expansion.py --draft    # optional: LLM-draft then pause for GT review
"""

from __future__ import annotations

import argparse
import importlib.util
import pprint
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAG = ROOT.parent / "rag-pipeline"
sys.path.insert(0, str(RAG))

from synthetic_proposals import PROPOSALS as ORIGINAL  # noqa: E402

ORIGINAL_KEYS = [
    "id",
    "title",
    "risk_level",
    "source",
    "proposal_text",
    "expected_requirements",
    "expected_rights",
    "expected_charter_articles",
    "expected_risks",
    "expected_risk_categories",
]
NEW_KEYS = ["info_sufficiency_expected", "rationale"]
ALL_KEYS = ORIGINAL_KEYS + NEW_KEYS

SYNTHETIC_SOURCE = (
    "Synthetic illustrative case constructed for the AIEF evaluation corpus (2026)."
)

# Backfill for the original 20 (quick pass; not shown to annotators).
ORIGINAL_BACKFILL = {
    "P01": (5, "Well-documented racial bias via cost proxy; articles and risks are clear."),
    "P02": (5, "Proprietary recidivism tool with documented disparate false-positive rates."),
    "P03": (5, "Law-enforcement facial recognition with published false-match audit."),
    "P04": (4, "Ad-delivery optimisation produces demographic skew without explicit protected attributes."),
    "P05": (4, "Clinical sepsis model with under-represented minority training data."),
    "P06": (4, "Classroom emotion recognition on minors without individual opt-out."),
    "P07": (3, "Retrospective essay NLP; consent and discrimination risks are partially specified."),
    "P08": (3, "Mental-health triage chatbot; clinical validation gap is stated but severity is judgemental."),
    "P09": (3, "Module recommender on historical records; consent gap clear, harm pathway less so."),
    "P10": (3, "Misinformation detector; expression vs safety trade-off is contested."),
    "P11": (4, "Automated grading with L1 bias and no AI-specific appeal path."),
    "P12": (4, "Bed allocation using medical-card status as a socioeconomic proxy."),
    "P13": (5, "Bibliometric metadata only; no personal data or deployment."),
    "P14": (5, "Literature-screening tool on public abstracts; no personal data."),
    "P15": (5, "Aggregated open transport counts; re-identification not feasible as described."),
    "P16": (5, "Public climate datasets; environmental documentation only."),
    "P17": (2, "Dual-use extremist-content classifier; Art.11 vs safety is genuinely contested."),
    "P18": (4, "Autonomous research agent with weak guardrails; accountability risks clear."),
    "P19": (4, "Cross-border genomic sharing with reconstruction-attack risk stated."),
    "P20": (3, "Workplace monitoring with formal consent but power-imbalance voluntariness contested."),
}


# ── 20 new proposals targeting corpus gaps ───────────────────────────────────
# Distribution target: more Medium/Low; non-Western; contested; framework tension.
NEW_PROPOSALS = [
    {
        "id": "P21",
        "title": "Mobile-Money Credit Scoring in Kenya",
        "risk_level": "Medium",
        "source": (
            "Illustrative case informed by: Berg, T. et al. (2020). On the Rise of "
            "FinTechs—Credit Scoring Using Digital Footprints. Review of Financial Studies; "
            "and Kenya Data Protection Act 2019 debates on alternative-data lending."
        ),
        "proposal_text": (
            "This research proposes to develop a machine learning credit-scoring model for "
            "a Nairobi-based digital lender serving unbanked and underbanked borrowers across "
            "Kenya. The model will predict default risk from mobile-money transaction histories, "
            "airtime purchase patterns, geolocation of cash-in/cash-out agents, phone contacts "
            "graph density, and device metadata. Training data cover approximately 2.4 million "
            "customers of a partner mobile-network operator, collected under the operator's "
            "terms of service rather than purpose-specific lending consent. Loan approval and "
            "pricing decisions will be fully automated for amounts under KES 50,000, with no "
            "human review unless the applicant formally complains. The researchers note that "
            "contact-graph features may encode ethnicity and socioeconomic clustering in urban "
            "informal settlements, but no demographic fairness audit across ethnic groups or "
            "counties is planned before pilot launch. Rejected applicants will receive a "
            "generic adverse-action notice without feature-level explanation. The study "
            "protocol has not yet been reviewed against the Kenya Data Protection Act 2019 "
            "or the EU Charter articles that would apply if the same pipeline were later "
            "ported to an EU migrant-lending product."
        ),
        "expected_requirements": ["R027", "R042", "R054", "R071", "R085", "AI001", "AI016", "HE012", "ACM001", "ACM002"],
        "expected_rights": ["Art21_NonDiscrimination", "Art8_DataProtection", "Art47_RightToEffectiveRemedy", "Art15_FreedomOfOccupation"],
        "expected_charter_articles": ["Art21_NonDiscrimination", "Art8_DataProtection", "Art47_RightToEffectiveRemedy", "Art15_FreedomOfOccupation"],
        "expected_risks": ["Discrimination", "EconomicHarm", "PrivacyBreach"],
        "expected_risk_categories": ["Discrimination", "EconomicHarm", "PrivacyBreach"],
        "info_sufficiency_expected": 4,
        "rationale": "Automated lending on alternative data with contact-graph proxies is a clear Medium-risk discrimination and remedy case in a non-Western deployment context.",
    },
    {
        "id": "P22",
        "title": "Hiring Ranking Model with Caste-Correlated Proxies in India",
        "risk_level": "High",
        "source": (
            "Illustrative case informed by Indian IT hiring audits and debates on caste "
            "discrimination in algorithmic recruitment (e.g. coverage in The Wire / Scroll "
            "on surname and education-network proxies)."
        ),
        "proposal_text": (
            "This research proposes to deploy a resume-ranking and interview-shortlisting "
            "model across three large technology employers in Bengaluru and Hyderabad. The "
            "model scores applicants using educational institution prestige, pin-code of "
            "permanent address, parental occupation fields scraped from optional profile "
            "forms, English-fluency estimates from writing samples, and historical hire "
            "outcomes. Caste is not an explicit feature. Independent auditors have previously "
            "shown that pin-code and institution features correlate strongly with "
            "Scheduled-Caste and Scheduled-Tribe membership in several Indian metros. The "
            "system will auto-reject the bottom 60% of applicants before any human recruiter "
            "sees the file. Candidates will not be told that an algorithmic gate was used. "
            "No caste-disaggregated fairness evaluation is included in the deployment plan, "
            "and the employers assert that Indian constitutional protections against caste "
            "discrimination do not require algorithmic audits. The research team has not "
            "consulted Dalit or Adivasi employee resource groups."
        ),
        "expected_requirements": ["R010", "R027", "R042", "R054", "R071", "R085", "AI001", "AI016", "AI021", "HE012", "ACM001", "ACM002"],
        "expected_rights": ["Art21_NonDiscrimination", "Art15_FreedomOfOccupation", "Art47_RightToEffectiveRemedy", "Art1_HumanDignity"],
        "expected_charter_articles": ["Art21_NonDiscrimination", "Art15_FreedomOfOccupation", "Art47_RightToEffectiveRemedy", "Art1_HumanDignity"],
        "expected_risks": ["Discrimination", "EmploymentHarm"],
        "expected_risk_categories": ["Discrimination", "EmploymentHarm"],
        "info_sufficiency_expected": 4,
        "rationale": "High-risk automated hiring gate with documented proxy discrimination pathway in a non-Western (India) context.",
    },
    {
        "id": "P23",
        "title": "Social-Benefit Eligibility Triage in Brazil",
        "risk_level": "Medium",
        "source": (
            "Illustrative case informed by Brazil Cadastro Único / Bolsa Família digitalisation "
            "debates and Latin American social-protection algorithmic targeting literature."
        ),
        "proposal_text": (
            "This project proposes a machine learning triage layer for a municipal social-"
            "assistance programme in São Paulo that prioritises home visits for families "
            "seeking cash-transfer enrolment. The model uses Cadastro Único registry fields, "
            "utility payment irregularities, school attendance flags, and neighbourhood "
            "vulnerability indices to score 'urgency'. Caseworkers will be instructed to "
            "follow the ranked list unless they document an override. Families scored as "
            "low-urgency may wait months for a visit. The training labels come from past "
            "caseworker decisions, which community organisations argue systematically "
            "under-served favelas and Afro-Brazilian households. No disparate-impact audit "
            "by race or territory is scheduled. Applicants cannot see their score or appeal "
            "the triage ranking—only the eventual eligibility decision after a visit. The "
            "proposal notes tension with EU-style fundamental-rights impact assessment "
            "expectations if the same pipeline were adapted under a Horizon Europe "
            "social-innovation grant."
        ),
        "expected_requirements": ["R027", "R042", "R054", "R071", "R085", "AI001", "AI016", "HE012", "HE015", "ACM001"],
        "expected_rights": ["Art21_NonDiscrimination", "Art1_HumanDignity", "Art47_RightToEffectiveRemedy", "Art8_DataProtection"],
        "expected_charter_articles": ["Art21_NonDiscrimination", "Art1_HumanDignity", "Art47_RightToEffectiveRemedy", "Art8_DataProtection"],
        "expected_risks": ["Discrimination", "EconomicHarm", "Accountability"],
        "expected_risk_categories": ["Discrimination", "EconomicHarm", "Accountability"],
        "info_sufficiency_expected": 4,
        "rationale": "Medium-risk welfare triage with proxy discrimination and weak appeal; non-Western (Brazil) plus FRIA/Horizon tension note.",
    },
    {
        "id": "P24",
        "title": "Remote Exam Proctoring Across Southeast Asian Universities",
        "risk_level": "Medium",
        "source": (
            "Illustrative case informed by Proctorio/ExamSoft controversies and ASEAN "
            "university emergency remote-assessment practices during and after COVID-19."
        ),
        "proposal_text": (
            "This research proposes a shared remote-proctoring platform for five public "
            "universities in Indonesia, Malaysia, and the Philippines. During timed exams, "
            "the system records webcam video, microphone audio, screen activity, and "
            "keystroke dynamics, flagging 'suspicious behaviour' via a proprietary model "
            "trained primarily on North American student footage. Flagged sessions are "
            "queued for human review; unflagged sessions are auto-cleared. Students in "
            "shared housing report false flags when family members enter the frame. The "
            "model has not been validated on darker skin tones under typical tropical "
            "indoor lighting. Students must accept continuous recording to sit the exam; "
            "no alternative invigilation path is offered. Recordings are retained for "
            "twelve months on a Singapore cloud vendor. Universities have not published "
            "false-positive rates by campus or demographic group."
        ),
        "expected_requirements": ["R027", "R042", "R043", "R054", "R071", "AI001", "AI011", "AI016", "HE007", "ACM004"],
        "expected_rights": ["Art7_PrivateLife", "Art8_DataProtection", "Art21_NonDiscrimination", "Art1_HumanDignity"],
        "expected_charter_articles": ["Art7_PrivateLife", "Art8_DataProtection", "Art21_NonDiscrimination", "Art1_HumanDignity"],
        "expected_risks": ["PrivacyBreach", "Discrimination", "Surveillance"],
        "expected_risk_categories": ["PrivacyBreach", "Discrimination", "Surveillance"],
        "info_sufficiency_expected": 4,
        "rationale": "Medium-risk biometric-adjacent proctoring with demographic validation gaps in Southeast Asia.",
    },
    {
        "id": "P25",
        "title": "Arabic Social-Media Extremism Classifier for MENA Platforms",
        "risk_level": "High",
        "source": (
            "Illustrative dual-use case informed by Arabic NLP moderation research and "
            "civil-society critiques of over-blocking political speech in MENA contexts."
        ),
        "proposal_text": (
            "This research proposes an Arabic-dialect NLP classifier to detect extremist "
            "recruitment and glorification of violence on public Telegram channels and "
            "X/Twitter accounts across Egypt, Jordan, and Morocco. Training data mix "
            "annotated jihadist propaganda with posts from secular activists, Islamist "
            "electoral campaigns, and satire. The classifier will output a risk score used "
            "by platform trust-and-safety teams to prioritise human review; scores above "
            "0.85 will auto-suspend accounts for 48 hours pending review. Civil-society "
            "partners warn that dialectal sarcasm and anti-regime protest slogans are "
            "frequently mislabelled. The team plans open-source release of the model "
            "weights. No engagement with journalists' unions or minority-rights groups "
            "is scheduled. Whether Art.11 freedom of expression or public-security "
            "limitations should dominate the rights analysis is deliberately left open "
            "in the protocol—experts disagree."
        ),
        "expected_requirements": ["R001", "R010", "R019", "R027", "R054", "R071", "AI001", "HE005", "HE019", "ACM020", "ACM025"],
        "expected_rights": ["Art11_FreedomOfExpression", "Art12_FreedomOfAssembly", "Art21_NonDiscrimination", "Art7_PrivateLife"],
        "expected_charter_articles": ["Art11_FreedomOfExpression", "Art12_FreedomOfAssembly", "Art21_NonDiscrimination", "Art7_PrivateLife"],
        "expected_risks": ["ExpressionHarm", "Discrimination", "DualUseMisuse"],
        "expected_risk_categories": ["ExpressionHarm", "Discrimination", "DualUseMisuse"],
        "info_sufficiency_expected": 2,
        "rationale": "Deliberately contested High-risk dual-use moderation case; Art.11 vs security is expert-disputed even with adequate text.",
    },
    {
        "id": "P26",
        "title": "Smallholder Crop-Advisory Chatbot in Rural India",
        "risk_level": "Low",
        "source": (
            "Illustrative case informed by Indian agri-advisory chatbots (e.g. Kisan Call "
            "Centre digitisation) and FAO discussions of AI for smallholder extension."
        ),
        "proposal_text": (
            "This project proposes a WhatsApp-based crop-advisory chatbot for smallholder "
            "farmers in Maharashtra and Odisha. The bot answers irrigation, pest, and "
            "market-price questions using retrieval over public agricultural extension "
            "bulletins and open weather APIs. Conversations are logged in aggregate for "
            "service improvement; phone numbers are hashed after 30 days. No credit, "
            "subsidy, or enforcement decisions are attached to bot use. A subtle residual "
            "issue is that incorrect pest-treatment advice could cause crop loss for "
            "farmers who treat the bot as authoritative, yet the interface presents answers "
            "with high confidence and no uncertainty bands. The team will run a small "
            "accuracy pilot against agronomist answers but has not planned liability or "
            "escalation pathways when advice fails. No personal land-holding registries "
            "are ingested."
        ),
        "expected_requirements": ["R001", "R054", "R057", "AI008", "HE023", "ACM018"],
        "expected_rights": ["Art1_HumanDignity", "Art8_DataProtection"],
        "expected_charter_articles": ["Art1_HumanDignity", "Art8_DataProtection"],
        "expected_risks": ["Accountability"],
        "expected_risk_categories": ["Accountability"],
        "info_sufficiency_expected": 3,
        "rationale": "Mostly Low-risk advisory tool; subtle over-confidence/accountability issue tests under-flagging.",
    },
    {
        "id": "P27",
        "title": "Horizon Europe Biometric FRIA vs Open-Science Tension Study",
        "risk_level": "High",
        "source": (
            "Synthetic case constructed to instantiate tension between EU AI Act Art.27 "
            "fundamental-rights impact assessment expectations for high-risk biometric "
            "systems and Horizon Europe open-science / data-sharing mandates."
        ),
        "proposal_text": (
            "This Horizon Europe consortium proposes a multi-site study of gait-and-face "
            "biometrics to recognise patients with rare neurological disorders across "
            "clinics in Ireland, Germany, and Spain. The technical work package will train "
            "a multimodal recognition model on clinic video and release model checkpoints "
            "and a 'de-identified' embedding database under an open-science deliverable "
            "required by the grant agreement. A parallel ethics work package notes that "
            "the same system may qualify as high-risk biometric categorisation under the "
            "EU AI Act, triggering an Art.27-style fundamental-rights impact assessment "
            "(FRIA) and possibly restricting public release of embeddings. The consortium "
            "has not resolved whether open deliverables or FRIA containment wins when they "
            "conflict. Patient consent forms mention research use but not public model "
            "release. No independent FRIA has been completed before the first data freeze."
        ),
        "expected_requirements": ["R005", "R023", "R027", "R042", "R054", "R071", "AI011", "AI013", "HE007", "HE008", "HE009", "ACM003", "ACM008"],
        "expected_rights": ["Art8_DataProtection", "Art7_PrivateLife", "Art35_HealthCare", "Art1_HumanDignity"],
        "expected_charter_articles": ["Art8_DataProtection", "Art7_PrivateLife", "Art35_HealthCare", "Art1_HumanDignity"],
        "expected_risks": ["PrivacyBreach", "DataBreach", "FunctionCreep"],
        "expected_risk_categories": ["PrivacyBreach", "DataBreach", "FunctionCreep"],
        "info_sufficiency_expected": 3,
        "rationale": "Framework-tension case (AI Act FRIA vs Horizon open science); High risk, contested compliance path.",
    },
    {
        "id": "P28",
        "title": "Municipal Permit Chatbot in Bogotá",
        "risk_level": "Medium",
        "source": (
            "Illustrative case informed by Latin American govtech chatbot deployments and "
            "OAS/IDB discussions of automated administrative decisions."
        ),
        "proposal_text": (
            "This research proposes a Spanish-language LLM chatbot that guides Bogotá "
            "residents through business-permit and construction-licence applications. The "
            "bot classifies query intent, retrieves municipal code passages, and drafts "
            "application forms. In a pilot ward, incomplete answers that the bot labels "
            "'likely ineligible' will auto-close the digital ticket without human review "
            "to reduce backlog. Residents with limited literacy or non-standard Spanish "
            "dialects may be disproportionately auto-closed. Conversation logs retain "
            "national ID numbers entered into forms. The city asserts the bot is 'advisory "
            "only,' yet ticket closure has the practical effect of a refusal. No "
            "administrative-appeal pathway specific to bot closures is described."
        ),
        "expected_requirements": ["R027", "R042", "R054", "R071", "AI001", "AI017", "HE011", "ACM013"],
        "expected_rights": ["Art41_GoodAdministration", "Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy", "Art8_DataProtection"],
        "expected_charter_articles": ["Art41_GoodAdministration", "Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy", "Art8_DataProtection"],
        "expected_risks": ["Accountability", "Discrimination", "PrivacyBreach"],
        "expected_risk_categories": ["Accountability", "Discrimination", "PrivacyBreach"],
        "info_sufficiency_expected": 4,
        "rationale": "Medium-risk automated administrative gatekeeping with remedy and discrimination concerns in LatAm.",
    },
    {
        "id": "P29",
        "title": "Community Safety Hotspot Analytics without Arrest Prediction",
        "risk_level": "Medium",
        "source": (
            "Illustrative contested case at the boundary of predictive policing critiques "
            "(e.g. Lum & Isaac; Chicago SSL debates) reframed as 'resource allocation'."
        ),
        "proposal_text": (
            "This project proposes a 'community safety analytics' dashboard for a mid-sized "
            "EU city police service. The model forecasts week-ahead geographic concentrations "
            "of emergency calls using historical CAD data, weather, and event calendars. "
            "Outputs are heat maps for patrol allocation, not individual risk scores. "
            "Civil-liberties groups argue the system recapitulates predictive policing by "
            "intensifying presence in already over-policed neighbourhoods; the police "
            "service argues it only allocates scarce ambulances and officers to call "
            "volume. No individual surveillance cameras or stop-and-search recommendations "
            "are generated. Historical call data embed prior discriminatory deployment "
            "patterns. Whether Art.6 liberty, Art.21 non-discrimination, or neither is "
            "primarily engaged is contested among reasonable experts given the "
            "aggregate-only design."
        ),
        "expected_requirements": ["R010", "R027", "R042", "R054", "R071", "AI001", "HE005", "ACM001"],
        "expected_rights": ["Art21_NonDiscrimination", "Art6_RightToLiberty", "Art8_DataProtection"],
        "expected_charter_articles": ["Art21_NonDiscrimination", "Art6_RightToLiberty", "Art8_DataProtection"],
        "expected_risks": ["Discrimination", "Surveillance", "LibertyViolation"],
        "expected_risk_categories": ["Discrimination", "Surveillance", "LibertyViolation"],
        "info_sufficiency_expected": 2,
        "rationale": "Deliberately contested Medium case: aggregate hotspotting vs predictive policing; article engagement disputed.",
    },
    {
        "id": "P30",
        "title": "Health Insurance Risk Pricing in South Africa",
        "risk_level": "High",
        "source": (
            "Illustrative case informed by South African medical-scheme risk-rating debates "
            "and broader literature on algorithmic insurance discrimination."
        ),
        "proposal_text": (
            "This research proposes a gradient-boosting model to set individual loading "
            "factors for a private medical scheme in Johannesburg and Cape Town. Features "
            "include claims history, pharmacy fills, wearable step counts (opt-in), and "
            "residential suburb codes. Race is not an input, but suburb codes strongly "
            "proxy apartheid-era spatial segregation. Members in the highest predicted-cost "
            "decile face premium increases up to 40% or coverage exclusions for elective "
            "procedures. The scheme plans no suburb- or race-disaggregated fairness audit, "
            "citing proprietary actuarial practice. Members cannot obtain a meaningful "
            "explanation of their loading beyond 'actuarial risk.' The National Health "
            "Insurance reform context makes the private-scheme impact politically sensitive."
        ),
        "expected_requirements": ["R027", "R042", "R054", "R071", "R085", "AI001", "AI016", "AI021", "HE012", "ACM001", "ACM002"],
        "expected_rights": ["Art21_NonDiscrimination", "Art35_HealthCare", "Art8_DataProtection", "Art47_RightToEffectiveRemedy"],
        "expected_charter_articles": ["Art21_NonDiscrimination", "Art35_HealthCare", "Art8_DataProtection", "Art47_RightToEffectiveRemedy"],
        "expected_risks": ["Discrimination", "EconomicHarm", "PhysicalHarm"],
        "expected_risk_categories": ["Discrimination", "EconomicHarm", "PhysicalHarm"],
        "info_sufficiency_expected": 4,
        "rationale": "High-risk insurance pricing with spatial proxies for race in South Africa; health and remedy articles clear.",
    },
    {
        "id": "P31",
        "title": "Open African-Languages Speech Corpus with Personal Narratives",
        "risk_level": "Low",
        "source": (
            "Illustrative case informed by Masakhane / Mozilla Common Voice African-language "
            "corpus efforts and consent debates around narrative speech data."
        ),
        "proposal_text": (
            "This project will release an open speech corpus of 400 hours across Yoruba, "
            "Igbo, and Swahili for ASR research. Speakers are paid volunteers who record "
            "scripted sentences and optional two-minute personal stories about family and "
            "work. Scripts are public-domain; personal stories may contain names, employers, "
            "and locations. Release includes raw audio under CC-BY with speaker IDs replaced "
            "by codes. A subtle issue: re-identification via voice biometrics plus story "
            "content is possible for well-known community members, but the datasheet treats "
            "the corpus as anonymised. No voice-biometric risk assessment is planned. "
            "Otherwise the project is standard open-science language resource work with "
            "no downstream decision system."
        ),
        "expected_requirements": ["R001", "R005", "R023", "R057", "HE007", "HE023", "ACM003"],
        "expected_rights": ["Art8_DataProtection", "Art7_PrivateLife"],
        "expected_charter_articles": ["Art8_DataProtection", "Art7_PrivateLife"],
        "expected_risks": ["PrivacyBreach"],
        "expected_risk_categories": ["PrivacyBreach"],
        "info_sufficiency_expected": 3,
        "rationale": "Low-risk open corpus with a subtle re-identification/voice issue to test under-flagging.",
    },
    {
        "id": "P32",
        "title": "Aggregated Mobile-Money Flow Heatmaps for Urban Planning",
        "risk_level": "Low",
        "source": (
            "Illustrative case informed by GSMA mobile-money analytics and urban-planning "
            "uses of aggregated transaction heatmaps in East Africa."
        ),
        "proposal_text": (
            "This research proposes to publish weekly heatmaps of mobile-money cash-in and "
            "cash-out volumes at 500-metre grid cells for Kampala, using operator data "
            "aggregated under a national statistics memorandum. No individual wallet IDs "
            "are released. The stated purpose is transit and market-infrastructure planning. "
            "A subtle residual risk is that thin cells in peri-urban areas may still permit "
            "inference about specific large traders when combined with public business "
            "registries, yet the proposal asserts 'full anonymisation by aggregation.' "
            "No attacker model or k-anonymity threshold is specified. No enforcement or "
            "tax authority use is planned in the research protocol."
        ),
        "expected_requirements": ["R001", "R005", "R023", "R057", "HE007", "HE023"],
        "expected_rights": ["Art8_DataProtection", "Art7_PrivateLife"],
        "expected_charter_articles": ["Art8_DataProtection", "Art7_PrivateLife"],
        "expected_risks": ["PrivacyBreach"],
        "expected_risk_categories": ["PrivacyBreach"],
        "info_sufficiency_expected": 2,
        "rationale": "Low-risk aggregated statistics with under-specified re-identification residual; info-thin by design.",
    },
    {
        "id": "P33",
        "title": "University FAQ Chatbot Logging Student Queries",
        "risk_level": "Low",
        "source": SYNTHETIC_SOURCE,
        "proposal_text": (
            "This project proposes an on-campus FAQ chatbot answering timetable, fee, and "
            "library questions for undergraduate students. Queries are answered from a "
            "curated knowledge base. For 'service improvement,' the system stores raw query "
            "text linked to student ID for twelve months. Most queries are mundane, but "
            "logs will inevitably include questions about mitigating circumstances, "
            "disability supports, and mental-health services. Students see a cookie-style "
            "banner but no granular opt-out from identifiable logging while still using "
            "the bot. No model makes academic decisions. The subtle issue is purpose "
            "creep and sensitive-query retention rather than high-stakes automation."
        ),
        "expected_requirements": ["R005", "R023", "R027", "R042", "HE007", "ACM003"],
        "expected_rights": ["Art8_DataProtection", "Art7_PrivateLife"],
        "expected_charter_articles": ["Art8_DataProtection", "Art7_PrivateLife"],
        "expected_risks": ["PrivacyBreach", "FunctionCreep"],
        "expected_risk_categories": ["PrivacyBreach", "FunctionCreep"],
        "info_sufficiency_expected": 3,
        "rationale": "Low-risk campus chatbot with subtle identifiable sensitive-query logging.",
    },
    {
        "id": "P34",
        "title": "Clickstream Engagement Analytics without Cameras",
        "risk_level": "Low",
        "source": SYNTHETIC_SOURCE,
        "proposal_text": (
            "This research proposes clickstream-only 'engagement analytics' for an online "
            "continuing-education platform: page dwell time, quiz retries, and forum posts. "
            "No webcam or emotion recognition is used. Instructors see per-student engagement "
            "scores that may inform outreach emails. Scores are not used for formal grading. "
            "A subtle issue is that engagement proxies can disadvantage students with "
            "disability-related interaction patterns or shared-device access, and outreach "
            "based on low scores may feel surveillant. The proposal does not discuss "
            "reasonable-accommodation effects. Data stay on the university LMS."
        ),
        "expected_requirements": ["R027", "R042", "R054", "HE007", "ACM003"],
        "expected_rights": ["Art8_DataProtection", "Art21_NonDiscrimination", "Art7_PrivateLife"],
        "expected_charter_articles": ["Art8_DataProtection", "Art21_NonDiscrimination", "Art7_PrivateLife"],
        "expected_risks": ["Discrimination", "PrivacyBreach"],
        "expected_risk_categories": ["Discrimination", "PrivacyBreach"],
        "info_sufficiency_expected": 3,
        "rationale": "Low-risk LMS analytics with subtle disability/discrimination pathway; tests over/under-flagging.",
    },
    {
        "id": "P35",
        "title": "Synthetic Clinical Notes for NLP Training",
        "risk_level": "Medium",
        "source": (
            "Illustrative case informed by synthetic EHR / clinical NLP literature and "
            "membership-inference concerns for generative clinical text."
        ),
        "proposal_text": (
            "This project fine-tunes a large language model on 1.2 million de-identified "
            "clinical notes from an Irish hospital group to generate synthetic notes for "
            "downstream NLP shared tasks. The team claims synthetic outputs eliminate "
            "privacy risk and plans public release of the generator. Recent research shows "
            "membership inference and rare-condition memorisation can still leak training "
            "patients. No empirical privacy attack evaluation is budgeted. Synthetic notes "
            "will be used only for research benchmarks, not clinical care. Hospital legal "
            "counsel has approved release based on the 'synthetic = safe' claim alone."
        ),
        "expected_requirements": ["R005", "R023", "R027", "R042", "R054", "AI011", "HE007", "HE008", "ACM003", "ACM008"],
        "expected_rights": ["Art8_DataProtection", "Art7_PrivateLife", "Art35_HealthCare"],
        "expected_charter_articles": ["Art8_DataProtection", "Art7_PrivateLife", "Art35_HealthCare"],
        "expected_risks": ["PrivacyBreach", "DataBreach"],
        "expected_risk_categories": ["PrivacyBreach", "DataBreach"],
        "info_sufficiency_expected": 3,
        "rationale": "Medium-risk synthetic EHR release with under-tested memorisation; privacy articles engaged.",
    },
    {
        "id": "P36",
        "title": "Online Exam Attention Estimation from Webcam Pose",
        "risk_level": "Medium",
        "source": SYNTHETIC_SOURCE,
        "proposal_text": (
            "This research estimates 'attention' during online university exams from webcam "
            "head-pose and gaze proxies, producing a per-student attention timeline for "
            "instructor review after the exam. Timelines are not auto-fail triggers. "
            "Students must enable the webcam to sit the exam. Disability advocates argue "
            "gaze proxies discriminate against neurodivergent students; the exam board "
            "argues attention analytics are ordinary pedagogy. Whether Art.21 "
            "non-discrimination, Art.7 private life, Art.1 dignity, or primarily "
            "education-policy rather than Charter law applies is contested among "
            "reasonable experts. No demographic validation is reported."
        ),
        "expected_requirements": ["R027", "R042", "R043", "R054", "AI011", "HE003", "ACM004"],
        "expected_rights": ["Art7_PrivateLife", "Art8_DataProtection", "Art21_NonDiscrimination", "Art1_HumanDignity"],
        "expected_charter_articles": ["Art7_PrivateLife", "Art8_DataProtection", "Art21_NonDiscrimination", "Art1_HumanDignity"],
        "expected_risks": ["PrivacyBreach", "Discrimination", "Surveillance"],
        "expected_risk_categories": ["PrivacyBreach", "Discrimination", "Surveillance"],
        "info_sufficiency_expected": 2,
        "rationale": "Contested Medium case: attention analytics vs disability discrimination; article set disputed.",
    },
    {
        "id": "P37",
        "title": "Refugee Resettlement Matching Algorithm",
        "risk_level": "High",
        "source": (
            "Illustrative case informed by Annie™ MOORE / refugee-matching research and "
            "humanitarian critiques of algorithmic resettlement prioritisation."
        ),
        "proposal_text": (
            "This project partners with a European resettlement NGO to rank refugee cases "
            "for limited placement slots using employability predictions, language scores, "
            "family composition, and health flags. Rankings influence which families are "
            "proposed to municipalities. Nationality and religion are excluded, but "
            "language and education features correlate with origin country. Rejected "
            "families receive no detailed explanation. Humanitarian lawyers disagree "
            "whether this primarily engages Art.1 dignity, Art.21 non-discrimination, "
            "Art.18 (asylum-related) analogues via dignity/liberty, or is a legitimate "
            "scarce-resource allocation outside Charter framing. The model has not been "
            "audited for nationality proxy effects. Affected communities were not "
            "consulted in feature design."
        ),
        "expected_requirements": ["R027", "R042", "R054", "R071", "R085", "AI001", "AI016", "HE012", "ACM001"],
        "expected_rights": ["Art1_HumanDignity", "Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy", "Art8_DataProtection"],
        "expected_charter_articles": ["Art1_HumanDignity", "Art21_NonDiscrimination", "Art47_RightToEffectiveRemedy", "Art8_DataProtection"],
        "expected_risks": ["Discrimination", "Accountability", "Dignity"],
        "expected_risk_categories": ["Discrimination", "Accountability"],
        "info_sufficiency_expected": 2,
        "rationale": "High-stakes humanitarian matching; Charter framing is genuinely contested among experts.",
    },
    {
        "id": "P38",
        "title": "Dating-App Safety Classifier for LGBTQ+ Users in Hostile Jurisdictions",
        "risk_level": "Medium",
        "source": SYNTHETIC_SOURCE,
        "proposal_text": (
            "This research builds a classifier that flags potentially entrapment-related "
            "profiles and messages on a dating app used by LGBTQ+ people in jurisdictions "
            "where same-sex intimacy is criminalised. Flagged chats are queued for "
            "voluntary user warnings; the app does not notify police. False positives may "
            "chill legitimate intimate speech (Art.11 / private life); false negatives may "
            "enable harm. Community advisory board members disagree whether the dominant "
            "frame is safety, expression, privacy, or non-discrimination. Training labels "
            "come from moderator decisions in EU markets and may not transfer. The "
            "proposal leaves the primary Charter article intentionally under-determined."
        ),
        "expected_requirements": ["R010", "R027", "R042", "R054", "HE005", "HE019", "ACM020"],
        "expected_rights": ["Art7_PrivateLife", "Art11_FreedomOfExpression", "Art21_NonDiscrimination", "Art1_HumanDignity"],
        "expected_charter_articles": ["Art7_PrivateLife", "Art11_FreedomOfExpression", "Art21_NonDiscrimination", "Art1_HumanDignity"],
        "expected_risks": ["PrivacyBreach", "ExpressionHarm", "Discrimination"],
        "expected_risk_categories": ["PrivacyBreach", "ExpressionHarm", "Discrimination"],
        "info_sufficiency_expected": 2,
        "rationale": "Contested Medium safety-vs-expression case; multiple articles reasonably primary.",
    },
    {
        "id": "P39",
        "title": "Municipal Climate-Migration Risk Scoring",
        "risk_level": "Medium",
        "source": (
            "Illustrative case informed by climate-migration foresight tools and municipal "
            "adaptation planning debates (IPCC SRCCL / urban adaptation literature)."
        ),
        "proposal_text": (
            "This project scores neighbourhoods in a coastal EU city for 'climate-migration "
            "pressure' using flood models, housing tenure, and demographic composition, "
            "to prioritise adaptation spending. Scores are public. Housing advocates warn "
            "publication will accelerate insurance retreat and stigmatise migrant-heavy "
            "districts; planners argue transparency is required for democratic budgeting. "
            "Whether Art.21 non-discrimination, Art.37 environment, Art.1 dignity, or "
            "primarily environmental policy applies is contested. No individual decisions "
            "are automated. The demographic features make disparate neighbourhood effects "
            "likely."
        ),
        "expected_requirements": ["R001", "R027", "R042", "R054", "HE018", "ACM026"],
        "expected_rights": ["Art21_NonDiscrimination", "Art37_EnvironmentalProtection", "Art1_HumanDignity"],
        "expected_charter_articles": ["Art21_NonDiscrimination", "Art37_EnvironmentalProtection", "Art1_HumanDignity"],
        "expected_risks": ["Discrimination", "EconomicHarm"],
        "expected_risk_categories": ["Discrimination", "EconomicHarm"],
        "info_sufficiency_expected": 2,
        "rationale": "Contested Medium planning tool; environment vs discrimination framing disputed.",
    },
    {
        "id": "P40",
        "title": "Workplace Emotion Analytics under 'Wellbeing' Framing",
        "risk_level": "Medium",
        "source": SYNTHETIC_SOURCE,
        "proposal_text": (
            "This research pilots camera-based emotion analytics in a Lagos business-process "
            "outsourcing centre, framed as employee wellbeing support. Aggregated mood "
            "dashboards go to team leads; individuals scoring repeatedly 'distressed' are "
            "offered counselling referrals. Participation is described as voluntary but "
            "tied to a wellness bonus. Labour advocates call it surveillance that chills "
            "union organising; HR calls it duty-of-care. Consent voluntariness under wage "
            "pressure is disputed. The system was validated on Western face sets only. "
            "Expected Charter mapping (private life, data protection, fair working "
            "conditions, dignity) is reasonably contested in weight even when articles "
            "are listed."
        ),
        "expected_requirements": ["R001", "R005", "R010", "R027", "R042", "R054", "AI011", "HE007", "HE020", "ACM003", "ACM011"],
        "expected_rights": ["Art7_PrivateLife", "Art8_DataProtection", "Art31_FairWorkingConditions", "Art1_HumanDignity"],
        "expected_charter_articles": ["Art7_PrivateLife", "Art8_DataProtection", "Art31_FairWorkingConditions", "Art1_HumanDignity"],
        "expected_risks": ["Surveillance", "PrivacyBreach", "EmploymentHarm"],
        "expected_risk_categories": ["Surveillance", "PrivacyBreach", "EmploymentHarm"],
        "info_sufficiency_expected": 3,
        "rationale": "Medium-risk workplace affect analytics in Nigeria; consent/surveillance framing contested.",
    },
]


def _vocab_from_original():
    arts, cats = set(), set()
    for p in ORIGINAL:
        arts.update(p["expected_charter_articles"])
        cats.update(p["expected_risk_categories"])
    return arts, cats


def _normalise_original(p: dict) -> dict:
    out = deepcopy(p)
    if "source" not in out or not out["source"]:
        out["source"] = SYNTHETIC_SOURCE
    # Keep expected_rights in sync with charter articles when present.
    if not out.get("expected_rights"):
        out["expected_rights"] = list(out["expected_charter_articles"])
    if not out.get("expected_risks"):
        out["expected_risks"] = list(out.get("expected_risk_categories") or [])
    sid = out["id"]
    info, rationale = ORIGINAL_BACKFILL[sid]
    out["info_sufficiency_expected"] = info
    out["rationale"] = rationale
    # Ensure all keys present.
    for k in ALL_KEYS:
        if k not in out:
            raise AssertionError(f"Original {sid} missing key {k} after backfill")
    return out


def build_corpus() -> list[dict]:
    originals = [_normalise_original(p) for p in ORIGINAL]
    assert len(originals) == 20, len(originals)
    assert len(NEW_PROPOSALS) == 20, len(NEW_PROPOSALS)
    # Preserve original 20 verbatim (plus backfill only of new fields + missing source).
    corpus = originals + deepcopy(NEW_PROPOSALS)
    return corpus


def validate(corpus: list[dict]) -> None:
    arts_vocab, cats_vocab = _vocab_from_original()

    if len(corpus) != 40:
        raise AssertionError(f"len(PROPOSALS) == {len(corpus)}, expected 40")

    ids = [p["id"] for p in corpus]
    if len(set(ids)) != 40:
        raise AssertionError(f"Duplicate ids: {ids}")

    for p in corpus:
        for k in ALL_KEYS:
            if k not in p:
                raise AssertionError(f"{p.get('id')}: missing key {k}")
            if p[k] is None:
                raise AssertionError(f"{p.get('id')}: key {k} is None")
        if not p["expected_charter_articles"]:
            raise AssertionError(f"{p['id']}: empty expected_charter_articles")
        if not p["proposal_text"].strip():
            raise AssertionError(f"{p['id']}: empty proposal_text")
        if p["risk_level"] not in {"High", "Medium", "Low"}:
            raise AssertionError(f"{p['id']}: invalid risk_level {p['risk_level']}")
        if not (1 <= int(p["info_sufficiency_expected"]) <= 5):
            raise AssertionError(f"{p['id']}: info_sufficiency_expected out of range")
        if not str(p["rationale"]).strip():
            raise AssertionError(f"{p['id']}: empty rationale")

        for a in p["expected_charter_articles"]:
            if a not in arts_vocab:
                raise AssertionError(
                    f"{p['id']}: charter article {a!r} not in original vocabulary "
                    f"{sorted(arts_vocab)}"
                )
        for c in p["expected_risk_categories"]:
            if c not in cats_vocab:
                raise AssertionError(
                    f"{p['id']}: risk category {c!r} not in original vocabulary "
                    f"{sorted(cats_vocab)}"
                )

    dist = Counter(p["risk_level"] for p in corpus)
    high_frac = dist["High"] / len(corpus)
    if high_frac > 0.70:
        raise AssertionError(
            f"High-risk fraction {high_frac:.1%} exceeds 70% cap; dist={dict(dist)}"
        )

    print("Acceptance checks passed.")
    print(f"  n={len(corpus)}")
    print(f"  risk_level distribution: {dict(dist)} (High={high_frac:.1%})")
    print(f"  charter vocab size: {len(arts_vocab)}; category vocab size: {len(cats_vocab)}")


def write_extended_module(corpus: list[dict], path: Path) -> None:
    header = '''"""
synthetic_proposals_extended.py
40 research proposals for the diagnostic methodology study.

First 20 entries are the original evaluation corpus preserved verbatim
(with info_sufficiency_expected / rationale backfilled, and source filled
where it was missing). Entries P21–P40 are new proposals targeting Medium/Low
coverage, contested Charter cases, non-Western contexts, and framework tension.

Generated by diagnostic/corpus_expansion.py — re-run that script to regenerate.
Do not introduce a branded acronym for the diagnostic methodology in this file.
"""

PROPOSALS = [
'''
    body_parts = []
    for p in corpus:
        body_parts.append("    " + pprint.pformat(p, width=100, sort_dicts=False).replace("\n", "\n    "))
    text = header + ",\n\n".join(body_parts) + ",\n]\n"
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path} ({len(corpus)} proposals)")


def optional_llm_draft(n: int = 1) -> None:
    """Optional helper: draft proposal prose via local Ollama (not used for GT)."""
    sys.path.insert(0, str(RAG))
    from llm_caller import call_llm

    prompt = (
        "Write one research-proposal paragraph (~180 words) in the style of AI ethics "
        "evaluation vignettes, grounded in a realistic non-US deployment context, "
        "Medium risk, with one subtle contested fundamental-rights issue. "
        "Return plain prose only."
    )
    for i in range(n):
        print(f"--- draft {i+1} ---")
        print(call_llm(prompt, backend="ollama", temperature=0.7, max_tokens=500))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Optionally print an LLM prose draft (GT still authored in this file).",
    )
    args = parser.parse_args()
    if args.draft:
        optional_llm_draft(1)

    corpus = build_corpus()
    validate(corpus)
    out = ROOT / "synthetic_proposals_extended.py"
    write_extended_module(corpus, out)

    # Re-import written module and re-assert.
    spec = importlib.util.spec_from_file_location("synthetic_proposals_extended", out)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    validate(mod.PROPOSALS)
    print("Re-import validation OK.")


if __name__ == "__main__":
    main()
