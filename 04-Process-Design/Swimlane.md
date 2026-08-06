# Business Process Design — Swimlane Diagrams
## Enterprise Asset Integrity Management System (AIMS)

Actors: **Asset Engineer**, **Inspector**, **Maintenance**, **Manager**, **System**

---

## 1. Inspection Workflow

```mermaid
flowchart TB
    subgraph L1["Asset Engineer"]
        A1[Create Inspection Plan]
        A2[Assign Inspector]
    end
    subgraph L2["System"]
        S1[Notify Inspector]
        S2[Validate Checklist Completion]
        S3{Findings Raised?}
        S4[Auto-create Finding Record]
        S5[Update Inspection Status = Completed]
    end
    subgraph L3["Inspector"]
        I1[Receive Assignment]
        I2[Execute Checklist in Field<br/>desktop/mobile, offline-capable]
        I3[Record Thickness Readings]
        I4[Capture Finding + Photo Evidence]
        I5[Submit Inspection]
    end

    A1 --> A2 --> S1 --> I1 --> I2 --> I3
    I2 --> I4
    I4 --> S3
    S3 -- Yes --> S4
    S3 -- No --> S5
    S4 --> S5
    I3 --> I5 --> S2 --> S3
    S5 --> A_END[Asset Engineer notified of completion]
```

---

## 2. Risk Assessment Workflow

```mermaid
flowchart TB
    subgraph L1["System"]
        S1[Aggregate Thickness/Finding Data]
        S2[Calculate Corrosion Rate & Remaining Life]
        S3[Calculate POF]
        S4[Calculate COF]
        S5[Compute Risk Score & Rank]
        S6[Recommend Inspection Interval]
    end
    subgraph L2["Reliability / Asset Engineer"]
        E1[Review Risk Assessment]
        E2{Adjust Assumptions?}
        E3[Override / Tune Parameters]
    end
    subgraph L3["Manager / Safety Engineer"]
        M1[Approve Risk Assessment]
    end

    S1 --> S2 --> S3
    S2 --> S4
    S3 --> S5
    S4 --> S5 --> S6 --> E1
    E1 --> E2
    E2 -- Yes --> E3 --> S3
    E2 -- No --> M1
    M1 --> UPDATE[Update Inspection Plan with New Interval]
```

---

## 3. Repair Workflow

```mermaid
flowchart TB
    subgraph L1["Inspector / System"]
        I1[Finding Escalated to Defect]
    end
    subgraph L2["Asset / Reliability Engineer"]
        E1[Assess Defect Severity]
        E2{FFS Assessment Required?<br/>API 579}
        E3[Perform Fitness-For-Service Assessment]
        E4[Define Repair Scope]
    end
    subgraph L3["Manager"]
        M1{Approve Repair Plan?}
    end
    subgraph L4["Maintenance"]
        MT1[Create Maintenance Order]
        MT2[Execute Repair]
        MT3[Mark Repair Complete]
    end
    subgraph L5["Inspector"]
        IN1[Verify Repair<br/>Re-inspect / Re-measure]
    end
    subgraph L6["System"]
        SY1[Close Defect Record]
    end

    I1 --> E1 --> E2
    E2 -- Yes --> E3 --> E4
    E2 -- No --> E4
    E4 --> M1
    M1 -- No --> E4
    M1 -- Yes --> MT1 --> MT2 --> MT3
    MT3 --> IN1
    IN1 -- Pass --> SY1
    IN1 -- Fail --> MT2
```

---

## 4. Approval Workflow (Generic — Risk / Repair / Document)

```mermaid
flowchart TB
    subgraph L1["Requester<br/>(Engineer / Inspector)"]
        R1[Submit for Approval]
    end
    subgraph L2["System"]
        S1[Route to Approver by Role/Org]
        S2[Log Approval Decision to Audit Trail]
        S3{Approved?}
        S4[Update Record Status]
        S5[Notify Requester]
    end
    subgraph L3["Manager / Safety Engineer<br/>(Approver)"]
        M1[Review Submission]
        M2{Decision}
    end

    R1 --> S1 --> M1 --> M2
    M2 -- Approve --> S3
    M2 -- Reject with Comments --> S3
    S3 -- Yes --> S4
    S3 -- No --> S4
    S4 --> S2 --> S5
```

---

*Related: [DFD.md](DFD.md) · [BRD.md](../01-Business-Requirement/BRD.md) · Next: [BusinessFlow.md](BusinessFlow.md)*
