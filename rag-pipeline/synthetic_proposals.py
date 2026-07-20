"""
synthetic_proposals.py
20 synthetic research proposals for framework evaluation.
Each proposal includes ground truth annotations for validation.

Author: Navina Ganapathy Amuthan
Trinity College Dublin — MSc Dissertation 2026

Phase 6 annotations:
  expected_risks / expected_risk_categories — AIEF RiskCategory ground truth
  expected_rights / expected_charter_articles — Charter article ground truth
"""

PROPOSALS = [

    # ══════════════════════════════════════════════════════════════════════════
    # HIGH RISK (P01–P06)
    # ══════════════════════════════════════════════════════════════════════════

    {
        "id": 'P01',
        "title": 'Optum Health Risk Stratification Algorithm',
        "risk_level": 'High',
        "source": 'Obermeyer, Z., Powers, B., Vogeli, C., & Mullainathan, S. (2019). Dissecting racial bias in an algorithm used to manage the health of populations. Science, 366(6464), 447–453. DOI: 10.1126/science.aax2342',
        "proposal_text": """This research proposes to develop a commercial health risk stratification algorithm to identify high-need patients for enrolment in care management programmes across a network of US hospital systems. The algorithm will use insurance claims data as a proxy for health need, predicting which patients require additional clinical resources based on historical healthcare costs, prior diagnoses, medication use, and utilisation patterns from electronic health records covering approximately 200 million patients annually. Patients scoring in the top 3 percentile will automatically be referred to care management; those in the top 45 percentile will be assessed for referral. The algorithm will not explicitly use race as a predictive variable. However, because Black patients have historically incurred lower healthcare costs than white patients with equivalent chronic disease burden — due to structural barriers to healthcare access including cost, discrimination, and geographic distance — the cost proxy will systematically underestimate the health needs of Black patients. The algorithm has not undergone independent bias auditing prior to deployment. No mechanism for algorithmic review or patient appeal of care management non-referral decisions is planned.""",
        "expected_requirements": ['R042', 'R054', 'R071', 'R085', 'AI001', 'AI016', 'AI021', 'AI024', 'HE012', 'HE015', 'ACM001', 'ACM002'],
        "expected_rights": ['Art21_NonDiscrimination', 'Art35_HealthCare', 'Art8_DataProtection', 'Art2_RightToLife'],
        "expected_charter_articles": ['Art21_NonDiscrimination', 'Art35_HealthCare', 'Art8_DataProtection', 'Art2_RightToLife'],
        "expected_risks": ['Discrimination', 'PhysicalHarm'],
        "expected_risk_categories": ['Discrimination', 'PhysicalHarm'],
    },

    {
        "id": 'P02',
        "title": 'COMPAS Recidivism Risk Assessment Tool',
        "risk_level": 'High',
        "source": 'Angwin, J., Larson, J., Mattu, S., & Kirchner, L. (2016). Machine Bias. ProPublica. https://www.propublica.org/article/machine-bias-risk-assessments-in-criminal-sentencing',
        "proposal_text": """This research proposes to deploy the COMPAS (Correctional Offender Management Profiling for Alternative Sanctions) risk assessment tool across criminal courts in Broward County, Florida, to predict defendants' likelihood of recidivism. The system uses a proprietary algorithm trained on a battery of psychological questionnaire responses administered at the time of arrest, combined with criminal history variables including prior arrest count, age at first offence, and charge severity. The algorithm produces three decile scores (1–10) for general recidivism, violent recidivism, and failure to appear, with scores categorised as Low (1–4), Medium (5–7), or High (8–10). These scores will be provided to judges and parole officers at pre-trial hearings and sentencing to inform detention and release decisions. The model is proprietary and its internal weighting is not disclosed to defendants or defence counsel. No mechanism for defendants to challenge the algorithmic risk score is included in the deployment design. An independent analysis of the algorithm's outputs found that Black defendants who did not re-offend were falsely classified as high risk at nearly twice the rate of white defendants who did not re-offend (45% vs 24%).""",
        "expected_requirements": ['R010', 'R027', 'R042', 'R054', 'R071', 'R085', 'AI001', 'AI016', 'AI021', 'AI022', 'HE005', 'ACM001', 'ACM024'],
        "expected_rights": ['Art21_NonDiscrimination', 'Art6_RightToLiberty', 'Art47_RightToEffectiveRemedy', 'Art48_PresumptionOfInnocence'],
        "expected_charter_articles": ['Art21_NonDiscrimination', 'Art6_RightToLiberty', 'Art47_RightToEffectiveRemedy', 'Art48_PresumptionOfInnocence'],
        "expected_risks": ['Discrimination', 'LibertyViolation'],
        "expected_risk_categories": ['Discrimination', 'LibertyViolation'],
    },

    {
        "id": 'P03',
        "title": 'Amazon Rekognition Law Enforcement Facial Recognition',
        "risk_level": 'High',
        "source": "Snow, J. (2018). Amazon Is Selling Facial Recognition to Law Enforcement — and It's Cause for Concern. ACLU. https://www.aclu.org/news/privacy-technology/amazon-teams-government-deploy-dangerous-new; Raji, I.D. & Buolamwini, J. (2019). Actionable Auditing. AAAI/ACM AIES 2019.",
        "proposal_text": """This research proposes to deploy Amazon Rekognition, a cloud-based facial recognition system, for use by law enforcement agencies across the United States to identify individuals in real-time surveillance footage, body camera recordings, and crime scene images. The system can identify and track up to 100 faces in a single image and match them against databases of tens of millions of faces drawn from arrest records and public sources. The system will be marketed to local police departments as a tool for identifying persons of interest in criminal investigations. The default confidence threshold of 80% will be used for initial deployment, with Amazon recommending a 99% threshold for law enforcement use — a discrepancy between default settings and recommended settings that has not been addressed in the deployment contract. An ACLU audit found that at 80% confidence, Rekognition falsely matched 28 members of the US Congress to criminal mugshots, with disproportionate false positives for people of colour including six members of the Congressional Black Caucus. No independent demographic bias audit has been conducted prior to law enforcement deployment. No independent oversight mechanism or accountability framework for false match consequences has been established.""",
        "expected_requirements": ['R010', 'R027', 'R042', 'R054', 'R071', 'R085', 'AI001', 'AI011', 'AI016', 'AI021', 'HE007', 'ACM001', 'ACM002'],
        "expected_rights": ['Art7_PrivateLife', 'Art8_DataProtection', 'Art21_NonDiscrimination', 'Art6_RightToLiberty', 'Art47_RightToEffectiveRemedy', 'Art48_PresumptionOfInnocence'],
        "expected_charter_articles": ['Art7_PrivateLife', 'Art8_DataProtection', 'Art21_NonDiscrimination', 'Art6_RightToLiberty', 'Art47_RightToEffectiveRemedy', 'Art48_PresumptionOfInnocence'],
        "expected_risks": ['Discrimination', 'Surveillance', 'FalseIdentification'],
        "expected_risk_categories": ['Discrimination', 'Surveillance', 'FalseIdentification'],
    },

    {
        "id": 'P04',
        "title": 'Facebook Ad Delivery Discriminatory Optimisation',
        "risk_level": 'High',
        "source": "Ali, M., Sapiezynski, P., Bogen, M., Korolova, A., Mislove, A., & Rieke, A. (2019). Discrimination through Optimization: How Facebook's Ad Delivery Can Lead to Skewed Outcomes. ACM CSCW 2019. DOI: 10.1145/3359301",
        "proposal_text": """This research proposes to develop a machine learning-based ad delivery optimisation system for deployment on a major social media platform. The system will use a multi-objective optimisation algorithm that maximises ad relevance scores and advertiser return on investment by predicting which users are most likely to engage with each advertisement. The algorithm will use thousands of user behavioural, demographic, and interest signals — excluding explicit race and gender variables — to determine ad delivery. The system will operate as a real-time auction where advertisers bid for impression opportunities, with the platform's relevance prediction model determining which users see which ads. An academic audit of this system found that even when advertisers set their targeting parameters to be fully inclusive with no demographic restrictions, the optimisation algorithm delivered employment ads predominantly to men and housing ads predominantly to white users. This skew was caused by the algorithm's financial optimisation function, which learned that majority-group users were cheaper to reach and more likely to engage. The system does not include pre-deployment fairness auditing. No mechanism for individual users to understand why they are or are not shown specific opportunity-related advertisements is planned.""",
        "expected_requirements": ['R010', 'R027', 'R042', 'R071', 'R085', 'AI001', 'AI016', 'AI021', 'HE012', 'HE013', 'HE015', 'ACM001', 'ACM002', 'ACM012'],
        "expected_rights": ['Art21_NonDiscrimination', 'Art23_GenderEquality', 'Art15_FreedomOfOccupation', 'Art8_DataProtection'],
        "expected_charter_articles": ['Art21_NonDiscrimination', 'Art23_GenderEquality', 'Art15_FreedomOfOccupation', 'Art8_DataProtection'],
        "expected_risks": ['Discrimination', 'EmploymentHarm', 'EconomicHarm'],
        "expected_risk_categories": ['Discrimination', 'EmploymentHarm', 'EconomicHarm'],
    },

    {
        "id": 'P05',
        "title": 'NHS Sepsis Prediction Algorithm with Racial Bias',
        "risk_level": 'High',
        "source": 'Bhatt, D.L. et al. (2021). Cited in: Guardian (2021). NHS AI tool may discriminate against patients with black and minority ethnic backgrounds. https://www.theguardian.com/society/2021/jun/11/nhs-ai-tool-may-discriminate-against-patients-with-black-and-minority-ethnic-backgrounds; Chua et al. (2025). The role of AI in sepsis in the Emergency Department. Annals of Translational Medicine.',
        "proposal_text": """This research proposes to deploy a machine learning sepsis prediction algorithm across NHS England hospital trusts to identify patients at risk of sepsis deterioration in emergency department and ward settings. The algorithm uses physiological parameters including respiratory rate, oxygen saturation, temperature, systolic blood pressure, pulse rate, and level of consciousness — as recorded in the National Early Warning Score 2 (NEWS2) framework — alongside laboratory values and electronic health record data, to generate real-time risk scores for clinical staff. The training dataset was drawn predominantly from NHS patient records which have documented under-representation of Black, Asian, and minority ethnic patient populations in specialist care pathways. Academic analysis has found that vital signs used as predictive features are racially skewed, as minority patients may exhibit different baseline physiological profiles than the majority-white training population. The algorithm has not undergone prospective demographic bias auditing across ethnic subgroups prior to nationwide deployment. Clinical staff will receive risk scores without visibility into the algorithm's feature weighting or demographic performance variance. No formal mechanism for clinicians to record or escalate concerns about demographic performance disparities is included in the deployment framework.""",
        "expected_requirements": ['R042', 'R054', 'R071', 'R085', 'AI001', 'AI008', 'AI016', 'AI024', 'HE012', 'HE015', 'ACM001', 'ACM014'],
        "expected_rights": ['Art21_NonDiscrimination', 'Art35_HealthCare', 'Art2_RightToLife', 'Art8_DataProtection'],
        "expected_charter_articles": ['Art21_NonDiscrimination', 'Art35_HealthCare', 'Art2_RightToLife', 'Art8_DataProtection'],
        "expected_risks": ['Discrimination', 'PhysicalHarm'],
        "expected_risk_categories": ['Discrimination', 'PhysicalHarm'],
    },

    {
        "id": 'P06',
        "title": 'Emotion Recognition in Secondary School Classrooms',
        "risk_level": 'High',
        "proposal_text": """This project proposes to install camera-based emotion recognition systems in six secondary school classrooms in Dublin to study the relationship between student emotional engagement and learning outcomes. The system will use computer vision to classify student facial expressions into six emotional categories (happy, sad, angry, surprised, fearful, neutral) at 5-second intervals throughout lessons. Data will be collected over one academic term covering approximately 180 students aged 13-17. Parental consent will be obtained but students will not be given an individual opt-out mechanism that allows them to remain in the classroom without being monitored. The emotion recognition system has been validated primarily on adult Western faces and has not been tested for accuracy on adolescent faces or faces from diverse ethnic backgrounds. Aggregated emotional engagement scores will be shared with teachers to inform pedagogical adjustments.""",
        "expected_requirements": ['R027', 'R042', 'R043', 'R044', 'R054', 'R071', 'R085', 'AI001', 'AI011', 'AI016', 'HE003', 'ACM004', 'ACM005'],
        "expected_rights": ['Art24_RightsOfChild', 'Art7_PrivateLife', 'Art8_DataProtection', 'Art1_HumanDignity', 'Art3_RightToIntegrity'],
        "expected_charter_articles": ['Art24_RightsOfChild', 'Art7_PrivateLife', 'Art8_DataProtection', 'Art1_HumanDignity', 'Art3_RightToIntegrity'],
        "expected_risks": ['ChildrenRights', 'PrivacyBreach', 'Discrimination'],
        "expected_risk_categories": ['ChildrenRights', 'PrivacyBreach', 'Discrimination'],
    },


    # ══════════════════════════════════════════════════════════════════════════
    # MEDIUM RISK (P07–P12)
    # ══════════════════════════════════════════════════════════════════════════

    {
        "id": 'P07',
        "title": 'NLP Sentiment Analysis on Student Essay Submissions',
        "risk_level": 'Medium',
        "proposal_text": """This research proposes to apply sentiment analysis and linguistic style detection to a corpus of 5,000 anonymised undergraduate essays submitted to the School of English at Trinity College Dublin. The aim is to investigate whether emotional tone and writing style correlate with academic grade outcomes. Essays will be collected from the past three academic years with student consent obtained retrospectively via email. The NLP pipeline will extract features including sentiment polarity, subjectivity scores, vocabulary complexity, and sentence structure patterns. The researchers will investigate whether detectable stylistic differences correlate with students' first language, gender, or socioeconomic background as indicated by fee status. All analysis will be performed on pseudonymised data with student IDs replaced by random codes. Results will be published in aggregate form only.""",
        "expected_requirements": ['R005', 'R023', 'R027', 'R042', 'R054', 'R085', 'HE007', 'HE012', 'ACM003', 'ACM012'],
        "expected_rights": ['Art8_DataProtection', 'Art21_NonDiscrimination', 'Art7_PrivateLife'],
        "expected_charter_articles": ['Art8_DataProtection', 'Art21_NonDiscrimination', 'Art7_PrivateLife'],
        "expected_risks": ['Discrimination', 'PrivacyBreach'],
        "expected_risk_categories": ['Discrimination', 'PrivacyBreach'],
    },

    {
        "id": 'P08',
        "title": 'AI Chatbot for Mental Health Support Triage',
        "risk_level": 'Medium',
        "proposal_text": """This project proposes to develop a conversational AI chatbot to provide initial mental health support triage for university students. The chatbot will conduct a structured conversational assessment to evaluate symptoms of anxiety and depression using validated clinical screening instruments (PHQ-9, GAD-7) adapted into conversational format. Based on the assessment, the chatbot will recommend one of three pathways: self-help resources, a scheduled counselling appointment, or immediate crisis intervention referral. The chatbot will store conversation logs for quality improvement purposes. Student data will be pseudonymised but linked to student records to enable follow-up. The chatbot will include a disclaimer that it is not a substitute for professional mental health care. The system has not been validated against clinical assessments performed by qualified professionals. Conversations will be processed by an external cloud-based NLP service.""",
        "expected_requirements": ['R021', 'R027', 'R042', 'R054', 'R071', 'AI001', 'AI008', 'AI024', 'HE003', 'HE017', 'ACM001'],
        "expected_rights": ['Art35_HealthCare', 'Art2_RightToLife', 'Art8_DataProtection', 'Art1_HumanDignity'],
        "expected_charter_articles": ['Art35_HealthCare', 'Art2_RightToLife', 'Art8_DataProtection', 'Art1_HumanDignity'],
        "expected_risks": ['PhysicalHarm', 'PrivacyBreach'],
        "expected_risk_categories": ['PhysicalHarm', 'PrivacyBreach'],
    },

    {
        "id": 'P09',
        "title": 'Intelligent Academic Advising Recommendation System',
        "risk_level": 'Medium',
        "proposal_text": """This research proposes to build a recommendation system for academic module selection at Trinity College Dublin. The system will analyse historical student records including module choices, grades achieved, attendance patterns, and degree outcomes to recommend optimal module combinations for current students. The dataset covers 20,000 student records from the past ten years. Students will receive personalised module recommendations through the student portal alongside existing manual advising. The system will use collaborative filtering to identify students with similar academic profiles and recommend modules that led to positive outcomes for comparable students. The researchers acknowledge that historical patterns may reflect systemic inequalities in module access and outcomes. The model will not account for disability accommodations or students who changed programmes. Student consent for the use of historical academic records in the training dataset has not been explicitly obtained.""",
        "expected_requirements": ['R005', 'R023', 'R027', 'R042', 'R054', 'R085', 'AI012', 'HE007', 'HE011', 'ACM003'],
        "expected_rights": ['Art8_DataProtection', 'Art21_NonDiscrimination', 'Art41_GoodAdministration'],
        "expected_charter_articles": ['Art8_DataProtection', 'Art21_NonDiscrimination', 'Art41_GoodAdministration'],
        "expected_risks": ['Discrimination', 'PrivacyBreach'],
        "expected_risk_categories": ['Discrimination', 'PrivacyBreach'],
    },

    {
        "id": 'P10',
        "title": 'Social Media Misinformation Detection Tool',
        "risk_level": 'Medium',
        "proposal_text": """This project aims to develop an NLP-based tool for detecting health-related misinformation on Irish social media platforms. The system will collect public posts from Twitter/X, Reddit, and Facebook groups discussing topics including vaccination, cancer treatments, and mental health remedies. The tool will classify posts as verified, unverified, or misleading using a combination of source credibility scoring and claim verification against WHO and HSE published guidelines. The dataset will include approximately 500,000 public posts collected via platform APIs. While posts are publicly available, the tool will process usernames and account metadata to assess source credibility patterns. The researchers plan to publish a list of accounts identified as frequent misinformation sources. The tool does not account for satire, cultural context, or legitimate medical debate where scientific consensus has not been established.""",
        "expected_requirements": ['R001', 'R010', 'R019', 'R027', 'R054', 'AI001', 'HE019', 'HE021', 'ACM020', 'ACM025'],
        "expected_rights": ['Art11_FreedomOfExpression', 'Art7_PrivateLife', 'Art8_DataProtection'],
        "expected_charter_articles": ['Art11_FreedomOfExpression', 'Art7_PrivateLife', 'Art8_DataProtection'],
        "expected_risks": ['PrivacyBreach', 'ExpressionHarm'],
        "expected_risk_categories": ['PrivacyBreach', 'ExpressionHarm'],
    },

    {
        "id": 'P11',
        "title": 'Automated Essay Grading System',
        "risk_level": 'Medium',
        "proposal_text": """This research proposes to develop an automated essay grading system for first-year undergraduate modules at Trinity College Dublin. The system will use large language model embeddings to score essays on a 0-100 scale by comparing them against a rubric-encoded scoring model trained on 3,000 previously graded essays. The system will provide both a numerical grade and written feedback comments generated by the LLM. The tool is intended to reduce marking workload by providing initial scores that lecturers can review and adjust. The training data consists of essays graded by twelve different tutors whose grading standards varied considerably. Students whose first language is not English may receive systematically different scores due to the model's sensitivity to grammatical patterns associated with non-native speakers. Students will not be informed that AI-assisted grading is being used. No appeals process specifically addressing algorithmic grading errors has been designed.""",
        "expected_requirements": ['R027', 'R042', 'R054', 'R071', 'R085', 'AI001', 'AI016', 'AI017', 'HE012', 'ACM002', 'ACM013'],
        "expected_rights": ['Art21_NonDiscrimination', 'Art41_GoodAdministration', 'Art47_RightToEffectiveRemedy'],
        "expected_charter_articles": ['Art21_NonDiscrimination', 'Art41_GoodAdministration', 'Art47_RightToEffectiveRemedy'],
        "expected_risks": ['Discrimination', 'Accountability'],
        "expected_risk_categories": ['Discrimination', 'Accountability'],
    },

    {
        "id": 'P12',
        "title": 'ML Model for Hospital Bed Allocation',
        "risk_level": 'Medium',
        "proposal_text": """This research proposes to develop a machine learning model to optimise hospital bed allocation across three Dublin hospitals. The model will predict patient length of stay, readmission risk, and discharge timing using electronic health records including diagnosis codes, vital signs, medication history, and demographic information including age, gender, and medical card status. The training dataset consists of 80,000 anonymised patient records from 2018-2024. The model will generate daily recommendations for bed managers on patient transfers and early discharge candidates. The researchers acknowledge that medical card status (a proxy for socioeconomic deprivation) could influence the model's predictions in ways that disadvantage lower-income patients. The model outputs will be advisory but will be integrated into the hospital's electronic patient record system. No mechanism for clinical override documentation has been designed.""",
        "expected_requirements": ['R027', 'R042', 'R054', 'R071', 'R085', 'AI001', 'AI008', 'AI024', 'HE003', 'ACM001', 'ACM014'],
        "expected_rights": ['Art35_HealthCare', 'Art21_NonDiscrimination', 'Art2_RightToLife', 'Art8_DataProtection'],
        "expected_charter_articles": ['Art35_HealthCare', 'Art21_NonDiscrimination', 'Art2_RightToLife', 'Art8_DataProtection'],
        "expected_risks": ['Discrimination', 'PhysicalHarm'],
        "expected_risk_categories": ['Discrimination', 'PhysicalHarm'],
    },


    # ══════════════════════════════════════════════════════════════════════════
    # LOW RISK (P13–P16)
    # ══════════════════════════════════════════════════════════════════════════

    {
        "id": 'P13',
        "title": 'Bibliometric Analysis of Open Access AI Ethics Publications',
        "risk_level": 'Low',
        "proposal_text": """This research proposes to conduct a bibliometric analysis of peer-reviewed publications on AI ethics from 2018-2025. The study will use the Scopus and Web of Science databases to identify all publications containing keywords related to AI ethics, responsible AI, algorithmic fairness, and AI governance. The analysis will examine publication trends, citation networks, geographic distribution of research groups, and thematic clustering using topic modelling. All data is publicly available metadata from academic databases. No personal data about individual researchers will be collected beyond publicly listed author names and institutional affiliations. The analysis will use standard bibliometric tools including VOSviewer and Bibliometrix. Results will identify gaps in the AI ethics literature to inform future research directions. No AI systems will be developed or deployed as part of this research.""",
        "expected_requirements": ['R001', 'R006', 'R057', 'HE023', 'ACM018'],
        "expected_rights": ['Art11_FreedomOfExpression'],
        "expected_charter_articles": ['Art11_FreedomOfExpression'],
        "expected_risks": [],
        "expected_risk_categories": [],
    },

    {
        "id": 'P14',
        "title": 'NLP-Assisted Systematic Literature Review Tool',
        "risk_level": 'Low',
        "proposal_text": """This project aims to develop an NLP pipeline to assist researchers in conducting systematic literature reviews. The tool will automate the screening of academic paper abstracts against predefined inclusion and exclusion criteria, reducing the manual workload of the initial screening phase. The system will use pre-trained transformer models to classify abstracts as relevant or irrelevant based on researcher-defined criteria. The tool will be evaluated on a benchmark of three previously completed systematic reviews where human screening decisions are available as ground truth. All data consists of publicly available academic abstracts. The tool will provide a confidence score alongside each classification to guide manual verification. The researchers will open-source the tool for academic use. No personal data is involved at any stage.""",
        "expected_requirements": ['R001', 'R054', 'R057', 'HE023', 'ACM018', 'ACM029'],
        "expected_rights": ['Art11_FreedomOfExpression'],
        "expected_charter_articles": ['Art11_FreedomOfExpression'],
        "expected_risks": [],
        "expected_risk_categories": [],
    },

    {
        "id": 'P15',
        "title": 'Public Transport Usage Pattern Analysis',
        "risk_level": 'Low',
        "proposal_text": """This research proposes to analyse anonymised Dublin Bus and Luas smart card tap-on data to model public transport usage patterns across different times of day, routes, and weather conditions. The dataset consists of aggregated journey counts per route per hour provided by the National Transport Authority under an open data licence. No individual passenger records are included and no re-identification is possible from the aggregated data. The analysis will use time series forecasting and clustering algorithms to identify underserved routes and peak demand periods. Results will be shared with Dublin City Council to inform transport planning decisions. The environmental impact of the computational resources required for the analysis will be documented. No AI system will be deployed in any operational context.""",
        "expected_requirements": ['R001', 'R052', 'R057', 'HE018', 'HE023', 'ACM026'],
        "expected_rights": ['Art37_EnvironmentalProtection'],
        "expected_charter_articles": ['Art37_EnvironmentalProtection'],
        "expected_risks": [],
        "expected_risk_categories": [],
    },

    {
        "id": 'P16',
        "title": 'Climate Dataset Trend Analysis Using Statistical ML',
        "risk_level": 'Low',
        "proposal_text": """This project proposes to apply statistical machine learning methods to publicly available climate datasets from Met Éireann and the European Centre for Medium-Range Weather Forecasts. The research will analyse temperature, precipitation, and wind patterns across Ireland over the past 50 years to identify statistically significant trends and regional variations. The methodology combines Gaussian process regression with ensemble methods to quantify prediction uncertainty. All datasets are publicly available under open government data licences. No personal data is involved. The computational resources required for model training will be documented including estimated carbon footprint using the ML CO2 Impact calculator. Results will be published as an open-access paper with all code and data made available in a public repository.""",
        "expected_requirements": ['R001', 'R052', 'R057', 'HE018', 'HE023', 'ACM026', 'ACM038'],
        "expected_rights": ['Art37_EnvironmentalProtection'],
        "expected_charter_articles": ['Art37_EnvironmentalProtection'],
        "expected_risks": [],
        "expected_risk_categories": [],
    },


    # ══════════════════════════════════════════════════════════════════════════
    # EDGE CASES (P17–P20)
    # ══════════════════════════════════════════════════════════════════════════

    {
        "id": 'P17',
        "title": 'Dual-Use AI for Detecting Online Extremist Content',
        "risk_level": 'High',
        "proposal_text": """This research proposes to develop an NLP classifier to detect extremist recruitment content on social media platforms including Telegram, Twitter/X, and encrypted messaging forums. The classifier will be trained on a dataset of 20,000 annotated posts collected from known extremist channels alongside 20,000 non-extremist posts covering political activism, religious discussion, and protest organisation. The system must distinguish between legitimate political expression and genuine incitement to violence. The training data includes content in English, Arabic, and Irish. The researchers acknowledge the dual-use risk that the classifier could be repurposed for political censorship or suppression of minority viewpoints by authoritarian actors. The tool will be developed as open-source software. No content moderation decisions will be automated. The research does not include engagement with affected communities or civil liberties organisations in the design process.""",
        "expected_requirements": ['R001', 'R010', 'R019', 'R027', 'R054', 'R071', 'R085', 'AI001', 'HE005', 'HE019', 'HE021', 'ACM020', 'ACM025'],
        "expected_rights": ['Art11_FreedomOfExpression', 'Art12_FreedomOfAssembly', 'Art21_NonDiscrimination', 'Art1_HumanDignity', 'Art7_PrivateLife'],
        "expected_charter_articles": ['Art11_FreedomOfExpression', 'Art12_FreedomOfAssembly', 'Art21_NonDiscrimination', 'Art1_HumanDignity', 'Art7_PrivateLife'],
        "expected_risks": ['Discrimination', 'ExpressionHarm', 'DualUseMisuse'],
        "expected_risk_categories": ['Discrimination', 'ExpressionHarm', 'DualUseMisuse'],
    },

    {
        "id": 'P18',
        "title": 'Agentic AI Research Assistant with Web Access',
        "risk_level": 'High',
        "proposal_text": """This project proposes to develop an autonomous AI research assistant capable of independently searching the web, reading academic papers, summarising findings, and drafting literature review sections. The agent will use a large language model with tool-use capabilities including web browsing, PDF parsing, database querying, and file creation. The agent will operate with minimal human oversight, executing multi-step research tasks overnight and presenting results for review the following morning. The system will access academic databases using the researcher's institutional credentials. The agent may encounter and process personal data, copyrighted material, and sensitive research findings during its autonomous web browsing. No guardrails have been implemented to prevent the agent from accessing restricted databases, submitting forms, or interacting with external services beyond its intended scope. The researchers plan to evaluate the agent's output quality but have not addressed accountability for errors, hallucinated citations, or unintended data access.""",
        "expected_requirements": ['R001', 'R010', 'R027', 'R054', 'R071', 'AI001', 'AI008', 'AI010', 'HE001', 'HE006', 'ACM001', 'ACM017'],
        "expected_rights": ['Art41_GoodAdministration', 'Art8_DataProtection', 'Art7_PrivateLife', 'Art1_HumanDignity'],
        "expected_charter_articles": ['Art41_GoodAdministration', 'Art8_DataProtection', 'Art7_PrivateLife', 'Art1_HumanDignity'],
        "expected_risks": ['Accountability', 'PrivacyBreach', 'FunctionCreep'],
        "expected_risk_categories": ['Accountability', 'PrivacyBreach', 'FunctionCreep'],
    },

    {
        "id": 'P19',
        "title": 'Cross-Border EU/US Medical Data Sharing for Rare Disease AI',
        "risk_level": 'High',
        "proposal_text": """This research proposes a collaboration between Trinity College Dublin and Johns Hopkins University to develop an AI diagnostic model for rare genetic conditions. The project requires sharing patient genomic data and medical imaging between Ireland and the United States. The Irish dataset of 2,000 patients was collected under GDPR with consent for domestic research use only. The US dataset was collected under HIPAA regulations. The researchers propose to use federated learning to train the model without raw data leaving each jurisdiction, but the federated learning protocol requires sharing model gradient updates which have been shown in recent research to be vulnerable to reconstruction attacks that can recover individual patient data. The project has received funding approval but cross-border data transfer impact assessments have not been completed. The rare disease patient population is small enough that anonymisation may not prevent re-identification. No patient advisory group has been consulted on the data sharing arrangements.""",
        "expected_requirements": ['R005', 'R023', 'R024', 'R027', 'R029', 'R042', 'R054', 'R071', 'AI011', 'AI013', 'AI014', 'AI025', 'HE007', 'HE008', 'HE009', 'ACM003', 'ACM008'],
        "expected_rights": ['Art8_DataProtection', 'Art7_PrivateLife', 'Art35_HealthCare', 'Art2_RightToLife'],
        "expected_charter_articles": ['Art8_DataProtection', 'Art7_PrivateLife', 'Art35_HealthCare', 'Art2_RightToLife'],
        "expected_risks": ['PrivacyBreach', 'DataBreach', 'PhysicalHarm'],
        "expected_risk_categories": ['PrivacyBreach', 'DataBreach', 'PhysicalHarm'],
    },

    {
        "id": 'P20',
        "title": 'Workplace Productivity Monitoring with Employee Consent',
        "risk_level": 'Medium',
        "proposal_text": """This research proposes to study the relationship between digital workplace behaviours and productivity by monitoring 200 consenting employees at a Dublin technology company over six months. The monitoring system will track application usage, email response times, meeting attendance, keyboard activity patterns, and break frequency. All participants will provide written informed consent and can withdraw at any time without workplace consequences. Data will be stored on encrypted university servers and destroyed after the study period. However, the monitoring software will also incidentally capture screen content including potentially sensitive communications. Aggregate productivity patterns will be shared with the employer in a format that does not identify individual employees, but the small team sizes of 5-8 people within departments may enable indirect identification. The employer has stated that monitoring results will not influence performance reviews, but this commitment is not legally binding. The research does not address the power imbalance between employer and employee that may compromise the voluntariness of consent.""",
        "expected_requirements": ['R001', 'R005', 'R010', 'R019', 'R023', 'R027', 'R042', 'R054', 'AI011', 'HE007', 'HE020', 'ACM003', 'ACM011'],
        "expected_rights": ['Art7_PrivateLife', 'Art8_DataProtection', 'Art31_FairWorkingConditions', 'Art15_FreedomOfOccupation'],
        "expected_charter_articles": ['Art7_PrivateLife', 'Art8_DataProtection', 'Art31_FairWorkingConditions', 'Art15_FreedomOfOccupation'],
        "expected_risks": ['Surveillance', 'PrivacyBreach', 'EmploymentHarm'],
        "expected_risk_categories": ['Surveillance', 'PrivacyBreach', 'EmploymentHarm'],
    },

]
