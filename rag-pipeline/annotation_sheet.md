# AIEF second-annotator sheet
For each proposal: risk level (High/Medium/Low) and applicable Charter articles (comma-separated, e.g. Article7, Article8).
Do not consult the system or the first annotator.

---
## P01
This research proposes to develop a commercial health risk stratification algorithm to identify high-need patients for enrolment in care management programmes across a network of US hospital systems. The algorithm will use insurance claims data as a proxy for health need, predicting which patients require additional clinical resources based on historical healthcare costs, prior diagnoses, medication use, and utilisation patterns from electronic health records covering approximately 200 million patients annually. Patients scoring in the top 3 percentile will automatically be referred to care management; those in the top 45 percentile will be assessed for referral. The algorithm will not explicitly use race as a predictive variable. However, because Black patients have historically incurred lower healthcare costs than white patients with equivalent chronic disease burden — due to structural barriers to healthcare access including cost, discrimination, and geographic distance — the cost proxy will systematically underestimate the health needs of Black patients. The algorithm has not undergone independent bias auditing prior to deployment. No mechanism for algorithmic review or patient appeal of care management non-referral decisions is planned.

**Risk level:** ____
**Charter articles:** ____

---
## P02
This research proposes to deploy the COMPAS (Correctional Offender Management Profiling for Alternative Sanctions) risk assessment tool across criminal courts in Broward County, Florida, to predict defendants' likelihood of recidivism. The system uses a proprietary algorithm trained on a battery of psychological questionnaire responses administered at the time of arrest, combined with criminal history variables including prior arrest count, age at first offence, and charge severity. The algorithm produces three decile scores (1–10) for general recidivism, violent recidivism, and failure to appear, with scores categorised as Low (1–4), Medium (5–7), or High (8–10). These scores will be provided to judges and parole officers at pre-trial hearings and sentencing to inform detention and release decisions. The model is proprietary and its internal weighting is not disclosed to defendants or defence counsel. No mechanism for defendants to challenge the algorithmic risk score is included in the deployment design. An independent analysis of the algorithm's outputs found that Black defendants who did not re-offend were falsely classified as high risk at nearly twice the rate of white defendants who did not re-offend (45% vs 24%).

**Risk level:** ____
**Charter articles:** ____

---
## P03
This research proposes to deploy Amazon Rekognition, a cloud-based facial recognition system, for use by law enforcement agencies across the United States to identify individuals in real-time surveillance footage, body camera recordings, and crime scene images. The system can identify and track up to 100 faces in a single image and match them against databases of tens of millions of faces drawn from arrest records and public sources. The system will be marketed to local police departments as a tool for identifying persons of interest in criminal investigations. The default confidence threshold of 80% will be used for initial deployment, with Amazon recommending a 99% threshold for law enforcement use — a discrepancy between default settings and recommended settings that has not been addressed in the deployment contract. An ACLU audit found that at 80% confidence, Rekognition falsely matched 28 members of the US Congress to criminal mugshots, with disproportionate false positives for people of colour including six members of the Congressional Black Caucus. No independent demographic bias audit has been conducted prior to law enforcement deployment. No independent oversight mechanism or accountability framework for false match consequences has been established.

**Risk level:** ____
**Charter articles:** ____

---
## P04
This research proposes to develop a machine learning-based ad delivery optimisation system for deployment on a major social media platform. The system will use a multi-objective optimisation algorithm that maximises ad relevance scores and advertiser return on investment by predicting which users are most likely to engage with each advertisement. The algorithm will use thousands of user behavioural, demographic, and interest signals — excluding explicit race and gender variables — to determine ad delivery. The system will operate as a real-time auction where advertisers bid for impression opportunities, with the platform's relevance prediction model determining which users see which ads. An academic audit of this system found that even when advertisers set their targeting parameters to be fully inclusive with no demographic restrictions, the optimisation algorithm delivered employment ads predominantly to men and housing ads predominantly to white users. This skew was caused by the algorithm's financial optimisation function, which learned that majority-group users were cheaper to reach and more likely to engage. The system does not include pre-deployment fairness auditing. No mechanism for individual users to understand why they are or are not shown specific opportunity-related advertisements is planned.

**Risk level:** ____
**Charter articles:** ____

