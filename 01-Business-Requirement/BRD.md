# Business Requirement Document (BRD)
## Enterprise Asset Integrity Management System (AIMS)

| Field | Value |
|---|---|
| Document Type | Business Requirement Document |
| Version | 1.0 |
| Status | Draft |
| Date | 2026-08-06 |
| Classification | Internal |

---

## 1. Executive Summary

The Enterprise Asset Integrity Management System (AIMS) is a web-based enterprise application designed to
digitize and standardize asset integrity, inspection, and reliability management across capital-intensive,
high-hazard industries (Oil & Gas, Petrochemical, Power Generation, Chemical Processing, Manufacturing,
Mining, and Heavy Industry).

AIMS consolidates asset registers, inspection planning and execution, Risk Based Inspection (RBI),
corrosion and thickness monitoring, defect and fitness-for-service management, condition monitoring, and
document control into a single system of record — aligned with **ISO 55000/55001**, **API 510/570/580/581/653/579**,
**IEC 61511**, and **ISO 14224**. An AI Asset Integrity Copilot layer provides natural-language insight
into risk, compliance, and predictive failure across the asset base.

The system replaces fragmented spreadsheets, paper inspection records, and siloed point-solutions with a
single auditable platform that reduces unplanned downtime, ensures regulatory/inspection compliance, and
extends asset remaining life through data-driven decision making.

---

## 2. Business Objective

| # | Objective | Description |
|---|---|---|
| BO-1 | Centralize Asset Data | Single source of truth for the full asset hierarchy (Plant → Area → Unit → Equipment → Component → Inspection Point) |
| BO-2 | Ensure Inspection Compliance | Guarantee inspections are planned, executed, and closed within regulatory/code-mandated intervals |
| BO-3 | Reduce Unplanned Downtime | Use RBI and predictive analytics to shift from reactive to risk-based, condition-based maintenance |
| BO-4 | Extend Asset Life | Track corrosion rate and remaining life to optimize repair/replace decisions |
| BO-5 | Strengthen Process Safety | Provide defensible fitness-for-service and risk data to prevent loss-of-containment events |
| BO-6 | Enable Data-Driven Decisions | Deliver executive, engineering, and inspection dashboards with real-time KPIs |
| BO-7 | Reduce Audit Burden | Maintain a full, immutable audit trail for internal, regulatory, and insurance audits |
| BO-8 | Accelerate Expertise Access | AI Copilot democratizes reliability/inspection knowledge across the organization |

---

## 3. Stakeholder Analysis

| Stakeholder | Role in System | Key Concerns | Primary Modules Used |
|---|---|---|---|
| **Asset Owner** | Accountable for asset performance & capital decisions | Asset value, risk exposure, ROI on integrity spend | Dashboard, Asset Register, Risk Assessment |
| **Plant Manager** | Operational accountability for the facility | Availability, safety incidents, production impact of inspection/maintenance | Executive Dashboard, Maintenance Order, Asset Register |
| **Maintenance Manager** | Owns repair/maintenance execution | Work order backlog, resource planning, repair verification | Defect Management, Maintenance Order, Document Management |
| **Reliability Engineer** | Owns RBI methodology & reliability analysis | POF/COF accuracy, inspection interval optimization, failure trend analysis | RBI, Corrosion Management, Condition Monitoring, AI Copilot |
| **Inspector** | Executes field inspections | Mobile access, checklist usability, finding capture, offline capability | Inspection Management, Defect Management, Document Management |
| **Safety Engineer** | Process safety & HSE compliance | Fitness-for-service, risk matrix accuracy, incident prevention | Risk Based Inspection, Defect Management, Audit Log |
| **Management / Executive** | Strategic oversight & governance | High-level KPIs, compliance status, capital risk | Executive Dashboard, AI Copilot |
| **System Administrator** | IT ownership of the platform | Security, uptime, integration, user/role administration | Identity & Access Management, Audit Log |

---

## 4. Business Requirement

| ID | Requirement |
|---|---|
| BR-01 | The system shall maintain a hierarchical asset register (Plant/Area/Unit/Equipment/Component/Inspection Point) |
| BR-02 | The system shall support the full asset lifecycle: Design → Construction → Commissioning → Operation → Inspection → Maintenance → Repair → Modification → Decommission |
| BR-03 | The system shall calculate risk (POF × COF) per API 580/581 methodology and generate risk-ranked inspection plans |
| BR-04 | The system shall track thickness readings and calculate corrosion rate and remaining life per API 570/653/579 |
| BR-05 | The system shall manage the full defect lifecycle from finding to close, with approval workflow |
| BR-06 | The system shall ingest and display condition monitoring data (temperature, pressure, vibration, flow) from IoT sources |
| BR-07 | The system shall provide role-based dashboards for executives, engineers, and inspectors |
| BR-08 | The system shall store and version-control engineering documents (P&ID, drawings, certificates, reports) |
| BR-09 | The system shall provide an AI Copilot capable of answering natural-language questions on risk, inspection status, and failure prediction |
| BR-10 | The system shall maintain a complete, tamper-evident audit trail of all data changes |
| BR-11 | The system shall enforce role-based access control (RBAC) aligned to organizational structure |
| BR-12 | The system shall be usable on mobile/tablet devices for field inspection data capture |

---

## 5. Functional Requirement

### 5.1 Identity & Access Management
- FR-01: Manage users, roles, permissions, and organizational structure
- FR-02: Support SSO/OAuth2 authentication and JWT-based session management
- FR-03: Log all authentication and authorization events

