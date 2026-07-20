"""
prompt_builder.py
Builds structured prompts for the ethics assessment LLM.
Combines: research proposal + retrieved KG context → assessment prompt.

Phase 2: risk-category taxonomy constraint + transparency/well-being surfacing rule.
"""

RISK_CALIBRATION = """
RISK LEVEL DEFINITIONS — apply these strictly:
- HIGH: Involves biometric data, criminal justice, medical diagnosis, predictive policing,
  autonomous systems making consequential decisions, or processing of special category data
  about vulnerable groups without explicit consent.
- MEDIUM: Involves personal data processing with consent, AI-assisted (not autonomous)
  decision support, recommendation systems, or NLP on non-sensitive text with privacy measures.
- LOW: Involves only publicly available data, no personal data, no consequential decisions,
  no deployment affecting individuals, or purely analytical/research tools with no operational use.
"""


DEFAULT_MAX_REQUIREMENTS = 25


def requirement_text_char_limit(max_requirements: int) -> int | None:
    """Truncate requirement text when showing more than the default cap."""
    if max_requirements <= DEFAULT_MAX_REQUIREMENTS:
        return None
    return max(40, min(120, 3500 // max_requirements))


def build_context(
    requirements: list,
    incidents: list,
    rights: list,
    max_requirements: int = DEFAULT_MAX_REQUIREMENTS,
    total_requirements: int = None,
    max_requirement_text_chars: int = None,
    risk_categories: list = None,
) -> str:
    """Format retrieved KG data as human-readable context for the LLM."""
    total_requirements = total_requirements if total_requirements is not None else len(requirements)
    prioritized = sorted(
        requirements,
        key=lambda r: (r.get("mandatory") != "true", r.get("id", "")),
    )
    shown_requirements = prioritized[:max_requirements]

    req_lines = []
    for r in shown_requirements:
        tier_label = "Mandatory" if r["mandatory"] == "true" else "Reflective"
        fw = r["framework"]
        text = r["text"]
        if max_requirement_text_chars and len(text) > max_requirement_text_chars:
            text = text[:max_requirement_text_chars].rstrip() + "..."
        section = r.get("section_reference") or ""
        section_bit = f" [section: {section}]" if section else ""
        risk_bit = ""
        if r.get("risk_categories"):
            risk_bit = f" [risks: {', '.join(r['risk_categories'])}]"
        req_lines.append(f"  [{fw}] {r['id']}: {text} ({tier_label}){section_bit}{risk_bit}")

    inc_lines = []
    for i in incidents:
        risk_bit = ""
        if i.get("risk_categories"):
            risk_bit = f" [risks: {', '.join(i['risk_categories'])}]"
        inc_lines.append(f"  {i['id']}: {i['title']}{risk_bit}")

    rights_clean = []
    for r in rights:
        name = r.replace("Art", "Article ").replace("_", " ")
        rights_clean.append(f"  {name}")

    risk_cat_lines = []
    for c in risk_categories or []:
        label = c.get("label") or c.get("id", "")
        definition = c.get("definition") or ""
        if definition:
            risk_cat_lines.append(f"  - {c['id']} ({label}): {definition}")
        else:
            risk_cat_lines.append(f"  - {c['id']}")

    context = f"""
RETRIEVED ETHICS REQUIREMENTS FROM KNOWLEDGE GRAPH ({total_requirements} total, showing top {len(shown_requirements)}):
{chr(10).join(req_lines) if req_lines else '  No requirements retrieved.'}

EU CHARTER OF FUNDAMENTAL RIGHTS AT RISK ({len(rights)} articles):
{chr(10).join(rights_clean)}

HISTORICAL AI INCIDENT PRECEDENTS ({len(incidents)} incidents):
{chr(10).join(inc_lines) if inc_lines else '  No incidents retrieved.'}

RISK CATEGORIES IN SCOPE FOR THIS PROPOSAL ({len(risk_categories or [])} categories from retrieved evidence):
{chr(10).join(risk_cat_lines) if risk_cat_lines else '  No risk categories retrieved — use only formal AIEF RiskCategory labels if needed.'}
"""
    return context


_RISK_CATEGORY_INSTRUCTIONS = """
RISK CATEGORY CONSTRAINTS:
- Every identified risk MUST include a "risk_category" field.
- "risk_category" MUST be drawn from the "RISK CATEGORIES IN SCOPE FOR THIS PROPOSAL" list above.
  Do not invent free-text category labels. Use the exact category id (e.g. ChildrenRights, Surveillance, PrivacyBreach).
- If a requirement tagged section "Transparency" or "Well-being" (environmental) was retrieved above and is
  relevant to this proposal, you MUST surface it as its own identified risk — do not omit it even if
  lower severity than the primary risks. Transparency should be treated as a near-default concern for
  any AI system that interacts with end-users; environmental/well-being disclosure should be surfaced
  when compute, training scale, or environmental-impact requirements are in scope.
"""


def build_assessment_prompt(proposal: str, context: str) -> str:
    """Build the full assessment prompt for the LLM."""

    prompt = f"""You are an AI ethics assessment assistant for early-stage research projects at Trinity College Dublin. You assess research proposals against four governance frameworks: TCD REAMS, EU AI Act, Horizon Europe, and ACM/NeurIPS ethics guidelines.

INSTRUCTIONS:
- Analyse the research proposal carefully and thoroughly.
- Use the retrieved knowledge graph context to ground your assessment.
- Cite BETWEEN 5 AND 10 specific requirement IDs from the retrieved context above.
  For HIGH risk: cite at least 8. For MEDIUM: at least 5. For LOW: at least 2.
- List ALL Charter rights relevant to this proposal.
  For HIGH risk: expect 4-6 rights. For MEDIUM: 2-4. For LOW: 0-2.
- List ALL relevant incidents from the provided precedents.
  Do not limit to 1 or 2.
- Identify ALL relevant risks — do not limit yourself to 2.
- Be specific and actionable.
- Return your assessment as valid JSON only. No markdown. No explanation outside the JSON.
- The JSON arrays must contain MULTIPLE items — never just 1 or 2 for a substantive proposal.
{_RISK_CATEGORY_INSTRUCTIONS}
{RISK_CALIBRATION}
RESEARCH PROPOSAL:
{proposal}

KNOWLEDGE GRAPH CONTEXT:
{context}

Return ONLY valid JSON:
{{
  "risk_summary": "3-4 sentence summary of ALL primary ethical risks",
  "overall_risk_level": "High or Medium or Low",
  "identified_risks": [
    {{"risk": "...", "risk_category": "e.g. ChildrenRights", "severity": "High or Medium or Low", "explanation": "..."}}
  ],
  "applicable_requirements": [
    {{"requirement_id": "e.g. R085", "requirement_text": "...", "framework": "REAMS or EUAIAct or HorizonEurope or ACMConference", "tier": "Tier 1 Mandatory or Tier 2 Reflective", "action_needed": "..."}}
  ],
  "charter_rights_at_risk": [
    {{"article": "e.g. Article 21", "right_name": "e.g. Non-Discrimination", "relevance": "..."}}
  ],
  "historical_precedents": [
    {{"incident_id": "e.g. AIAAIC-001", "incident_title": "...", "lesson": "..."}}
  ],
  "recommended_mitigations": [
    {{"mitigation": "...", "priority": "High or Medium or Low"}}
  ],
  "tier1_mandatory_actions": ["..."],
  "tier2_reflective_prompts": ["..."],
  "reams_clearance_likely": true
}}"""

    return prompt


def build_llm_only_prompt(proposal: str) -> str:
    """Build an assessment prompt without knowledge graph context (baseline mode)."""

    prompt = f"""You are an AI ethics assessment assistant for early-stage research projects at Trinity College Dublin. You assess research proposals against four governance frameworks: TCD REAMS, EU AI Act, Horizon Europe, and ACM/NeurIPS ethics guidelines.

INSTRUCTIONS:
- Analyse the research proposal carefully and thoroughly.
- No knowledge graph context is provided — assess using your general AI ethics knowledge.
- Identify ALL relevant risks — do not limit yourself to 2.
- Identify ALL relevant Charter rights — do not limit yourself to 2.
- Be specific and actionable.
- Return your assessment as valid JSON only. No markdown. No explanation outside the JSON.
- The JSON arrays must contain MULTIPLE items — never just 1 or 2 for a substantive proposal.
- Every identified risk MUST include a "risk_category" drawn from the AIEF RiskCategory taxonomy
  (e.g. PhysicalHarm, PsychologicalHarm, FinancialHarm, ReputationalHarm, PrivacyBreach,
  Discrimination, EnvironmentalHarm, DualUseMisuse, FunctionCreep, WorkplaceSafetyRisk,
  DemocraticProcessHarm, AddictionRisk, Surveillance, Manipulation, ChildrenRights, Dignity,
  GenderHarm, EconomicHarm, EmploymentHarm, Accountability, LibertyViolation, ExpressionHarm).
  Do not invent free-text category labels.

{RISK_CALIBRATION}
RESEARCH PROPOSAL:
{proposal}

Return ONLY valid JSON:
{{
  "risk_summary": "3-4 sentence summary of ALL primary ethical risks",
  "overall_risk_level": "High or Medium or Low",
  "identified_risks": [
    {{"risk": "...", "risk_category": "e.g. ChildrenRights", "severity": "High or Medium or Low", "explanation": "..."}}
  ],
  "applicable_requirements": [
    {{"requirement_id": "e.g. R085", "requirement_text": "...", "framework": "REAMS or EUAIAct or HorizonEurope or ACMConference", "tier": "Tier 1 Mandatory or Tier 2 Reflective", "action_needed": "..."}}
  ],
  "charter_rights_at_risk": [
    {{"article": "e.g. Article 21", "right_name": "e.g. Non-Discrimination", "relevance": "..."}}
  ],
  "historical_precedents": [
    {{"incident_id": "e.g. AIAAIC-001", "incident_title": "...", "lesson": "..."}}
  ],
  "recommended_mitigations": [
    {{"mitigation": "...", "priority": "High or Medium or Low"}}
  ],
  "tier1_mandatory_actions": ["..."],
  "tier2_reflective_prompts": ["..."],
  "reams_clearance_likely": true
}}"""

    return prompt


if __name__ == "__main__":
    import argparse

    from sparql_retrieval import retrieve_all_for_proposal
    from synthetic_proposals import PROPOSALS

    parser = argparse.ArgumentParser(description="Build and preview assessment prompts")
    parser.add_argument("proposal_id", help="Proposal ID (e.g. P01)")
    parser.add_argument(
        "--max-requirements",
        type=int,
        default=DEFAULT_MAX_REQUIREMENTS,
        help=f"Cap requirements in context (default: {DEFAULT_MAX_REQUIREMENTS})",
    )
    args = parser.parse_args()

    proposal = next(p for p in PROPOSALS if p["id"] == args.proposal_id)
    reqs, incidents, rights, _, risk_cats = retrieve_all_for_proposal(proposal["proposal_text"])
    text_limit = requirement_text_char_limit(args.max_requirements)
    context = build_context(
        reqs,
        incidents,
        rights,
        max_requirements=args.max_requirements,
        total_requirements=len(reqs),
        max_requirement_text_chars=text_limit,
        risk_categories=risk_cats,
    )
    prompt = build_assessment_prompt(proposal["proposal_text"], context)
    print(f"Proposal: {args.proposal_id}")
    print(f"Retrieved requirements: {len(reqs)}")
    print(f"Shown in context: {min(args.max_requirements, len(reqs))}")
    print(f"Risk categories: {[c['id'] for c in risk_cats]}")
    print(f"Requirement text limit: {text_limit or 'none'}")
    print(f"Prompt length: {len(prompt)} characters (~{len(prompt) // 2} tokens est.)")
    print("\n--- CONTEXT PREVIEW (first 2500 chars) ---")
    print(context[:2500])