---
## P05
This research proposes to deploy a machine learning sepsis prediction algorithm across NHS England hospital trusts to identify patients at risk of sepsis deterioration in emergency department and ward settings. The algorithm uses physiological parameters including respiratory rate, oxygen saturation, temperature, systolic blood pressure, pulse rate, and level of consciousness — as recorded in the National Early Warning Score 2 (NEWS2) framework — alongside laboratory values and electronic health record data, to generate real-time risk scores for clinical staff. The training dataset was drawn predominantly from NHS patient records which have documented under-representation of Black, Asian, and minority ethnic patient populations in specialist care pathways. Academic analysis has found that vital signs used as predictive features are racially skewed, as minority patients may exhibit different baseline physiological profiles than the majority-white training population. The algorithm has not undergone prospective demographic bias auditing across ethnic subgroups prior to nationwide deployment. Clinical staff will receive risk scores without visibility into the algorithm's feature weighting or demographic performance variance. No formal mechanism for clinicians to record or escalate concerns about demographic performance disparities is included in the deployment framework.

**Risk level:** ____
**Charter articles:** ____

---
## P06
This project proposes to install camera-based emotion recognition systems in six secondary school classrooms in Dublin to study the relationship between student emotional engagement and learning outcomes. The system will use computer vision to classify student facial expressions into six emotional categories (happy, sad, angry, surprised, fearful, neutral) at 5-second intervals throughout lessons. Data will be collected over one academic term covering approximately 180 students aged 13-17. Parental consent will be obtained but students will not be given an individual opt-out mechanism that allows them to remain in the classroom without being monitored. The emotion recognition system has been validated primarily on adult Western faces and has not been tested for accuracy on adolescent faces or faces from diverse ethnic backgrounds. Aggregated emotional engagement scores will be shared with teachers to inform pedagogical adjustments.

**Risk level:** ____
**Charter articles:** ____

---
## P07
This research proposes to apply sentiment analysis and linguistic style detection to a corpus of 5,000 anonymised undergraduate essays submitted to the School of English at Trinity College Dublin. The aim is to investigate whether emotional tone and writing style correlate with academic grade outcomes. Essays will be collected from the past three academic years with student consent obtained retrospectively via email. The NLP pipeline will extract features including sentiment polarity, subjectivity scores, vocabulary complexity, and sentence structure patterns. The researchers will investigate whether detectable stylistic differences correlate with students' first language, gender, or socioeconomic background as indicated by fee status. All analysis will be performed on pseudonymised data with student IDs replaced by random codes. Results will be published in aggregate form only.

**Risk level:** ____
**Charter articles:** ____

---
## P08
This project proposes to develop a conversational AI chatbot to provide initial mental health support triage for university students. The chatbot will conduct a structured conversational assessment to evaluate symptoms of anxiety and depression using validated clinical screening instruments (PHQ-9, GAD-7) adapted into conversational format. Based on the assessment, the chatbot will recommend one of three pathways: self-help resources, a scheduled counselling appointment, or immediate crisis intervention referral. The chatbot will store conversation logs for quality improvement purposes. Student data will be pseudonymised but linked to student records to enable follow-up. The chatbot will include a disclaimer that it is not a substitute for professional mental health care. The system has not been validated against clinical assessments performed by qualified professionals. Conversations will be processed by an external cloud-based NLP service.

**Risk level:** ____
**Charter articles:** ____

---
## P09
This research proposes to build a recommendation system for academic module selection at Trinity College Dublin. The system will analyse historical student records including module choices, grades achieved, attendance patterns, and degree outcomes to recommend optimal module combinations for current students. The dataset covers 20,000 student records from the past ten years. Students will receive personalised module recommendations through the student portal alongside existing manual advising. The system will use collaborative filtering to identify students with similar academic profiles and recommend modules that led to positive outcomes for comparable students. The researchers acknowledge that historical patterns may reflect systemic inequalities in module access and outcomes. The model will not account for disability accommodations or students who changed programmes. Student consent for the use of historical academic records in the training dataset has not been explicitly obtained.

**Risk level:** ____
**Charter articles:** ____

---
## P10
This project aims to develop an NLP-based tool for detecting health-related misinformation on Irish social media platforms. The system will collect public posts from Twitter/X, Reddit, and Facebook groups discussing topics including vaccination, cancer treatments, and mental health remedies. The tool will classify posts as verified, unverified, or misleading using a combination of source credibility scoring and claim verification against WHO and HSE published guidelines. The dataset will include approximately 500,000 public posts collected via platform APIs. While posts are publicly available, the tool will process usernames and account metadata to assess source credibility patterns. The researchers plan to publish a list of accounts identified as frequent misinformation sources. The tool does not account for satire, cultural context, or legitimate medical debate where scientific consensus has not been established.

