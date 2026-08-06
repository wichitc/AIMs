# Entity Relationship Diagram (ERD)
## Enterprise Asset Integrity Management System (AIMS)

Full column-level definitions, indexes, and constraints are in [Database.md](Database.md).
This document shows entity relationships grouped by module.

---

## 1. Identity & Access Management

```mermaid
erDiagram
    ORGANIZATION ||--o{ ORGANIZATION : "parent of"
    ORGANIZATION ||--o{ USER : employs
    ORGANIZATION ||--o{ LOCATION : owns
    USER ||--o{ USER_ROLE : has
    ROLE ||--o{ USER_ROLE : "assigned via"
    ROLE ||--o{ ROLE_PERMISSION : has
    PERMISSION ||--o{ ROLE_PERMISSION : "granted via"

    ORGANIZATION {
        uuid id PK
        uuid parent_org_id FK
        string name
        string code
        string org_type
    }
    USER {
        uuid id PK
        uuid org_id FK
        string username
        string email
        string password_hash
        boolean is_active
    }
    ROLE {
        uuid id PK
        string name
        boolean is_system_role
    }
    PERMISSION {
        uuid id PK
        string code
        string module
        string action
    }
    USER_ROLE {
        uuid user_id FK
        uuid role_id FK
        uuid org_id FK
    }
    ROLE_PERMISSION {
        uuid role_id FK
        uuid permission_id FK
    }
```

---

## 2. Asset Hierarchy

```mermaid
erDiagram
    ORGANIZATION ||--o{ LOCATION : owns
    LOCATION ||--o{ LOCATION : "parent of (Plant>Area>Unit)"
    LOCATION ||--o{ ASSET : hosts
    ASSET_CLASS ||--o{ ASSET : classifies
    ASSET ||--o| CRITICALITY : "current rating"
    ASSET ||--o{ CRITICALITY : "assessment history"
    ASSET ||--o{ EQUIPMENT : "decomposed into"
    EQUIPMENT ||--o{ EQUIPMENT : "parent of (Component>InspectionPoint)"

    LOCATION {
        uuid id PK
        uuid org_id FK
        uuid parent_location_id FK
        string level
        string name
        string code
    }
    ASSET_CLASS {
        uuid id PK
        string name
        string category
    }
    ASSET {
        uuid id PK
        uuid org_id FK
        uuid location_id FK
        uuid asset_class_id FK
        uuid current_criticality_id FK
        string tag_number
        string name
        string status
    }
    EQUIPMENT {
        uuid id PK
        uuid asset_id FK
        uuid parent_equipment_id FK
        string level
        string tag_number
        string cml_number
    }
    CRITICALITY {
        uuid id PK
        uuid asset_id FK
        string criticality_level
        numeric calculated_score
    }
```

---

## 3. Inspection & Risk Based Inspection

```mermaid
erDiagram
    ASSET ||--o{ INSPECTION_PLAN : "planned for"
    EQUIPMENT ||--o{ INSPECTION_PLAN : "planned for"
    INSPECTION_PLAN ||--o{ INSPECTION : generates
    ASSET ||--o{ INSPECTION : "inspected"
    EQUIPMENT ||--o{ INSPECTION : "inspected"
    USER ||--o{ INSPECTION : "performed by (inspector)"
    INSPECTION ||--o{ INSPECTION_RESULT : produces
    INSPECTION ||--o{ FINDING : raises
    EQUIPMENT ||--o{ FINDING : "found on"
    ASSET ||--o{ RISK_ASSESSMENT : "assessed for"
    EQUIPMENT ||--o{ RISK_ASSESSMENT : "assessed for"

    INSPECTION_PLAN {
        uuid id PK
        uuid asset_id FK
        uuid equipment_id FK
        string plan_code
        string applicable_code
        string basis
        date next_due_date
    }
    INSPECTION {
        uuid id PK
        uuid inspection_plan_id FK
        uuid asset_id FK
        uuid equipment_id FK
        uuid inspector_id FK
        string status
        date scheduled_date
        date actual_date
    }
    INSPECTION_RESULT {
        uuid id PK
        uuid inspection_id FK
        string checklist_item
        string result_status
    }
    FINDING {
        uuid id PK
        uuid inspection_id FK
        uuid equipment_id FK
        string finding_type
        string severity
        string status
    }
    RISK_ASSESSMENT {
        uuid id PK
        uuid asset_id FK
        uuid equipment_id FK
        numeric pof_score
        string cof_category
        numeric risk_score
        string risk_rank
        date next_inspection_date
    }
```

---

## 4. Corrosion, Defect & Maintenance

```mermaid
erDiagram
    EQUIPMENT ||--o{ THICKNESS_RECORD : measured
    INSPECTION ||--o{ THICKNESS_RECORD : "captured during"
    EQUIPMENT ||--o{ CORROSION_RECORD : "rate calculated for"
    FINDING ||--o{ DEFECT : "escalated to"
    EQUIPMENT ||--o{ DEFECT : "affects"
    DEFECT ||--o{ MAINTENANCE_ORDER : "resolved by"
    EQUIPMENT ||--o{ MAINTENANCE_ORDER : "target of"
    USER ||--o{ MAINTENANCE_ORDER : "assigned to"

    THICKNESS_RECORD {
        uuid id PK
        uuid equipment_id FK
        uuid inspection_id FK
        date reading_date
        numeric measured_thickness_mm
    }
    CORROSION_RECORD {
        uuid id PK
        uuid equipment_id FK
        numeric governing_rate_mm_yr
        numeric remaining_life_years
        date next_inspection_date
    }
    DEFECT {
        uuid id PK
        uuid finding_id FK
        uuid equipment_id FK
        string workflow_status
        boolean ffs_required
        date due_date
    }
    MAINTENANCE_ORDER {
        uuid id PK
        uuid equipment_id FK
        uuid defect_id FK
        string order_type
        string status
    }
```

---

## 5. Condition Monitoring, Document, Audit & AI

```mermaid
erDiagram
    EQUIPMENT ||--o{ SENSOR_DATA : streams
    ORGANIZATION ||--o{ DOCUMENT : stores
    ASSET ||--o{ DOCUMENT : "attached to"
    EQUIPMENT ||--o{ DOCUMENT : "attached to"
    INSPECTION ||--o{ DOCUMENT : "attached to"
    USER ||--o{ AUDIT_LOG : performs
    ASSET ||--o{ AI_PREDICTION : "predicted for"
    EQUIPMENT ||--o{ AI_PREDICTION : "predicted for"

    SENSOR_DATA {
        uuid id PK
        uuid equipment_id FK
        string sensor_type
        double value
        timestamptz reading_timestamp
    }
    DOCUMENT {
        uuid id PK
        uuid org_id FK
        uuid asset_id FK
        uuid equipment_id FK
        string document_type
        string storage_key
        int version
    }
    AUDIT_LOG {
        uuid id PK
        uuid user_id FK
        string action
        string entity_type
        uuid entity_id
        jsonb old_value
        jsonb new_value
    }
    AI_PREDICTION {
        uuid id PK
        uuid asset_id FK
        uuid equipment_id FK
        string prediction_type
        jsonb predicted_value
        numeric confidence_score
    }
```

---

*Related: [Database.md](Database.md) (full column/index/constraint spec) · [DFD.md](../04-Process-Design/DFD.md)*
