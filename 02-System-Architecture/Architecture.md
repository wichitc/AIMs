# System Architecture Design
## Enterprise Asset Integrity Management System (AIMS)

| Field | Value |
|---|---|
| Version | 1.0 |
| Status | Draft |
| Date | 2026-08-06 |

---

## 1. Technology Stack Decision

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | Next.js (React, TypeScript), TailwindCSS, shadcn/ui | SSR/SSG for dashboards, strong TS ecosystem, accessible component primitives |
| Backend (Core API) | **FastAPI (Python)** | Native fit with AI/ML/RAG services, async I/O, automatic OpenAPI generation, strong typing via Pydantic |
| Database | PostgreSQL | ACID compliance, mature RBAC/row-level security, JSONB for flexible attributes |
| Time-Series | TimescaleDB (PostgreSQL extension) | Native SQL for sensor/thickness time-series without a separate DB engine |
| Cache/Queue | Redis | Session cache, rate limiting, Celery/task queue broker |
| AI Service | Python (FastAPI microservice), LangChain/LlamaIndex-style RAG, LLM API integration | Isolates AI workload, independent scaling, model-agnostic |
| IoT Ingestion | MQTT broker (Mosquitto/EMQX), OPC-UA client, Modbus TCP gateway | Industry-standard industrial protocols |
| Deployment | Docker, Docker Compose (dev), Kubernetes (prod-ready) | Portable, horizontally scalable |
| Security | OAuth2, JWT, RBAC, Audit Trail | Enterprise SSO compatibility, fine-grained authorization |

> Decision note: FastAPI is chosen over NestJS because the AI Copilot, RBI probabilistic calculations, and
> corrosion-rate/statistical analysis are naturally Python-native workloads; using one language across
> Core API and AI Service reduces cross-team handoff and duplicate data models.

---

## 2. High Level Architecture

```mermaid
flowchart TB
    subgraph Users["Users"]
        U1[Asset Owner / Management]
        U2[Reliability Engineer]
        U3[Inspector - Mobile/Field]
        U4[Maintenance Manager]
    end

    subgraph Frontend["Frontend Layer"]
        FE[Next.js / React / TypeScript<br/>TailwindCSS + shadcn/ui]
    end

    subgraph Gateway["API Gateway"]
        GW[API Gateway / Reverse Proxy<br/>Auth, Rate Limit, Routing]
    end

    subgraph Backend["Backend Services"]
        API[Core API Service<br/>FastAPI - Clean Architecture]
        AI[AI Engine Service<br/>Python - RAG / LLM / ML Pipeline]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL<br/>Transactional Data)]
        TS[(TimescaleDB<br/>Sensor / Thickness Time-Series)]
        RD[(Redis<br/>Cache / Queue)]
        VEC[(Vector Store<br/>RAG Knowledge Base)]
    end

    subgraph IoT["IoT Platform"]
        MQTT[MQTT Broker]
        OPC[OPC-UA Client]
        MOD[Modbus TCP Gateway]
        SENSORS[Field Sensors<br/>Temp / Pressure / Vibration / Flow]
    end

    U1 --> FE
    U2 --> FE
    U3 --> FE
    U4 --> FE

    FE --> GW
    GW --> API
    GW --> AI

    API --> PG
    API --> RD
    API --> TS
    AI --> VEC
    AI --> PG
    AI --> API

    SENSORS --> MQTT
    SENSORS --> OPC
    SENSORS --> MOD
    MQTT --> API
    OPC --> API
    MOD --> API
    API --> TS

    classDef userClass fill:#e1f0ff,stroke:#4a90d9
    classDef svcClass fill:#fff4e1,stroke:#d9a54a
    classDef dataClass fill:#e8f5e9,stroke:#4caf50
    class U1,U2,U3,U4 userClass
    class FE,GW,API,AI svcClass
    class PG,TS,RD,VEC dataClass
```

---

## 3. C4 Model

### 3.1 Level 1 — System Context

```mermaid
flowchart TB
    Owner((Asset Owner))
    PM((Plant Manager))
    MM((Maintenance Manager))
    RE((Reliability Engineer))
    INS((Inspector))
    SE((Safety Engineer))
    MGT((Management))

    AIMS[["AIMS<br/>Enterprise Asset Integrity<br/>Management System"]]

    IOT[IoT Sensor Platform<br/>external]
    DOC[Document / File Storage<br/>external]
    IDP[Corporate Identity Provider<br/>OAuth2/SSO - external]
    LLM[LLM Provider<br/>external]
    CMMS[CMMS/ERP<br/>future integration - external]

    Owner --> AIMS
    PM --> AIMS
    MM --> AIMS
    RE --> AIMS
    INS --> AIMS
    SE --> AIMS
    MGT --> AIMS

    AIMS --> IOT
    AIMS --> DOC
    AIMS --> IDP
    AIMS --> LLM
    AIMS -.future.-> CMMS
```

### 3.2 Level 2 — Container Diagram