### 5.2 Asset Management
- FR-04: Create/read/update/retire assets with full hierarchy (Plant→Component)
- FR-05: Classify assets by type, criticality, and service
- FR-06: Assign and recalculate criticality rating based on defined criteria
- FR-07: Manage asset location/GPS/geo-tagging

### 5.3 Inspection Management
- FR-08: Create inspection plans linked to asset/component and applicable code
- FR-09: Schedule inspections and assign inspectors
- FR-10: Execute digital checklists (desktop & mobile/offline)
- FR-11: Capture findings with photo/attachment evidence
- FR-12: Generate recommendations linked to findings

### 5.4 Risk Based Inspection (RBI)
- FR-13: Calculate Probability of Failure (POF) and Consequence of Failure (COF)
- FR-14: Generate risk matrix (5x5 or configurable) and risk score
- FR-15: Recommend/optimize next inspection interval based on risk score
- FR-16: Support qualitative, semi-quantitative, and quantitative RBI (API 581)

### 5.5 Corrosion Management
- FR-17: Record thickness measurements per inspection point (CML)
- FR-18: Calculate short-term/long-term corrosion rate
- FR-19: Calculate remaining life and next inspection due date
- FR-20: Provide trend analysis and corrosion rate charting

### 5.6 Defect Management
- FR-21: Manage defect workflow: Finding → Assessment → Approval → Repair → Verification → Close
- FR-22: Link defects to Fitness-For-Service (FFS) assessments per API 579
- FR-23: Track defect severity, priority, and SLA

### 5.7 Condition Monitoring
- FR-24: Ingest sensor data (temperature, pressure, vibration, flow) via MQTT/OPC-UA/Modbus TCP
- FR-25: Trigger threshold-based alerts
- FR-26: Store and visualize time-series sensor data

### 5.8 Document Management
- FR-27: Store, version, and retrieve P&IDs, drawings, certificates, inspection reports
- FR-28: Link documents to asset/equipment/inspection records

### 5.9 Dashboard & Reporting
- FR-29: Provide Executive, Engineering, and Inspection dashboards
- FR-30: Generate scheduled and on-demand reports (PDF/Excel export)

### 5.10 AI Copilot
- FR-31: Answer natural-language queries against asset/risk/inspection data (RAG-based)
- FR-32: Generate inspection report drafts
- FR-33: Provide predictive failure insights based on historical + sensor data

---

## 6. Non-Functional Requirement

| Category | ID | Requirement |
|---|---|---|
| Performance | NFR-01 | Page load ≤ 2s (P95) for standard views; dashboard queries ≤ 3s (P95) |
| Scalability | NFR-02 | Support 10,000+ assets, 100+ concurrent users, horizontally scalable via Kubernetes |
| Availability | NFR-03 | 99.5% uptime SLA for production environment |
| Security | NFR-04 | OAuth2/JWT authentication, RBAC authorization, encryption at rest and in transit (TLS 1.2+) |
| Auditability | NFR-05 | Immutable audit log for all create/update/delete operations, retained ≥ 7 years |
| Usability | NFR-06 | Responsive design (desktop/tablet/mobile), WCAG 2.1 AA accessibility target |
| Data Integrity | NFR-07 | Referential integrity enforced at database level; no orphaned records |
| Interoperability | NFR-08 | REST API with OpenAPI 3.0 spec; support MQTT/OPC-UA/Modbus TCP ingestion |
| Maintainability | NFR-09 | Clean Architecture / modular codebase; ≥80% automated test coverage |
| Deployability | NFR-10 | Containerized (Docker), Kubernetes-ready, CI/CD pipeline with automated build/test/deploy |
| Data Retention | NFR-11 | Inspection and corrosion records retained per API/regulatory minimums (typically ≥ equipment life + 5 years) |
| Localization | NFR-12 | Support multi-language UI (Thai/English) and multi-timezone data display |

---

## 7. Key Performance Indicators (KPI)

| KPI | Definition | Target |
|---|---|---|
| Asset Availability | (Total time − Downtime) / Total time | ≥ 95% |
| Inspection Compliance | Inspections completed on/before due date / Total scheduled | ≥ 98% |
| Risk Reduction | % reduction in high/very-high risk-ranked equipment YoY | ≥ 10% YoY |
| Corrosion Rate | Average measured corrosion rate vs. design corrosion allowance | Within design allowance |
| Remaining Life | Average remaining life across critical equipment | > 5 years (flag if lower) |
| Failure Rate | Unplanned failures / total equipment count per year | Decreasing trend |
| Defect Closure SLA | Defects closed within target SLA / total defects | ≥ 90% |
| Overdue Inspections | Count of inspections past due date | 0 (target) |
| Audit Findings | Number of non-conformances raised in internal/external audits | Decreasing trend |

---

## 8. Assumptions & Constraints

- Users have existing corporate identity infrastructure that can federate via OAuth2/SSO.
- Field inspectors require offline-capable data capture with later sync.
- IoT/sensor infrastructure (MQTT/OPC-UA/Modbus gateways) exists or will be provisioned separately from this application.
- Initial deployment targets a single organization with multiple plants (multi-tenant architecture considered for future phase).
- Regulatory code editions (API 510/570/580/581/653/579) are configurable per asset to accommodate jurisdiction/version differences.

## 9. Out of Scope (Phase 1)

- Financial/ERP integration (CMMS/ERP integration is a future-phase interface, not core scope)
- Full multi-tenant SaaS billing/subscription management
- Native mobile app store distribution (Phase 1 targets responsive web/PWA)

---

*Next document: [Architecture.md](../02-System-Architecture/Architecture.md)*