**Risk level:** ____
**Charter articles:** ____

---
## P11
This research proposes to develop an automated essay grading system for first-year undergraduate modules at Trinity College Dublin. The system will use large language model embeddings to score essays on a 0-100 scale by comparing them against a rubric-encoded scoring model trained on 3,000 previously graded essays. The system will provide both a numerical grade and written feedback comments generated by the LLM. The tool is intended to reduce marking workload by providing initial scores that lecturers can review and adjust. The training data consists of essays graded by twelve different tutors whose grading standards varied considerably. Students whose first language is not English may receive systematically different scores due to the model's sensitivity to grammatical patterns associated with non-native speakers. Students will not be informed that AI-assisted grading is being used. No appeals process specifically addressing algorithmic grading errors has been designed.

**Risk level:** ____
**Charter articles:** ____

---
## P12
This research proposes to develop a machine learning model to optimise hospital bed allocation across three Dublin hospitals. The model will predict patient length of stay, readmission risk, and discharge timing using electronic health records including diagnosis codes, vital signs, medication history, and demographic information including age, gender, and medical card status. The training dataset consists of 80,000 anonymised patient records from 2018-2024. The model will generate daily recommendations for bed managers on patient transfers and early discharge candidates. The researchers acknowledge that medical card status (a proxy for socioeconomic deprivation) could influence the model's predictions in ways that disadvantage lower-income patients. The model outputs will be advisory but will be integrated into the hospital's electronic patient record system. No mechanism for clinical override documentation has been designed.

**Risk level:** ____
**Charter articles:** ____

---
## P13
This research proposes to conduct a bibliometric analysis of peer-reviewed publications on AI ethics from 2018-2025. The study will use the Scopus and Web of Science databases to identify all publications containing keywords related to AI ethics, responsible AI, algorithmic fairness, and AI governance. The analysis will examine publication trends, citation networks, geographic distribution of research groups, and thematic clustering using topic modelling. All data is publicly available metadata from academic databases. No personal data about individual researchers will be collected beyond publicly listed author names and institutional affiliations. The analysis will use standard bibliometric tools including VOSviewer and Bibliometrix. Results will identify gaps in the AI ethics literature to inform future research directions. No AI systems will be developed or deployed as part of this research.

**Risk level:** ____
**Charter articles:** ____

---
## P14
This project aims to develop an NLP pipeline to assist researchers in conducting systematic literature reviews. The tool will automate the screening of academic paper abstracts against predefined inclusion and exclusion criteria, reducing the manual workload of the initial screening phase. The system will use pre-trained transformer models to classify abstracts as relevant or irrelevant based on researcher-defined criteria. The tool will be evaluated on a benchmark of three previously completed systematic reviews where human screening decisions are available as ground truth. All data consists of publicly available academic abstracts. The tool will provide a confidence score alongside each classification to guide manual verification. The researchers will open-source the tool for academic use. No personal data is involved at any stage.

**Risk level:** ____
**Charter articles:** ____

---
## P15
This research proposes to analyse anonymised Dublin Bus and Luas smart card tap-on data to model public transport usage patterns across different times of day, routes, and weather conditions. The dataset consists of aggregated journey counts per route per hour provided by the National Transport Authority under an open data licence. No individual passenger records are included and no re-identification is possible from the aggregated data. The analysis will use time series forecasting and clustering algorithms to identify underserved routes and peak demand periods. Results will be shared with Dublin City Council to inform transport planning decisions. The environmental impact of the computational resources required for the analysis will be documented. No AI system will be deployed in any operational context.

**Risk level:** ____
**Charter articles:** ____

---
## P16
This project proposes to apply statistical machine learning methods to publicly available climate datasets from Met Éireann and the European Centre for Medium-Range Weather Forecasts. The research will analyse temperature, precipitation, and wind patterns across Ireland over the past 50 years to identify statistically significant trends and regional variations. The methodology combines Gaussian process regression with ensemble methods to quantify prediction uncertainty. All datasets are publicly available under open government data licences. No personal data is involved. The computational resources required for model training will be documented including estimated carbon footprint using the ML CO2 Impact calculator. Results will be published as an open-access paper with all code and data made available in a public repository.

**Risk level:** ____
**Charter articles:** ____