```mermaid
flowchart TB
    subgraph AIMS["AIMS System Boundary"]
        WebApp[Web Application<br/>Next.js/React/TS]
        Gateway[API Gateway<br/>Auth / Routing / Rate Limit]
        CoreAPI[Core API<br/>FastAPI - Python]
        AIEngine[AI Engine<br/>FastAPI - RAG/ML Service]
        Worker[Background Worker<br/>Celery - Python]
        DB[(PostgreSQL)]
        TSDB[(TimescaleDB)]
        Cache[(Redis)]
        VectorDB[(Vector Store)]
        ObjStore[(Object Storage<br/>Documents/Attachments)]
    end

    Broker[MQTT / OPC-UA / Modbus Gateway]
    IDP[Identity Provider]
    LLM[LLM Provider API]

    User((User Browser/Mobile)) --> WebApp
    WebApp --> Gateway
    Gateway --> CoreAPI
    Gateway --> AIEngine
    Gateway --> IDP

    CoreAPI --> DB
    CoreAPI --> Cache
    CoreAPI --> TSDB
    CoreAPI --> ObjStore
    CoreAPI --> Worker
    Worker --> DB
    Worker --> Cache

    AIEngine --> VectorDB
    AIEngine --> DB
    AIEngine --> LLM
    AIEngine --> CoreAPI

    Broker --> CoreAPI
```

### 3.3 Level 3 — Component Diagram (Core API)

```mermaid
flowchart TB
    subgraph CoreAPI["Core API - FastAPI (Clean Architecture)"]
        direction TB
        subgraph API_Layer["API Layer"]
            R1[Asset Router]
            R2[Inspection Router]
            R3[RBI Router]
            R4[Corrosion Router]
            R5[Defect Router]
            R6[Document Router]
            R7[Auth Router]
        end

        subgraph Service_Layer["Service Layer"]
            S1[Asset Service]
            S2[Inspection Service]
            S3[RBI Calculation Service]
            S4[Corrosion Calculation Service]
            S5[Defect Workflow Service]
            S6[Document Service]
            S7[Auth/RBAC Service]
        end

        subgraph Repository_Layer["Repository Layer"]
            RP1[Asset Repository]
            RP2[Inspection Repository]
            RP3[Risk Repository]
            RP4[Corrosion Repository]
            RP5[Defect Repository]
            RP6[Document Repository]
            RP7[User/Role Repository]
        end

        subgraph Cross["Cross-Cutting"]
            MW1[Auth Middleware]
            MW2[Audit Log Middleware]
            MW3[Validation - Pydantic]
            MW4[Exception Handler]
        end
    end

    DB[(PostgreSQL)]

    R1 --> S1 --> RP1 --> DB
    R2 --> S2 --> RP2 --> DB
    R3 --> S3 --> RP3 --> DB
    R4 --> S4 --> RP4 --> DB
    R5 --> S5 --> RP5 --> DB
    R6 --> S6 --> RP6 --> DB
    R7 --> S7 --> RP7 --> DB

    API_Layer --> Cross
```

---

## 4. Deployment Topology (Kubernetes-Ready)

```mermaid
flowchart LR
    subgraph Ingress
        LB[Load Balancer / Ingress]
    end
    subgraph K8s["Kubernetes Cluster"]
        FEPod[Frontend Pods x N]
        APIPod[Core API Pods x N]
        AIPod[AI Engine Pods x N]
        WorkerPod[Worker Pods x N]
    end
    subgraph Managed["Managed / Stateful Services"]
        PGSvc[(PostgreSQL - Primary/Replica)]
        TSSvc[(TimescaleDB)]
        RedisSvc[(Redis)]
        ObjSvc[(Object Storage)]
    end

    LB --> FEPod
    LB --> APIPod
    LB --> AIPod
    APIPod --> PGSvc
    APIPod --> TSSvc
    APIPod --> RedisSvc
    APIPod --> ObjSvc
    WorkerPod --> PGSvc
    WorkerPod --> RedisSvc
    AIPod --> PGSvc
```

---

## 5. Architecture Principles

1. **Clean Architecture** — Core API separates API/Service/Repository/Domain layers; business logic is framework-independent.
2. **Domain-Driven Modules** — Each business module (Asset, Inspection, RBI, Corrosion, Defect, Document) is a bounded context with its own service/repository set.
3. **Stateless Services** — Core API and AI Engine are stateless and horizontally scalable; state lives in PostgreSQL/TimescaleDB/Redis.
4. **API-First** — All functionality exposed via versioned REST API (OpenAPI 3.0), enabling web, mobile, and third-party integration.
5. **Security by Design** — OAuth2/JWT at the gateway, RBAC enforced at the service layer, audit logging at the data layer.
6. **AI as a Separate Service** — The AI Engine is isolated from the Core API so LLM/RAG workloads scale and fail independently of transactional operations.

---

*Related documents: [BRD.md](../01-Business-Requirement/BRD.md) · Next: [Database.md](../03-Database-Design/Database.md)*
