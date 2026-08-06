# Data Flow Diagram (DFD)
## Enterprise Asset Integrity Management System (AIMS)

Notation: Rounded rectangles = Process · Rectangles = External Entity · Cylinders = Data Store

---

## Level 0 — Context Diagram

```mermaid
flowchart TB
    ENG([Reliability / Asset Engineer])
    INSP([Inspector])
    MGR([Manager / Executive])
    IOT[/IoT Sensor Platform/]
    LLM[/LLM Provider/]

    AIMS(("0.0<br/>AIMS<br/>Asset Integrity<br/>Management System"))

    ENG -- "Asset data, Risk parameters" --> AIMS
    INSP -- "Inspection results, Findings" --> AIMS
    MGR -- "Report requests, Approvals" --> AIMS
    IOT -- "Sensor readings" --> AIMS

    AIMS -- "Dashboards, Alerts, Reports" --> ENG
    AIMS -- "Inspection plans, Schedules" --> INSP
    AIMS -- "KPI dashboards, Compliance status" --> MGR
    AIMS -- "Query" --> LLM
    LLM -- "AI-generated insight" --> AIMS
```

---

## Level 1 — System Process Flow

```mermaid
flowchart TB
    ENG([Asset Engineer])
    INSP([Inspector])
    MGR([Manager])
    IOT[/IoT Platform/]

    P1("1.0<br/>Asset Registration")
    P2("2.0<br/>Inspection")
    P3("3.0<br/>Risk Calculation")
    P4("4.0<br/>Maintenance")
    P5("5.0<br/>Reporting")

    DS1[(D1 Asset Register)]
    DS2[(D2 Inspection Data)]
    DS3[(D3 Risk / Corrosion Data)]
    DS4[(D4 Defect / Maintenance Data)]
    DS5[(D5 Sensor Data)]
    DS6[(D6 Document Store)]
    DS7[(D7 Audit Log)]

    ENG -- "Asset details" --> P1
    P1 -- "Store asset" --> DS1
    DS1 -- "Asset hierarchy" --> P2
    DS1 -- "Asset hierarchy" --> P3

    INSP -- "Inspection execution, findings" --> P2
    P2 -- "Store results/findings" --> DS2
    DS2 -- "Findings, thickness data" --> P3

    IOT -- "Sensor streams" --> DS5
    DS5 -- "Condition data" --> P3

    P3 -- "POF/COF/Risk score, corrosion rate" --> DS3
    DS3 -- "Risk-ranked equipment, defects" --> P4
    P2 -- "Findings requiring action" --> P4
    P4 -- "Work order / repair record" --> DS4

    DS1 & DS2 & DS3 & DS4 & DS5 --> P5
    P5 -- "Dashboards / KPI reports" --> MGR
    P5 -- "Compliance status" --> ENG

    P1 & P2 & P3 & P4 -- "Change events" --> DS7
    P1 & P2 -- "Attachments" --> DS6
```

---

## Level 2 — Detail Process Breakdown

### 2.1 Process 1.0 — Asset Registration

```mermaid
flowchart TB
    ENG([Asset Engineer])
    P1_1("1.1 Define Location<br/>(Plant/Area/Unit)")
    P1_2("1.2 Register Asset<br/>(Equipment)")
    P1_3("1.3 Decompose into<br/>Component/Inspection Point")
    P1_4("1.4 Assess Criticality")

    DS1[(D1 Asset Register)]
    DS_LOC[(Location)]
    DS_CRIT[(Criticality)]

    ENG --> P1_1 --> DS_LOC
    ENG --> P1_2
    DS_LOC --> P1_2 --> DS1
    DS1 --> P1_3 --> DS1
    DS1 --> P1_4 --> DS_CRIT
    DS_CRIT -- "current rating" --> DS1
```

### 2.2 Process 2.0 — Inspection