---
## P17
This research proposes to develop an NLP classifier to detect extremist recruitment content on social media platforms including Telegram, Twitter/X, and encrypted messaging forums. The classifier will be trained on a dataset of 20,000 annotated posts collected from known extremist channels alongside 20,000 non-extremist posts covering political activism, religious discussion, and protest organisation. The system must distinguish between legitimate political expression and genuine incitement to violence. The training data includes content in English, Arabic, and Irish. The researchers acknowledge the dual-use risk that the classifier could be repurposed for political censorship or suppression of minority viewpoints by authoritarian actors. The tool will be developed as open-source software. No content moderation decisions will be automated. The research does not include engagement with affected communities or civil liberties organisations in the design process.

**Risk level:** ____
**Charter articles:** ____

---
## P18
This project proposes to develop an autonomous AI research assistant capable of independently searching the web, reading academic papers, summarising findings, and drafting literature review sections. The agent will use a large language model with tool-use capabilities including web browsing, PDF parsing, database querying, and file creation. The agent will operate with minimal human oversight, executing multi-step research tasks overnight and presenting results for review the following morning. The system will access academic databases using the researcher's institutional credentials. The agent may encounter and process personal data, copyrighted material, and sensitive research findings during its autonomous web browsing. No guardrails have been implemented to prevent the agent from accessing restricted databases, submitting forms, or interacting with external services beyond its intended scope. The researchers plan to evaluate the agent's output quality but have not addressed accountability for errors, hallucinated citations, or unintended data access.

**Risk level:** ____
**Charter articles:** ____

---
## P19
This research proposes a collaboration between Trinity College Dublin and Johns Hopkins University to develop an AI diagnostic model for rare genetic conditions. The project requires sharing patient genomic data and medical imaging between Ireland and the United States. The Irish dataset of 2,000 patients was collected under GDPR with consent for domestic research use only. The US dataset was collected under HIPAA regulations. The researchers propose to use federated learning to train the model without raw data leaving each jurisdiction, but the federated learning protocol requires sharing model gradient updates which have been shown in recent research to be vulnerable to reconstruction attacks that can recover individual patient data. The project has received funding approval but cross-border data transfer impact assessments have not been completed. The rare disease patient population is small enough that anonymisation may not prevent re-identification. No patient advisory group has been consulted on the data sharing arrangements.

**Risk level:** ____
**Charter articles:** ____

---
## P20
This research proposes to study the relationship between digital workplace behaviours and productivity by monitoring 200 consenting employees at a Dublin technology company over six months. The monitoring system will track application usage, email response times, meeting attendance, keyboard activity patterns, and break frequency. All participants will provide written informed consent and can withdraw at any time without workplace consequences. Data will be stored on encrypted university servers and destroyed after the study period. However, the monitoring software will also incidentally capture screen content including potentially sensitive communications. Aggregate productivity patterns will be shared with the employer in a format that does not identify individual employees, but the small team sizes of 5-8 people within departments may enable indirect identification. The employer has stated that monitoring results will not influence performance reviews, but this commitment is not legally binding. The research does not address the power imbalance between employer and employee that may compromise the voluntariness of consent.

**Risk level:** ____
**Charter articles:** ____

---
## Mapping validity (agree/disagree)
For each requirement→right mapping, mark A (agree) or D (disagree).

| Req | Mapped right | A/D |
|---|---|---|
| R085 | Art21_NonDiscrimination |  |
| R085 | Art20_EqualityBeforeLaw |  |
| R042 | Art8_DataProtection |  |
| R019 | Art7_PrivateLife |  |
| ACM005 | Art17_RightToProperty |  |
| ACM023 | Art21_NonDiscrimination |  |
| AI001 | Art47_RightToEffectiveRemedy |  |
| HE012 | Art21_NonDiscrimination |  |
| R068 | Art8_DataProtection |  |
| ACM011 | Art31_FairWorkingConditions |  |
| R027 | Art8_DataProtection |  |
| HE003 | Art1_HumanDignity |  |
| AI016 | Art21_NonDiscrimination |  |
| R071 | Art47_RightToEffectiveRemedy |  |
| ACM001 | Art1_HumanDignity |  |
| R054 | Art8_DataProtection |  |
| HE015 | Art21_NonDiscrimination |  |
| AI021 | Art41_GoodAdministration |  |
| R010 | Art6_RightToLiberty |  |
| ACM037 | Art31_FairWorkingConditions |  |
