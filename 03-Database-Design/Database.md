# Database Design
## Enterprise Asset Integrity Management System (AIMS)

| Field | Value |
|---|---|
| Version | 1.0 |
| Status | Draft |
| Date | 2026-08-06 |
| Engine | PostgreSQL 16 (+ TimescaleDB extension for `sensor_data`) |

---

## 1. Conventions

| Convention | Rule |
|---|---|
| Primary Key | `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` on every table |
| Audit Fields | Every table (except the immutable `sensor_data` hypertable and `audit_log`) carries `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `created_by UUID REFERENCES "user"(id)`, `updated_by UUID REFERENCES "user"(id)` |
| Soft Delete | `is_deleted BOOLEAN NOT NULL DEFAULT false`, `deleted_at TIMESTAMPTZ NULL` on master-data tables (asset, equipment, user, document) |
| Naming | Tables/columns: `snake_case`, singular noun (`asset`, not `assets`) |
| Foreign Keys | Named `<table>_id`; `ON DELETE RESTRICT` by default, `ON DELETE CASCADE` only on junction/child-detail tables explicitly noted |
| Enums | Implemented as PostgreSQL `CHECK` constraints or native `ENUM` types for portability with ORMs |
| Multi-tenancy | Every top-level table scoped by `org_id` (directly or transitively via asset/location) to support Row-Level Security in Postgres |

---

## 2. Asset Hierarchy Mapping

The business hierarchy `Plant → Area → Unit → Equipment → Component → Inspection Point` maps to tables as follows:

| Business Level | Table | Notes |
|---|---|---|
| Plant / Area / Unit | `location` | Self-referencing (`parent_location_id`), discriminated by `level` |
| Equipment | `asset` | Registered, tagged item — FK to `location` (Unit) |
| Component / Inspection Point | `equipment` | Self-referencing (`parent_equipment_id`), discriminated by `level`, FK to `asset` |

---

## 3. Module: Identity & Access Management

### 3.1 `organization`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| parent_org_id | UUID | FK → organization(id), NULL for root |
| name | VARCHAR(200) | NOT NULL |
| code | VARCHAR(50) | NOT NULL, UNIQUE |
| org_type | VARCHAR(30) | CHECK IN ('Corporate','BusinessUnit','Plant') |
| address | TEXT | NULL |
| created_at/updated_at/created_by/updated_by | — | standard audit |

Indexes: `idx_organization_parent (parent_org_id)`, `uq_organization_code (code)`

### 3.2 `user`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → organization(id), NOT NULL |
| username | VARCHAR(100) | NOT NULL, UNIQUE |
| email | VARCHAR(200) | NOT NULL, UNIQUE |
| password_hash | VARCHAR(255) | NULL (NULL if SSO-only) |
| sso_subject_id | VARCHAR(255) | NULL, UNIQUE |
| full_name | VARCHAR(200) | NOT NULL |
| phone | VARCHAR(30) | NULL |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| last_login_at | TIMESTAMPTZ | NULL |
| is_deleted / deleted_at | — | soft delete |
| audit fields | — | standard |

Indexes: `uq_user_username`, `uq_user_email`, `idx_user_org (org_id)`

### 3.3 `role`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(100) | NOT NULL, UNIQUE |
| description | TEXT | NULL |
| is_system_role | BOOLEAN | DEFAULT false |
| audit fields | — | standard |

### 3.4 `permission`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| code | VARCHAR(100) | NOT NULL, UNIQUE (e.g. `asset.create`) |
| module | VARCHAR(50) | NOT NULL |
| action | VARCHAR(30) | CHECK IN ('create','read','update','delete','approve','export') |
| description | TEXT | NULL |
| audit fields | — | standard |

### 3.5 `role_permission` (junction)
| Column | Type | Constraint |
|---|---|---|
| role_id | UUID | FK → role(id), ON DELETE CASCADE |
| permission_id | UUID | FK → permission(id), ON DELETE CASCADE |
| created_at / created_by | — | standard |

PK: composite `(role_id, permission_id)`

### 3.6 `user_role` (junction)
| Column | Type | Constraint |
|---|---|---|
| user_id | UUID | FK → user(id), ON DELETE CASCADE |
| role_id | UUID | FK → role(id), ON DELETE CASCADE |
| org_id | UUID | FK → organization(id) — scopes the role assignment |
| created_at / created_by | — | standard |

PK: composite `(user_id, role_id, org_id)`

---

## 4. Module: Asset Management

### 4.1 `location`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → organization(id), NOT NULL |
| parent_location_id | UUID | FK → location(id), NULL for Plant root |
| level | VARCHAR(20) | CHECK IN ('Plant','Area','Unit') |
| name | VARCHAR(200) | NOT NULL |
| code | VARCHAR(50) | NOT NULL |
| latitude / longitude | NUMERIC(9,6) | NULL |
| audit fields | — | standard |

Indexes: `idx_location_parent`, `uq_location_org_code (org_id, code)`

### 4.2 `asset_class`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(100) | NOT NULL |
| code | VARCHAR(30) | NOT NULL, UNIQUE |
| category | VARCHAR(30) | CHECK IN ('PressureVessel','Piping','Tank','Rotating','Static','Instrument','Electrical') |
| description | TEXT | NULL |
| audit fields | — | standard |

### 4.3 `asset`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → organization(id), NOT NULL |
| location_id | UUID | FK → location(id), NOT NULL |
| asset_class_id | UUID | FK → asset_class(id), NOT NULL |
| tag_number | VARCHAR(50) | NOT NULL, UNIQUE |
| name | VARCHAR(200) | NOT NULL |
| design_code | VARCHAR(50) | NULL (e.g. ASME VIII Div.1, API 650) |
| design_pressure_bar | NUMERIC(10,2) | NULL |
| design_temperature_c | NUMERIC(10,2) | NULL |
| material | VARCHAR(100) | NULL |
| install_date | DATE | NULL |
| status | VARCHAR(20) | CHECK IN ('Design','Construction','Commissioning','Operating','Inactive','Decommissioned') |
| current_criticality_id | UUID | FK → criticality(id), NULL |
| is_deleted / deleted_at | — | soft delete |
| audit fields | — | standard |

Indexes: `uq_asset_tag_number`, `idx_asset_location`, `idx_asset_class`, `idx_asset_criticality`

### 4.4 `equipment`
Represents **Component** and **Inspection Point** levels beneath an `asset`.

| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| asset_id | UUID | FK → asset(id), NOT NULL |
| parent_equipment_id | UUID | FK → equipment(id), NULL (self-ref for Inspection Point under Component) |
| level | VARCHAR(20) | CHECK IN ('Component','InspectionPoint') |
| tag_number | VARCHAR(50) | NOT NULL |
| name | VARCHAR(200) | NOT NULL |
| cml_number | VARCHAR(30) | NULL (Corrosion Monitoring Location ID, applies to InspectionPoint) |
| nominal_thickness_mm | NUMERIC(8,3) | NULL |
| minimum_required_thickness_mm | NUMERIC(8,3) | NULL |
| is_deleted / deleted_at | — | soft delete |
| audit fields | — | standard |

Indexes: `idx_equipment_asset`, `idx_equipment_parent`, `uq_equipment_asset_tag (asset_id, tag_number)`

### 4.5 `criticality`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| asset_id | UUID | FK → asset(id), NOT NULL |
| safety_score | NUMERIC(5,2) | NOT NULL |
| environmental_score | NUMERIC(5,2) | NOT NULL |
| economic_score | NUMERIC(5,2) | NOT NULL |
| calculated_score | NUMERIC(5,2) | NOT NULL |
| criticality_level | VARCHAR(20) | CHECK IN ('Low','Medium','High','VeryHigh') |
| methodology | VARCHAR(50) | NULL |
| assessed_date | DATE | NOT NULL |
| assessed_by | UUID | FK → user(id) |
| audit fields | — | standard |

Indexes: `idx_criticality_asset`

---

## 5. Module: Inspection Management

### 5.1 `inspection_plan`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| asset_id | UUID | FK → asset(id), NOT NULL |
| equipment_id | UUID | FK → equipment(id), NULL |
| plan_code | VARCHAR(50) | NOT NULL, UNIQUE |
| applicable_code | VARCHAR(50) | NULL (API 510 / 570 / 653 / 580) |
| inspection_type | VARCHAR(30) | CHECK IN ('Visual','UT','RT','MT','PT','PMI','Other') |
| basis | VARCHAR(20) | CHECK IN ('RBI','FixedInterval','Regulatory') |
| frequency_months | INTEGER | NOT NULL |
| next_due_date | DATE | NOT NULL |
| status | VARCHAR(20) | CHECK IN ('Active','Suspended','Retired') |
| audit fields | — | standard |

Indexes: `idx_plan_asset`, `idx_plan_next_due`

### 5.2 `inspection`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| inspection_plan_id | UUID | FK → inspection_plan(id), NOT NULL |
| asset_id | UUID | FK → asset(id), NOT NULL |
| equipment_id | UUID | FK → equipment(id), NULL |
| inspector_id | UUID | FK → user(id), NOT NULL |
| inspection_type | VARCHAR(30) | same enum as plan |
| scheduled_date | DATE | NOT NULL |
| actual_date | DATE | NULL |
| status | VARCHAR(20) | CHECK IN ('Planned','InProgress','Completed','Overdue','Cancelled') |
| audit fields | — | standard |

Indexes: `idx_inspection_plan`, `idx_inspection_asset`, `idx_inspection_status_date (status, scheduled_date)`

### 5.3 `inspection_result`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| inspection_id | UUID | FK → inspection(id), NOT NULL, ON DELETE CASCADE |
| checklist_item | VARCHAR(300) | NOT NULL |
| result_value | VARCHAR(500) | NULL |
| result_status | VARCHAR(10) | CHECK IN ('Pass','Fail','NA') |
| remarks | TEXT | NULL |
| attachment_document_id | UUID | FK → document(id), NULL |
| recorded_at | TIMESTAMPTZ | NOT NULL |
| recorded_by | UUID | FK → user(id) |
| audit fields | — | standard |

Indexes: `idx_result_inspection`

### 5.4 `finding`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| inspection_id | UUID | FK → inspection(id), NOT NULL |
| equipment_id | UUID | FK → equipment(id), NOT NULL |
| finding_type | VARCHAR(30) | CHECK IN ('Corrosion','Crack','Leak','CoatingFailure','Deformation','Other') |
| severity | VARCHAR(20) | CHECK IN ('Low','Medium','High','Critical') |
| description | TEXT | NOT NULL |
| location_detail | VARCHAR(300) | NULL |
| photo_document_id | UUID | FK → document(id), NULL |
| status | VARCHAR(20) | CHECK IN ('Open','UnderAssessment','Closed') |
| raised_by | UUID | FK → user(id), NOT NULL |
| raised_date | DATE | NOT NULL |
| audit fields | — | standard |

Indexes: `idx_finding_inspection`, `idx_finding_equipment`, `idx_finding_status`

---

## 6. Module: Risk Based Inspection

### 6.1 `risk_assessment`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| asset_id | UUID | FK → asset(id), NOT NULL |
| equipment_id | UUID | FK → equipment(id), NULL |
| assessment_date | DATE | NOT NULL |
| methodology | VARCHAR(20) | CHECK IN ('Qualitative','SemiQuantitative','Quantitative') |
| pof_score | NUMERIC(6,3) | NOT NULL |
| pof_category | VARCHAR(1) | CHECK IN ('1','2','3','4','5') |
| cof_financial | NUMERIC(14,2) | NULL |
| cof_safety | VARCHAR(20) | NULL |
| cof_environmental | VARCHAR(20) | NULL |
| cof_category | VARCHAR(1) | CHECK IN ('A','B','C','D','E') |
| risk_score | NUMERIC(8,3) | NOT NULL |
| risk_rank | VARCHAR(20) | CHECK IN ('Low','Medium','High','VeryHigh') |
| recommended_interval_months | INTEGER | NULL |
| next_inspection_date | DATE | NULL |
| assessed_by | UUID | FK → user(id) |
| approved_by | UUID | FK → user(id), NULL |
| status | VARCHAR(20) | CHECK IN ('Draft','PendingApproval','Approved') |
| audit fields | — | standard |

Indexes: `idx_risk_asset`, `idx_risk_rank`, `idx_risk_next_due`

---

## 7. Module: Corrosion Management

### 7.1 `thickness_record`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| equipment_id | UUID | FK → equipment(id) [level='InspectionPoint'], NOT NULL |
| inspection_id | UUID | FK → inspection(id), NULL |
| reading_date | DATE | NOT NULL |
| measured_thickness_mm | NUMERIC(8,3) | NOT NULL |
| measurement_method | VARCHAR(20) | CHECK IN ('UT','RT') |
| recorded_by | UUID | FK → user(id) |
| audit fields | — | standard |

Indexes: `idx_thickness_equipment_date (equipment_id, reading_date)`

### 7.2 `corrosion_record`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| equipment_id | UUID | FK → equipment(id), NOT NULL |
| assessment_date | DATE | NOT NULL |
| short_term_rate_mm_yr | NUMERIC(8,4) | NULL |
| long_term_rate_mm_yr | NUMERIC(8,4) | NULL |
| governing_rate_mm_yr | NUMERIC(8,4) | NOT NULL |
| remaining_life_years | NUMERIC(6,2) | NOT NULL |
| next_inspection_date | DATE | NOT NULL |
| calculation_basis | VARCHAR(50) | NULL (e.g. API 570 / API 653 / API 579) |
| calculated_by | UUID | FK → user(id) |
| audit fields | — | standard |

Indexes: `idx_corrosion_equipment`, `idx_corrosion_next_due`

---

## 8. Module: Defect Management

### 8.1 `defect`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| finding_id | UUID | FK → finding(id), NOT NULL |
| equipment_id | UUID | FK → equipment(id), NOT NULL |
| defect_type | VARCHAR(50) | NOT NULL |
| severity | VARCHAR(20) | CHECK IN ('Low','Medium','High','Critical') |
| workflow_status | VARCHAR(20) | CHECK IN ('Finding','Assessment','Approval','Repair','Verification','Closed') |
| ffs_required | BOOLEAN | DEFAULT false |
| ffs_reference_document_id | UUID | FK → document(id), NULL |
| assigned_to | UUID | FK → user(id), NULL |
| due_date | DATE | NULL |
| closed_date | DATE | NULL |
| audit fields | — | standard |

Indexes: `idx_defect_finding`, `idx_defect_status`, `idx_defect_assigned`

---

## 9. Module: Condition Monitoring

### 9.1 `sensor_data` (TimescaleDB Hypertable)
| Column | Type | Constraint |
|---|---|---|
| id | UUID | DEFAULT gen_random_uuid() |
| equipment_id | UUID | FK → equipment(id), NOT NULL |
| sensor_type | VARCHAR(20) | CHECK IN ('Temperature','Pressure','Vibration','Flow') |
| value | DOUBLE PRECISION | NOT NULL |
| unit | VARCHAR(10) | NOT NULL |
| reading_timestamp | TIMESTAMPTZ | NOT NULL — **partitioning key** |
| source | VARCHAR(20) | CHECK IN ('MQTT','OPC-UA','Modbus') |
| quality_flag | VARCHAR(10) | DEFAULT 'Good' |
| created_at | TIMESTAMPTZ | DEFAULT now() |

PK: composite `(id, reading_timestamp)` (required by TimescaleDB hypertable partitioning)
`SELECT create_hypertable('sensor_data', 'reading_timestamp');`
Indexes: `idx_sensor_equipment_time (equipment_id, reading_timestamp DESC)`
Retention: continuous aggregate + retention policy (raw data 2 years, hourly rollups indefinite)

---

## 10. Module: Maintenance

### 10.1 `maintenance_order`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| equipment_id | UUID | FK → equipment(id), NOT NULL |
| defect_id | UUID | FK → defect(id), NULL |
| order_type | VARCHAR(20) | CHECK IN ('Corrective','Preventive','Predictive') |
| description | TEXT | NOT NULL |
| priority | VARCHAR(10) | CHECK IN ('Low','Medium','High','Urgent') |
| status | VARCHAR(20) | CHECK IN ('Open','InProgress','Completed','Cancelled') |
| scheduled_date | DATE | NULL |
| completed_date | DATE | NULL |
| assigned_to | UUID | FK → user(id), NULL |
| cost_estimate | NUMERIC(14,2) | NULL |
| audit fields | — | standard |

Indexes: `idx_mo_equipment`, `idx_mo_status`

---

## 11. Module: Document Management

### 11.1 `document`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → organization(id), NOT NULL |
| asset_id | UUID | FK → asset(id), NULL |
| equipment_id | UUID | FK → equipment(id), NULL |
| inspection_id | UUID | FK → inspection(id), NULL |
| document_type | VARCHAR(30) | CHECK IN ('PID','Drawing','Certificate','Report','InspectionRecord','Photo','Other') |
| file_name | VARCHAR(255) | NOT NULL |
| storage_key | VARCHAR(500) | NOT NULL (object storage path) |
| version | INTEGER | DEFAULT 1 |
| mime_type | VARCHAR(100) | NULL |
| file_size_bytes | BIGINT | NULL |
| uploaded_by | UUID | FK → user(id) |
| uploaded_at | TIMESTAMPTZ | NOT NULL |
| is_deleted / deleted_at | — | soft delete |
| audit fields | — | standard |

Indexes: `idx_document_asset`, `idx_document_equipment`, `idx_document_type`

---

## 12. Module: Audit & AI

### 12.1 `audit_log` (append-only, immutable)
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → organization(id) |
| user_id | UUID | FK → user(id), NULL (system actions) |
| action | VARCHAR(20) | CHECK IN ('Create','Update','Delete','Login','Logout','Approve','Export') |
| entity_type | VARCHAR(50) | NOT NULL |
| entity_id | UUID | NOT NULL |
| old_value | JSONB | NULL |
| new_value | JSONB | NULL |
| ip_address | INET | NULL |
| timestamp | TIMESTAMPTZ | NOT NULL DEFAULT now() |

Indexes: `idx_audit_entity (entity_type, entity_id)`, `idx_audit_user`, `idx_audit_timestamp`
Constraint: No UPDATE/DELETE grants at the DB role level — insert-only via application role.

### 12.2 `ai_prediction`
| Column | Type | Constraint |
|---|---|---|
| id | UUID | PK |
| asset_id | UUID | FK → asset(id), NOT NULL |
| equipment_id | UUID | FK → equipment(id), NULL |
| prediction_type | VARCHAR(30) | CHECK IN ('FailureRisk','RemainingLife','Anomaly','MaintenanceRecommendation') |
| predicted_value | JSONB | NOT NULL |
| confidence_score | NUMERIC(5,4) | NOT NULL |
| model_version | VARCHAR(50) | NOT NULL |
| input_features | JSONB | NULL |
| predicted_for_date | DATE | NULL |
| generated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| created_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `idx_prediction_asset`, `idx_prediction_type`

---

*Related: [ERD.md](ERD.md) · [BRD.md](../01-Business-Requirement/BRD.md) · Next: [API-Spec.md](../05-API-Specification/API-Spec.md)*