```mermaid
flowchart TB
    ENG([Asset Engineer])
    INSP([Inspector])
    P2_1("2.1 Create Inspection Plan")
    P2_2("2.2 Schedule & Assign Inspector")
    P2_3("2.3 Execute Checklist<br/>(field/mobile, offline capable)")
    P2_4("2.4 Capture Finding")
    P2_5("2.5 Record Thickness Reading")

    DS1[(D1 Asset Register)]
    DS_PLAN[(Inspection Plan)]
    DS2[(D2 Inspection Data)]
    DS_FIND[(Finding)]
    DS_THICK[(Thickness Record)]
    DS6[(D6 Document Store)]

    DS1 --> P2_1 --> DS_PLAN
    ENG --> P2_1
    DS_PLAN --> P2_2 --> DS2
    INSP --> P2_2
    DS2 --> P2_3
    P2_3 --> DS2
    P2_3 -- "photo/attachment" --> DS6
    P2_3 --> P2_4 --> DS_FIND
    P2_3 --> P2_5 --> DS_THICK
```

### 2.3 Process 3.0 — Risk Calculation

```mermaid
flowchart TB
    DS_FIND[(Finding)]
    DS_THICK[(Thickness Record)]
    DS1[(D1 Asset Register)]
    DS_SENSOR[(Sensor Data)]

    P3_1("3.1 Calculate Corrosion Rate<br/>& Remaining Life")
    P3_2("3.2 Calculate POF")
    P3_3("3.3 Calculate COF")
    P3_4("3.4 Compute Risk Score & Rank")
    P3_5("3.5 Recommend Inspection Interval")

    DS_CORR[(Corrosion Record)]
    DS_RISK[(Risk Assessment)]
    DS_PLAN[(Inspection Plan)]

    DS_THICK --> P3_1 --> DS_CORR
    DS_CORR --> P3_2
    DS1 --> P3_2
    DS_SENSOR --> P3_2
    DS1 --> P3_3
    P3_2 --> P3_4
    P3_3 --> P3_4 --> DS_RISK
    DS_RISK --> P3_5 --> DS_PLAN
```

### 2.4 Process 4.0 — Maintenance

```mermaid
flowchart TB
    DS_FIND[(Finding)]
    DS_RISK[(Risk Assessment)]
    MGR([Manager])
    MAINT([Maintenance Team])

    P4_1("4.1 Assess Defect &<br/>Determine FFS Need")
    P4_2("4.2 Approve Repair Plan")
    P4_3("4.3 Execute Repair /<br/>Maintenance Order")
    P4_4("4.4 Verify & Close")

    DS_DEFECT[(Defect)]
    DS_MO[(Maintenance Order)]

    DS_FIND --> P4_1
    DS_RISK --> P4_1 --> DS_DEFECT
    DS_DEFECT --> P4_2
    MGR --> P4_2 --> DS_DEFECT
    DS_DEFECT --> P4_3
    MAINT --> P4_3 --> DS_MO
    DS_MO --> P4_4 --> DS_DEFECT
```

### 2.5 Process 5.0 — Reporting

```mermaid
flowchart TB
    DS1[(D1 Asset Register)]
    DS2[(D2 Inspection Data)]
    DS3[(D3 Risk/Corrosion Data)]
    DS4[(D4 Defect/Maintenance Data)]

    P5_1("5.1 Aggregate KPIs")
    P5_2("5.2 Generate Dashboard View")
    P5_3("5.3 Export Report<br/>(PDF/Excel)")
    P5_4("5.4 AI Copilot Query<br/>(RAG over all data)")

    MGR([Manager])
    ENG([Engineer])

    DS1 & DS2 & DS3 & DS4 --> P5_1 --> P5_2
    P5_2 --> MGR
    P5_2 --> ENG
    P5_2 --> P5_3
    DS1 & DS2 & DS3 & DS4 --> P5_4
    P5_4 -- "natural language answer" --> ENG
    P5_4 -- "natural language answer" --> MGR
```

---

*Related: [ERD.md](../03-Database-Design/ERD.md) · Next: [Swimlane.md](Swimlane.md)*
