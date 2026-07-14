# Diagrams for the Trinity-format paper

Five diagrams below, as Mermaid code. For each:

1. Paste the code into https://mermaid.live
2. Export as PNG or SVG (Actions > download)
3. Save into this `diagrams/` folder using **exactly** the filename given (the .tex file already references these names)
4. Recompile `main.tex`

Diagram 1 (`concept-diagram.png`) recreates and extends your existing drawio ontology diagram —
same classes and relationships, redrawn in Mermaid so it's version-controllable and editable as text.
Diagrams 2–5 are new: system architecture, knowledge graph schema, evaluation/ablation methodology,
and the retrieval-vs-generation finding that's the paper's central result.

---

## 1. Ontology concept diagram — save as `concept-diagram.png`

```mermaid
classDiagram
    direction TB
    class ResearchProposal
    class Framework
    class Requirement
    class Tier
    class Evidence
    class EUCharterRight
    class Incident
    class RiskCategory
    class Mitigation

    ResearchProposal --> Framework : triggersAssessment
    Framework --> Requirement : hasRequirement
    Requirement --> Evidence : requiresEvidence
    Requirement --> Tier : hasTier
    Requirement --> EUCharterRight : mapsToRight
    Incident --> Requirement : supportsRequirement
    Incident --> RiskCategory : demonstratesRisk
    Incident --> EUCharterRight : impactsRight
    RiskCategory --> Mitigation : mitigatedBy
```

## 2. System architecture — save as `architecture-flow.png`

```mermaid
flowchart LR
    A[Free-text\nResearch Proposal] --> B[Keyword\nExtraction]
    B --> C[SPARQL Retrieval\nGraphDB]
    C --> D[Prompt\nConstruction]
    D --> E[LLM Generation\nLlama 3.1 8B / 3.3 70B]
    E --> F[Structured\nAssessment]

    C -.-> G[(Knowledge Graph\n207 requirements\n70 incidents\n342 rights mappings)]
    G -.-> C

    F --> H[Risk Level]
    F --> I[Requirement IDs\n+ provenance]
    F --> J[Charter Rights]
    F --> K[Incident\nPrecedents]
    F --> L[Mitigations]

    style G fill:#e8f0fe,stroke:#4285f4
    style A fill:#fff3e0,stroke:#fb8c00
    style F fill:#e6f4ea,stroke:#34a853
```

## 3. Knowledge graph schema (framework harmonisation) — save as `kg-schema.png`

```mermaid
flowchart TB
    subgraph Frameworks
        REAMS[REAMS\nR001-R087\n87 requirements]
        AIACT[EU AI Act\nAI001-AI030\n30 requirements]
        HE[Horizon Europe\nHE001-HE052\n52 requirements]
        ACM[ACM / NeurIPS\nACM001-ACM038\n38 requirements]
    end

    REAMS --> REQ[Requirement\n207 total]
    AIACT --> REQ
    HE --> REQ
    ACM --> REQ

    REQ -->|mapsToRight\n342 triples| RIGHTS[EU Charter of\nFundamental Rights\n18 articles mapped]

    INC[AI Incidents\n70 curated\nAIAAIC + AIID] -->|impactsRight| RIGHTS
    INC -->|supportsRequirement| REQ

    style REQ fill:#e6f4ea,stroke:#34a853
    style RIGHTS fill:#fce8e6,stroke:#ea4335
    style INC fill:#f3e8fd,stroke:#a142f4
```

## 4. Ablation study methodology — save as `ablation-methodology.png`

```mermaid
flowchart TB
    P[Research Proposal] --> A
    P --> B
    P --> C

    subgraph A[Condition A: LLM Only]
        A1[No KG context] --> A2[No traceable\nrequirement IDs]
        A2 --> A3[Hallucinated /\nabsent incidents]
    end

    subgraph B[Condition B: KG Only]
        B1[SPARQL retrieval\nno interpretation] --> B2[All matched\nrequirements returned]
        B2 --> B3[8 incidents,\n9-11 rights\nno narrative]
    end

    subgraph C[Condition C: Full Pipeline]
        C1[SPARQL retrieval\n+ LLM interpretation] --> C2[Cited requirements\nwith provenance]
        C2 --> C3[1-2 grounded\nincidents, 2-4 rights]
    end

    style A fill:#fce8e6,stroke:#ea4335
    style B fill:#fff3e0,stroke:#fb8c00
    style C fill:#e6f4ea,stroke:#34a853
```

## 5. Central finding — retrieval vs. generation — save as `central-finding.png`

```mermaid
flowchart LR
    subgraph Retrieval["Retrieval (Knowledge Graph)"]
        direction TB
        R1[Llama 3.1 8B: 0.99 recall]
        R2[Llama 3.3 70B: 0.99 recall]
        R3["Model-agnostic →\nstable, reusable"]
        R1 --> R3
        R2 --> R3
    end

    subgraph Generation["Generation (LLM)"]
        direction TB
        G1[Llama 3.1 8B: 65% accuracy]
        G2[Llama 3.3 70B: 90% accuracy]
        G3["Scales with model\ncapacity"]
        G1 --> G3
        G2 --> G3
    end

    Retrieval -.->|separable dimensions,\nGao et al. 2023| Generation

    style Retrieval fill:#e6f4ea,stroke:#34a853
    style Generation fill:#e8f0fe,stroke:#4285f4
```
