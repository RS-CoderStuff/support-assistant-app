# Support Assistant Service - Architecture Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Query Understanding Pipeline](#query-understanding-pipeline)
6. [Retrieval Pipeline](#retrieval-pipeline)
7. [Conversation Management](#conversation-management)
8. [Security & Guardrails](#security--guardrails)
9. [Deployment Architecture](#deployment-architecture)
10. [API Reference](#api-reference)

---

## 🎯 System Overview

The **Support Assistant Service** is an intelligent conversational AI system designed to assist users with support queries. It leverages state-of-the-art AI services to provide contextual, accurate responses backed by a knowledge base.

### Key Capabilities
- 🤖 **Intelligent Query Understanding** - Classifies and rewrites user queries for optimal retrieval
- 📚 **Knowledge Base Integration** - Retrieves relevant documents from AWS Bedrock Knowledge Base
- 💬 **Conversation Context** - Maintains multi-turn conversation state
- 🛡️ **Security Guardrails** - Input/output validation to prevent prompt injection
- 📊 **Confidence Scoring** - Provides confidence metrics with citations

---

## 🏗️ High-Level Architecture

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#6366f1', 'primaryTextColor': '#fff', 'primaryBorderColor': '#4f46e5', 'lineColor': '#94a3b8', 'secondaryColor': '#f43f5e', 'tertiaryColor': '#10b981', 'background': '#f8fafc'}}}%%
flowchart TB
    subgraph Client["🖥️ Client Layer"]
        direction LR
        UI[("Web/Mobile\nClient")]
    end
    
    subgraph API["🌐 API Gateway"]
        direction TB
        FastAPI["FastAPI\nApplication"]
        Routes["API Routes"]
    end
    
    subgraph Core["⚙️ Core Engine"]
        direction TB
        Workflow["LangGraph\nWorkflow"]
        Services["Business\nServices"]
    end
    
    subgraph AWS["☁️ AWS Services"]
        direction TB
        Bedrock["Amazon\nBedrock"]
        KB["Knowledge\nBase"]
        DynamoDB[("DynamoDB")]
    end
    
    subgraph ML["🧠 AI/ML Layer"]
        direction TB
        LLM["LLM\n(Nova Lite)"]
        Ollama["Ollama\n(Local)"]
    end
    
    UI --> FastAPI
    FastAPI --> Routes
    Routes --> Workflow
    Workflow --> Services
    Services --> Bedrock
    Services --> KB
    Services --> DynamoDB
    Services --> LLM
    Services --> Ollama

    classDef client fill:#818cf8,stroke:#4f46e5,color:#fff
    classDef api fill:#f472b6,stroke:#db2777,color:#fff
    classDef core fill:#34d399,stroke:#059669,color:#fff
    classDef aws fill:#fbbf24,stroke:#d97706,color:#1f2937
    classDef ml fill:#a78bfa,stroke:#7c3aed,color:#fff
    
    class UI client
    class FastAPI,Routes api
    class Workflow,Services core
    class Bedrock,KB,DynamoDB aws
    class LLM,Ollama ml
```

---

## 🧩 Component Architecture

### Application Structure

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#3b82f6', 'secondaryColor': '#8b5cf6'}}}%%
graph TD
    subgraph Application["📦 support-assistant-service"]
        subgraph API["api/"]
            Routes["routes/"]
            Schemas["schemas/"]
        end
        
        subgraph Services["services/"]
            QU["Query\nUnderstanding"]
            QC["Query\nClassifier"]
            QR["Query\nRewriter"]
            ME["Metadata\nExtractor"]
            MF["Metadata\nFilter Builder"]
            RD["Retrieval\nDecision"]
            RR["Reranker"]
            EV["Evidence\nValidator"]
            LLM["LLM\nService"]
            PB["Prompt\nBuilder"]
            CM["Conversation\nManager"]
            GS["Guardrail\nService"]
        end
        
        subgraph Graph["graph/"]
            AG["Assistant\nGraph"]
            State["State\nDefinition"]
        end
        
        subgraph AWS["aws/"]
            BRC["Bedrock\nClient"]
            KBC["KB Client"]
            DBC["DynamoDB\nClient"]
        end
        
        subgraph Models["models/"]
            Conv["Conversation"]
            Retr["Retrieval"]
        end
        
        subgraph Repos["repositories/"]
            ConvRepo["Conversation\nRepository"]
        end
    end
    
    API --> Graph
    Graph --> Services
    Services --> AWS
    Services --> Models
    AWS --> Repos
    
    classDef apiStyle fill:#60a5fa,stroke:#2563eb,color:#fff
    classDef servicesStyle fill:#a78bfa,stroke:#7c3aed,color:#fff
    classDef graphStyle fill:#34d399,stroke:#059669,color:#fff
    classDef awsStyle fill:#fbbf24,stroke:#d97706,color:#1f2937
    classDef modelsStyle fill:#f472b6,stroke:#db2777,color:#fff
    
    class Routes,Schemas apiStyle
    class QU,QC,QR,ME,MF,RD,RR,EV,LLM,PB,CM,GS servicesStyle
    class AG,State graphStyle
    class BRC,KBC,DBC awsStyle
    class Conv,Retr,ConvRepo modelsStyle
```

### Directory Structure

```
support-assistant-service/
├── app/
│   ├── api/
│   │   ├── routes/          # API endpoint handlers
│   │   │   ├── assistant.py # Chat endpoint
│   │   │   ├── conversations.py
│   │   │   └── health.py
│   │   └── schemas/         # Request/Response models
│   │       ├── assistant.py
│   │       └── conversation.py
│   ├── aws/                 # AWS service clients
│   │   ├── bedrock_client.py
│   │   ├── bedrock_kb_client.py
│   │   └── dynamodb_client.py
│   ├── config/
│   │   └── settings.py      # Application configuration
│   ├── exceptions/
│   │   └── exceptions.py    # Custom exceptions
│   ├── graph/               # LangGraph workflow
│   │   ├── assistant_graph.py
│   │   └── state.py
│   ├── models/              # Domain models
│   │   ├── conversation.py
│   │   └── retrieval.py
│   ├── repositories/        # Data access layer
│   │   └── conversation_repository.py
│   ├── services/            # Business logic
│   │   ├── query_understanding.py
│   │   ├── query_classifier.py
│   │   ├── query_rewriter.py
│   │   ├── metadata_extractor.py
│   │   ├── metadata_filter_builder.py
│   │   ├── retrieval_decision.py
│   │   ├── reranker.py
│   │   ├── evidence_validator.py
│   │   ├── llm_service.py
│   │   ├── prompt_builder.py
│   │   ├── conversation_manager.py
│   │   ├── conversation_updater.py
│   │   └── guardrail_service.py
│   ├── utils/
│   │   └── logging.py
│   └── main.py              # Application entry point
├── tests/
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 🔄 Data Flow

### Request Processing Pipeline

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#6366f1'}}}%%
sequenceDiagram
    autonumber
    participant C as 🖥️ Client
    participant A as 🌐 API
    participant W as ⚙️ Workflow
    participant G as 🛡️ Guardrail
    participant Q as 🧠 Query Understanding
    participant R as 📚 Retrieval
    participant L as 🤖 LLM
    participant D as 💾 DynamoDB
    
    C->>A: POST /api/v1/assistant/chat
    A->>W: invoke(state)
    
    rect rgb(230, 240, 255)
        Note over W,D: Load Conversation Phase
        W->>D: get/create conversation
        D-->>W: conversation data
        W->>D: persist user message
    end
    
    rect rgb(255, 235, 235)
        Note over W,G: Input Validation Phase
        W->>G: validate input
        G-->>W: allowed/blocked
    end
    
    rect rgb(235, 255, 235)
        Note over W,Q: Query Understanding Phase
        W->>Q: understand query
        Q->>Q: classify query type
        Q->>Q: extract metadata
        Q->>Q: rewrite query
        Q-->>W: understanding result
    end
    
    rect rgb(255, 245, 235)
        Note over W,R: Retrieval Phase (conditional)
        W->>R: retrieve documents
        R->>R: query knowledge base
        R->>R: rerank results
        R->>R: validate evidence
        R-->>W: validated evidence
    end
    
    rect rgb(245, 235, 255)
        Note over W,L: Answer Generation Phase
        W->>L: generate answer
        L-->>W: response
        W->>G: validate output
        G-->>W: sanitized answer
    end
    
    rect rgb(235, 245, 255)
        Note over W,D: Update Phase
        W->>D: update conversation
        W->>D: persist assistant message
    end
    
    W-->>A: result state
    A-->>C: ChatResponse
```

### LangGraph Workflow Nodes

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#10b981'}}}%%
stateDiagram-v2
    [*] --> load_conversation
    load_conversation --> input_guardrail
    input_guardrail --> understand
    understand --> retrieve: retrieval_required = true
    understand --> answer: retrieval_required = false
    retrieve --> answer
    answer --> update_conversation
    update_conversation --> [*]
```

---

## 🧠 Query Understanding Pipeline

The Query Understanding system uses a **deterministic-first approach** with optional AI enhancement through local Ollama or cloud Bedrock fallback.

### Pipeline Architecture

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#8b5cf6'}}}%%
flowchart TB
    subgraph Input["📥 Input"]
        UM["User Message"]
        SI["Stored Issue"]
        RC["Request Context"]
    end
    
    subgraph Deterministic["🔧 Deterministic Layer"]
        direction TB
        QC["Query Classifier"]
        QR["Query Rewriter"]
        ME["Metadata Extractor"]
    end
    
    subgraph Semantic["🧠 Semantic Layer"]
        direction TB
        Need{{"Needs\nSemantic?"}}
        Local["Ollama\n(Local LLM)"]
        Cloud["Bedrock\n(Cloud Fallback)"]
        Conf{{"Confidence\n≥ 0.8?"}}
    end
    
    subgraph Output["📤 Output"]
        QT["Query Type"]
        RQ["Rewritten Query"]
        EM["Extracted Metadata"]
        CI["Current Issue"]
        RR["Retrieval Required"]
    end
    
    UM --> QC
    UM --> QR
    UM --> ME
    SI --> QR
    RC --> ME
    
    QC --> Need
    ME --> Need
    
    Need -->|Yes| Local
    Need -->|No| Output
    
    Local --> Conf
    Conf -->|Yes| Output
    Conf -->|No| Cloud
    Cloud --> Conf
    
    classDef inputStyle fill:#60a5fa,stroke:#2563eb,color:#fff
    classDef deterStyle fill:#34d399,stroke:#059669,color:#fff
    classDef semanticStyle fill:#a78bfa,stroke:#7c3aed,color:#fff
    classDef outputStyle fill:#f472b6,stroke:#db2777,color:#fff
    classDef decisionStyle fill:#fbbf24,stroke:#d97706,color:#1f2937
    
    class UM,SI,RC inputStyle
    class QC,QR,ME deterStyle
    class Local,Cloud semanticStyle
    class Need,Conf decisionStyle
    class QT,RQ,EM,CI,RR outputStyle
```

### Query Types

| Type | Description | Triggers Retrieval |
|------|-------------|-------------------|
| 🟢 `GREETING` | Social interaction | ❌ No |
| 🟢 `SUMMARY_REQUEST` | Request for conversation recap | ❌ No |
| 🟢 `CLARIFICATION` | Request to explain previous answer | ❌ No |
| 🟡 `FOLLOW_UP` | Continuation of current issue | ⚠️ Conditional |
| 🔴 `NEW_ISSUE` | New support issue reported | ✅ Yes |
| 🔴 `KNOWLEDGE_QUERY` | General knowledge question | ✅ Yes |

### Classification Logic

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#06b6d4'}}}%%
flowchart TD
    Start["User Message"]
    
    G{{"Contains greeting\nkeywords?"}}
    S{{"Contains 'summarize'\n+ conversation ref?"}}
    C{{"Has context &\n'explain/simple'?"}}
    F{{"Has context &\nreference words?"}}
    I{{"Contains error/\nissue keywords?"}}
    
    GREETING["🟢 GREETING"]
    SUMMARY["🟢 SUMMARY_REQUEST"]
    CLARIFICATION["🟢 CLARIFICATION"]
    FOLLOW_UP["🟡 FOLLOW_UP"]
    NEW_ISSUE["🔴 NEW_ISSUE"]
    KNOWLEDGE["🔴 KNOWLEDGE_QUERY"]
    
    Start --> G
    G -->|Yes| GREETING
    G -->|No| S
    S -->|Yes| SUMMARY
    S -->|No| C
    C -->|Yes| CLARIFICATION
    C -->|No| F
    F -->|Yes| FOLLOW_UP
    F -->|No| I
    I -->|Yes| NEW_ISSUE
    I -->|No| KNOWLEDGE
```

---

## 📚 Retrieval Pipeline

### Knowledge Base Integration

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#f59e0b'}}}%%
flowchart LR
    subgraph Query["🔍 Query"]
        RQ["Rewritten\nQuery"]
        MF["Metadata\nFilter"]
    end
    
    subgraph Retrieval["📦 Retrieval"]
        KB[("AWS Bedrock\nKnowledge Base")]
        VR["Managed\nSearch"]
    end
    
    subgraph Processing["⚙️ Processing"]
        RR["Reranker\n(Top 8)"]
        EV["Evidence\nValidator"]
    end
    
    subgraph Output["✅ Output"]
        VE["Validated\nEvidence\n(Top 5)"]
        CT["Citations"]
    end
    
    RQ --> VR
    MF --> VR
    VR --> KB
    KB --> RR
    RR --> EV
    EV --> VE
    EV --> CT
    
    classDef queryStyle fill:#60a5fa,stroke:#2563eb,color:#fff
    classDef retrievalStyle fill:#fbbf24,stroke:#d97706,color:#1f2937
    classDef processStyle fill:#34d399,stroke:#059669,color:#fff
    classDef outputStyle fill:#a78bfa,stroke:#7c3aed,color:#fff
    
    class RQ,MF queryStyle
    class KB,VR retrievalStyle
    class RR,EV processStyle
    class VE,CT outputStyle
```

### Document Processing Flow

| Stage | Count | Description |
|-------|-------|-------------|
| **Initial Retrieval** | 25 | Raw results from Knowledge Base |
| **After Reranking** | 8 | Sorted by relevance score |
| **After Validation** | 5 | Filtered by quality criteria |

### Evidence Validation Criteria

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#10b981'}}}%%
flowchart TD
    Doc["Retrieved Document"]
    
    S1{{"Score ≥ 0.72?"}}
    S2{{"Unique Source?"}}
    S3{{"No Prompt\nInjection?"}}
    S4{{"Active Status?"}}
    S5{{"Metadata\nMatch?"}}
    
    Valid["✅ Valid Evidence"]
    Invalid["❌ Filtered Out"]
    
    Doc --> S1
    S1 -->|Yes| S2
    S1 -->|No| Invalid
    S2 -->|Yes| S3
    S2 -->|No| Invalid
    S3 -->|Yes| S4
    S3 -->|No| Invalid
    S4 -->|Yes| S5
    S4 -->|No| Invalid
    S5 -->|Yes| Valid
    S5 -->|No| Invalid
    
    classDef checkStyle fill:#60a5fa,stroke:#2563eb,color:#fff
    classDef validStyle fill:#34d399,stroke:#059669,color:#fff
    classDef invalidStyle fill:#f87171,stroke:#dc2626,color:#fff
    
    class S1,S2,S3,S4,S5 checkStyle
    class Valid validStyle
    class Invalid invalidStyle
```

### Metadata Filter Building

Filters are constructed from **request context only** (not from conversation history) to ensure precise retrieval:

```mermaid
%%{init: {'theme': 'base'}}%%
flowchart LR
    RC["Request Context"]
    FB["Filter Builder"]
    MF["Metadata Filter"]
    
    RC --> FB
    FB --> MF
    
    subgraph Supported["Supported Fields"]
        P["product"]
        C["component"]
        E["environment"]
        ST["source_type"]
    end
```

---

## 💬 Conversation Management

### State Machine

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ec4899'}}}%%
stateDiagram-v2
    [*] --> ACTIVE: Create Conversation
    
    ACTIVE --> ACTIVE: User Message
    ACTIVE --> ACTIVE: Assistant Response
    ACTIVE --> ACTIVE: Update Issue
    ACTIVE --> CLOSED: Close Conversation
    
    CLOSED --> [*]
    
    note right of ACTIVE
        Maintains:
        - Conversation Summary
        - Current Issue
        - Active Evidence
        - Message History
    end note
```

### Data Model

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#06b6d4'}}}%%
erDiagram
    CONVERSATION {
        string conversation_id PK
        string user_id
        string status
        string summary
        json current_issue
        json active_evidence
        datetime created_at
        datetime updated_at
    }
    
    MESSAGE {
        string conversation_id FK
        string timestamp PK
        string role
        string content
        datetime created_at
    }
    
    CONVERSATION ||--o{ MESSAGE : contains
```

### DynamoDB Single-Table Design

| PK | SK | Attributes |
|----|----|------------|
| `CONVERSATION#{id}` | `METADATA` | status, summary, current_issue, active_evidence |
| `CONVERSATION#{id}` | `MESSAGE#{timestamp}` | role, content, created_at |

### Current Issue Management

The `current_issue` object tracks the ongoing support context:

```json
{
  "issue_summary": "503 error after deployment",
  "product": "api-gateway",
  "component": "authentication",
  "environment": "production",
  "error_code": "HTTP_503",
  "version": "2.1.0"
}
```

---

## 🛡️ Security & Guardrails

### Security Architecture

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ef4444'}}}%%
flowchart TB
    subgraph Input["🔒 Input Security"]
        IG["Input Guardrail"]
        PI["Prompt Injection\nDetection"]
        IV["Input\nValidation"]
    end
    
    subgraph Processing["⚙️ Secure Processing"]
        ES["Evidence\nSanitization"]
        PS["Prompt\nSafety"]
    end
    
    subgraph Output["🔐 Output Security"]
        OG["Output Guardrail"]
        OS["Output\nSanitization"]
    end
    
    User["👤 User Input"] --> IG
    IG --> PI
    PI --> IV
    IV --> Processing
    Processing --> ES
    ES --> PS
    PS --> OG
    OG --> OS
    OS --> Response["📤 Safe Response"]
    
    classDef securityStyle fill:#f87171,stroke:#dc2626,color:#fff
    classDef processStyle fill:#34d399,stroke:#059669,color:#fff
    
    class IG,PI,IV,OG,OS securityStyle
    class ES,PS processStyle
```

### Security Controls

| Layer | Control | Description |
|-------|---------|-------------|
| 🛡️ Input | Prompt Injection Detection | Blocks commands like "ignore all previous instructions" |
| 🛡️ Input | Pydantic Validation | Validates request schema and field constraints |
| ⚙️ Processing | Evidence Sanitization | Filters documents containing injection attempts |
| ⚙️ Processing | Untrusted Evidence Prompting | LLM instructed to treat KB content as untrusted |
| 🔐 Output | Response Sanitization | Validates and cleans generated responses |

### Blocked Patterns

- `reveal (the )?(system prompt|secrets)`
- `ignore all previous instructions`
- `ignore (all|previous)` (in documents)
- `reveal (the )?system prompt` (in documents)

---

## 🚀 Deployment Architecture

### AWS Infrastructure

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ff9900'}}}%%
flowchart TB
    subgraph Internet["🌐 Internet"]
        Users["👥 Users"]
    end
    
    subgraph AWS["☁️ AWS Cloud"]
        subgraph EB["Elastic Beanstalk"]
            LB["Application\nLoad Balancer"]
            EC2["EC2 Instance\n(Docker)"]
        end
        
        subgraph Compute["🖥️ Compute Services"]
            Ollama["Ollama Service\n(qwen2.5:3b)"]
        end
        
        subgraph AI["🧠 AI Services"]
            Bedrock["Amazon\nBedrock"]
            Nova["Nova Lite\n(LLM)"]
            KnowledgeBase["Bedrock\nKnowledge Base"]
        end
        
        subgraph Data["💾 Data Services"]
            DynamoDB[("DynamoDB")]
            S3[("S3\nKB Storage")]
        end
        
        subgraph Security["🔒 Security"]
            IAM["IAM Roles"]
        end
    end
    
    Users --> LB
    LB --> EC2
    EC2 --> Ollama
    EC2 --> Bedrock
    Bedrock --> Nova
    Bedrock --> KnowledgeBase
    KnowledgeBase --> S3
    EC2 --> DynamoDB
    EC2 -.-> IAM
    
    classDef ebStyle fill:#ff9900,stroke:#cc7700,color:#fff
    classDef aiStyle fill:#a78bfa,stroke:#7c3aed,color:#fff
    classDef dataStyle fill:#34d399,stroke:#059669,color:#fff
    classDef secStyle fill:#f87171,stroke:#dc2626,color:#fff
    
    class LB,EC2,Ollama ebStyle
    class Bedrock,Nova,KnowledgeBase aiStyle
    class DynamoDB,S3 dataStyle
    class IAM secStyle
```

### Container Architecture

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#2563eb'}}}%%
flowchart LR
    subgraph Docker["🐳 Docker Container"]
        Python["Python 3.12"]
        FastAPI["FastAPI"]
        Uvicorn["Uvicorn\n:8000"]
    end
    
    subgraph EB["Elastic Beanstalk"]
        ALB["ALB\n:80"]
        Nginx["Nginx Proxy"]
    end
    
    ALB --> Nginx
    Nginx --> Uvicorn
    Uvicorn --> FastAPI
    FastAPI --> Python
```

### Required IAM Permissions

| Service | Actions | Resource |
|---------|---------|----------|
| Bedrock Runtime | `bedrock:InvokeModel`, `bedrock:Converse` | `*` |
| Bedrock Agent Runtime | `bedrock:Retrieve` | Knowledge Base ARN |
| DynamoDB | `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:Query` | Conversation Table |

---

## 📡 API Reference

### Endpoints

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#3b82f6'}}}%%
flowchart LR
    subgraph Endpoints["📡 API Endpoints"]
        E1["POST /api/v1/assistant/chat"]
        E2["GET /api/v1/conversations/{id}"]
        E3["GET /api/v1/conversations/{id}/messages"]
        E4["POST /api/v1/conversations/{id}/close"]
        E5["GET /health"]
    end
    
    classDef endpointStyle fill:#60a5fa,stroke:#2563eb,color:#fff
    class E1,E2,E3,E4,E5 endpointStyle
```

### Chat Endpoint

**POST** `/api/v1/assistant/chat`

#### Request Body

```json
{
  "conversation_id": "conv-12345",
  "user": {
    "user_id": "user-001",
    "name": "John Doe"
  },
  "message": "How do I resolve a 503 error after deployment?",
  "context": {
    "product": "api-gateway",
    "component": "authentication",
    "environment": "production"
  }
}
```

#### Response Body

```json
{
  "conversation_id": "conv-12345",
  "request_id": "REQ-abc123def456",
  "answer": "A 503 error after deployment typically indicates that the service is temporarily unavailable. Here are the recommended steps to resolve this...",
  "confidence": 0.87,
  "citations": [
    {
      "source_id": "DOC-001",
      "source_type": "product_document",
      "title": "Troubleshooting Deployment Errors",
      "relevance_score": 0.92
    }
  ],
  "metadata": {
    "query_type": "NEW_ISSUE",
    "retrieval_performed": true,
    "documents_retrieved": 25,
    "documents_reranked": 8,
    "documents_used": 3
  }
}
```

### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conversation_id` | string | Yes | Unique conversation identifier |
| `user.user_id` | string | Yes | User identifier |
| `user.name` | string | No | Display name |
| `message` | string | Yes | User message (1-8000 chars) |
| `context.product` | string | No | Product filter |
| `context.component` | string | No | Component filter |
| `context.environment` | string | No | Environment filter |

### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | string | Conversation identifier |
| `request_id` | string | Unique request tracking ID |
| `answer` | string | Generated response |
| `confidence` | float | Confidence score (0-1) |
| `citations` | array | Source citations |
| `metadata` | object | Processing metadata |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPPORT_ASSISTANT_ENVIRONMENT` | Deployment environment | `dev` |
| `SUPPORT_ASSISTANT_AWS_REGION` | AWS region | `us-east-1` |
| `SUPPORT_ASSISTANT_KNOWLEDGE_BASE_ID` | Bedrock Knowledge Base ID | - |
| `SUPPORT_ASSISTANT_KNOWLEDGE_BASE_RETRIEVAL_MODE` | KB retrieval mode (`managed`/`vector`) | `managed` |
| `SUPPORT_ASSISTANT_ANSWER_MODEL_ID` | LLM model ID for answers | - |
| `SUPPORT_ASSISTANT_CONVERSATION_TABLE_NAME` | DynamoDB table name | - |
| `SUPPORT_ASSISTANT_QUERY_UNDERSTANDING_LOCAL_MODEL` | Ollama model name | - |
| `SUPPORT_ASSISTANT_QUERY_UNDERSTANDING_OLLAMA_URL` | Ollama service URL | `http://localhost:11434` |
| `SUPPORT_ASSISTANT_QUERY_UNDERSTANDING_CLOUD_FALLBACK_ENABLED` | Enable Bedrock fallback | `false` |
| `SUPPORT_ASSISTANT_QUERY_UNDERSTANDING_MINIMUM_CONFIDENCE` | Minimum confidence threshold | `0.8` |
| `SUPPORT_ASSISTANT_QUERY_UNDERSTANDING_TIMEOUT_SECONDS` | LLM timeout | `60` |
| `SUPPORT_ASSISTANT_RETRIEVAL_TOP_K` | Initial retrieval count | `25` |
| `SUPPORT_ASSISTANT_RERANKING_ENABLED` | Enable reranking | `true` |
| `SUPPORT_ASSISTANT_RERANKING_TOP_K` | Post-rerank count | `8` |
| `SUPPORT_ASSISTANT_EVIDENCE_MINIMUM_SCORE` | Minimum evidence score | `0.72` |
| `SUPPORT_ASSISTANT_EVIDENCE_MINIMUM_SOURCES` | Minimum sources required | `1` |
| `SUPPORT_ASSISTANT_EVIDENCE_FINAL_TOP_K` | Final evidence count | `5` |
| `SUPPORT_ASSISTANT_CONVERSATION_RECENT_MESSAGES` | Recent message context | `4` |
| `SUPPORT_ASSISTANT_LLM_TEMPERATURE` | LLM temperature | `0.1` |
| `SUPPORT_ASSISTANT_LLM_MAX_OUTPUT_TOKENS` | Max output tokens | `800` |

---

## 🔧 Technology Stack

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#6366f1'}}}%%
mindmap
  root((Support<br/>Assistant))
    Framework
      FastAPI
      LangGraph
      Pydantic
      Uvicorn
    AI/ML
      Amazon Bedrock
      Nova Lite LLM
      Ollama
      qwen2.5:3b
    AWS Services
      Elastic Beanstalk
      DynamoDB
      S3
      IAM
    Infrastructure
      Docker
      Python 3.12
      boto3
```

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `langgraph` | Workflow orchestration |
| `pydantic` | Data validation |
| `pydantic-settings` | Configuration management |
| `boto3` | AWS SDK |
| `uvicorn` | ASGI server |

---

## 📈 Performance Characteristics

| Metric | Target | Description |
|--------|--------|-------------|
| **Latency (P50)** | < 2s | Typical response time |
| **Latency (P99)** | < 5s | With full retrieval pipeline |
| **Retrieval Limit** | 25 docs | Initial KB retrieval |
| **Rerank Limit** | 8 docs | Post-reranking |
| **Final Evidence** | 5 docs | Used in answer generation |
| **Context Window** | 4 messages | Recent conversation history |
| **Max Message Size** | 8000 chars | Input message limit |
| **Max Output Tokens** | 800 | LLM response limit |

---

## 🎨 Design Principles

1. **Deterministic First** - Use pattern matching before AI for predictable, fast behavior
2. **Graceful Degradation** - Local LLM → Cloud LLM → Deterministic fallback chain
3. **Evidence-Based** - All answers must be grounded in retrieved knowledge
4. **Security by Default** - Treat all external content as untrusted
5. **Observable** - Comprehensive structured logging at every pipeline stage
6. **Configurable** - Environment-based configuration for all thresholds
7. **Stateful Conversations** - Maintain context across multi-turn interactions
8. **Separation of Concerns** - Request context for filtering, stored issue for memory

---

## 🔍 Observability

### Structured Logging Events

| Event | Description |
|-------|-------------|
| `assistant_workflow_started` | Workflow invocation begins |
| `conversation_loaded` | Conversation state retrieved |
| `input_guardrail_allowed` | Input validation passed |
| `query_understanding_completed` | Query analysis finished |
| `knowledge_base_retrieval_request` | KB query initiated |
| `knowledge_base_retrieval_completed` | KB results received |
| `knowledge_base_results_reranked` | Reranking completed |
| `knowledge_base_results_validated` | Evidence validation done |
| `llm_generation_started` | Answer generation begins |
| `llm_generation_completed` | Answer generated |
| `conversation_updated` | State persisted |
| `assistant_workflow_completed` | Full pipeline finished |

### Log Fields

Every log event includes:
- `request_id` - Unique request identifier
- `conversation_id` - Conversation identifier
- `timestamp` - Event timestamp

---

## 📚 Related Documentation

- [README.md](README.md) - Quick start guide
- [Dockerfile](Dockerfile) - Container configuration
- [pyproject.toml](pyproject.toml) - Project metadata

---

*Documentation generated for Support Assistant Service v0.1.0*
