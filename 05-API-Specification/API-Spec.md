# REST API Specification
## Enterprise Asset Integrity Management System (AIMS)

| Field | Value |
|---|---|
| Version | 1.0 |
| Base URL | `https://api.aims.example.com/v1` |
| Spec Format | REST + JSON, OpenAPI 3.0 (this doc is the human-readable companion) |
| Auth | OAuth2 / JWT Bearer Token |

---

## 1. Global Conventions

### 1.1 Authentication & Authorization
- All endpoints (except `/auth/login`, `/auth/refresh`) require header: `Authorization: Bearer <JWT>`
- JWT claims include `sub` (user id), `org_id`, `roles[]`, `permissions[]`, `exp`
- Authorization is enforced per-endpoint against `permission.code` (e.g. `asset.create`, `inspection.approve`)

### 1.2 Standard Response Envelope
```json
{
  "success": true,
  "data": { },
  "meta": { "page": 1, "page_size": 20, "total": 134 },
  "error": null
}
```

### 1.3 Standard Error Format
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "tag_number is required",
    "details": [
      { "field": "tag_number", "issue": "required" }
    ]
  }
}
```

### 1.4 HTTP Status Codes
| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 400 | Validation error |
| 401 | Unauthenticated (missing/invalid token) |
| 403 | Unauthorized (valid token, insufficient permission) |
| 404 | Resource not found |
| 409 | Conflict (e.g. duplicate tag_number) |
| 422 | Semantic validation error (business rule) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

### 1.5 Pagination, Filtering, Sorting
- `?page=1&page_size=20` — pagination
- `?sort=-created_at,name` — sort (prefix `-` = descending)
- `?filter[status]=Active&filter[criticality_level]=High` — field filters

### 1.6 Security Baseline (applies to every endpoint)
- Input validated via Pydantic schema (type, length, enum, required) before reaching service layer
- Parameterized queries only (ORM) — no raw SQL string interpolation (SQL injection prevention)
- Output-encoded JSON (no HTML rendering server-side) — XSS not applicable at API layer, enforced at frontend render
- CSRF not applicable (stateless Bearer token, no cookie-based session)
- All mutating requests (`POST/PUT/PATCH/DELETE`) write an `audit_log` entry with before/after state
- Rate limiting: 100 req/min per user (configurable), enforced at API Gateway

---

## 2. Auth

| Method | Path | Description | Permission |
|---|---|---|---|
| POST | `/auth/login` | Username/password or SSO code exchange → JWT | Public |
| POST | `/auth/refresh` | Refresh access token | Valid refresh token |
| POST | `/auth/logout` | Revoke refresh token | Authenticated |

**POST `/auth/login`**
```json
// Request
{ "username": "j.smith", "password": "********" }

// Response 200
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "expires_in": 3600,
    "user": { "id": "uuid", "full_name": "John Smith", "roles": ["Inspector"] }
  }
}
```
Validation: `username` required; `password` required, min 8 chars.
Errors: `401 INVALID_CREDENTIALS`, `403 ACCOUNT_DISABLED`.

---

## 3. Identity & Access Management

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/users` | List users (paginated, filterable by org/role) | `user.read` |
| POST | `/users` | Create user | `user.create` |
| GET | `/users/{id}` | Get user detail | `user.read` |
| PUT | `/users/{id}` | Update user | `user.update` |
| DELETE | `/users/{id}` | Soft-delete/deactivate user | `user.delete` |
| GET | `/roles` | List roles | `role.read` |
| POST | `/roles` | Create role | `role.create` |
| PUT | `/roles/{id}/permissions` | Set role's permission set | `role.update` |
| POST | `/users/{id}/roles` | Assign role to user (scoped by org) | `user.update` |
| GET | `/organizations` | List organizations (tree) | `organization.read` |
| POST | `/organizations` | Create organization/plant | `organization.create` |

---

## 4. Asset Management

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/assets` | List assets (filter: location, class, criticality, status) | `asset.read` |
| POST | `/assets` | Create asset | `asset.create` |
| GET | `/assets/{id}` | Get asset detail (incl. equipment tree) | `asset.read` |
| PUT | `/assets/{id}` | Update asset | `asset.update` |
| DELETE | `/assets/{id}` | Soft-delete/retire asset | `asset.delete` |
| GET | `/assets/{id}/equipment` | List equipment/components under asset | `asset.read` |
| POST | `/assets/{id}/equipment` | Add equipment/component | `asset.update` |
| GET | `/locations` | List location tree (Plant/Area/Unit) | `location.read` |
| POST | `/locations` | Create location node | `location.create` |
| GET | `/asset-classes` | List asset classes | `asset.read` |
| POST | `/assets/{id}/criticality` | Submit criticality assessment | `asset.update` |

**POST `/assets`**
```json
// Request
{
  "location_id": "uuid",
  "asset_class_id": "uuid",
  "tag_number": "V-101",
  "name": "Feed Surge Vessel",
  "design_code": "ASME VIII Div.1",
  "design_pressure_bar": 12.5,
  "design_temperature_c": 150,
  "material": "SA-516-70",
  "install_date": "2020-03-15"
}

// Response 201
{
  "success": true,
  "data": {
    "id": "uuid",
    "tag_number": "V-101",
    "status": "Operating",
    "created_at": "2026-08-06T10:00:00Z"
  }
}
```
Validation: `tag_number` required, unique, max 50 chars; `location_id`/`asset_class_id` must reference existing records.
Errors: `409 DUPLICATE_TAG_NUMBER`, `400 VALIDATION_ERROR`, `404 LOCATION_NOT_FOUND`.

---

## 5. Inspection Management

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/inspection-plans` | List inspection plans (filter: asset, due date range) | `inspection.read` |
| POST | `/inspection-plans` | Create inspection plan | `inspection.create` |
| GET | `/inspections` | List inspections (filter: status, inspector, date) | `inspection.read` |
| POST | `/inspections` | Schedule inspection from plan | `inspection.create` |
| GET | `/inspections/{id}` | Get inspection detail (results, findings) | `inspection.read` |
| PUT | `/inspections/{id}` | Update inspection (status, actual_date) | `inspection.update` |
| POST | `/inspections/{id}/results` | Submit checklist results | `inspection.execute` |
| POST | `/inspections/{id}/findings` | Raise a finding | `inspection.execute` |
| POST | `/inspections/{id}/thickness-readings` | Submit thickness readings | `inspection.execute` |
| POST | `/inspections/{id}/complete` | Mark inspection complete | `inspection.execute` |

**POST `/inspections/{id}/findings`**
```json
// Request
{
  "equipment_id": "uuid",
  "finding_type": "Corrosion",
  "severity": "High",
  "description": "Localized pitting observed on shell course 2",
  "location_detail": "0.5m below manway N1",
  "photo_document_id": "uuid"
}

// Response 201
{
  "success": true,
  "data": { "id": "uuid", "status": "Open", "raised_date": "2026-08-06" }
}
```
Validation: `severity` must be one of `Low|Medium|High|Critical`; `equipment_id` must belong to the inspection's asset.
Errors: `422 EQUIPMENT_NOT_IN_ASSET_SCOPE`.

---

## 6. Risk Based Inspection (RBI)

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/risk-assessments` | List risk assessments (filter: asset, risk_rank) | `risk.read` |
| POST | `/risk-assessments` | Create/run risk assessment for asset/equipment | `risk.create` |
| GET | `/risk-assessments/{id}` | Get risk assessment detail | `risk.read` |
| POST | `/risk-assessments/{id}/approve` | Approve risk assessment | `risk.approve` |
| GET | `/risk-matrix` | Get configured 5x5 risk matrix definition | `risk.read` |
| GET | `/assets/{id}/risk-history` | Risk score trend over time for an asset | `risk.read` |

**POST `/risk-assessments`**
```json
// Request
{
  "asset_id": "uuid",
  "equipment_id": "uuid",
  "methodology": "SemiQuantitative",
  "pof_score": 3.2,
  "cof_financial": 1500000,
  "cof_safety": "High",
  "cof_environmental": "Medium"
}

// Response 201
{
  "success": true,
  "data": {
    "id": "uuid",
    "risk_score": 12.8,
    "risk_rank": "High",
    "recommended_interval_months": 24,
    "next_inspection_date": "2028-08-06",
    "status": "Draft"
  }
}
```
Validation: `pof_score` numeric 0–5; risk score/rank are **server-calculated**, not client-supplied.
Errors: `422 INVALID_METHODOLOGY_FOR_ASSET_CLASS`.

---

## 7. Corrosion Management

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/equipment/{id}/thickness-records` | List thickness readings for a CML | `corrosion.read` |
| POST | `/equipment/{id}/thickness-records` | Add thickness reading | `corrosion.create` |
| GET | `/equipment/{id}/corrosion-records` | List corrosion rate/remaining-life calculations | `corrosion.read` |
| POST | `/equipment/{id}/corrosion-records/calculate` | Trigger corrosion rate & remaining life calculation | `corrosion.create` |
| GET | `/equipment/{id}/corrosion-trend` | Trend chart data (thickness vs. time) | `corrosion.read` |

**POST `/equipment/{id}/corrosion-records/calculate`**
```json
// Response 200
{
  "success": true,
  "data": {
    "short_term_rate_mm_yr": 0.15,
    "long_term_rate_mm_yr": 0.09,
    "governing_rate_mm_yr": 0.15,
    "remaining_life_years": 6.7,
    "next_inspection_date": "2029-08-06",
    "calculation_basis": "API 570"
  }
}
```
Errors: `422 INSUFFICIENT_THICKNESS_HISTORY` (requires ≥ 2 readings).

---

## 8. Defect Management

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/defects` | List defects (filter: workflow_status, severity, assigned_to) | `defect.read` |
| POST | `/defects` | Create defect (from finding) | `defect.create` |
| GET | `/defects/{id}` | Get defect detail | `defect.read` |
| PUT | `/defects/{id}` | Update defect (workflow_status transition) | `defect.update` |
| POST | `/defects/{id}/approve` | Approve repair plan | `defect.approve` |
| POST | `/defects/{id}/verify` | Verify & close after repair | `defect.update` |

Workflow transitions enforced server-side: `Finding → Assessment → Approval → Repair → Verification → Closed`
(illegal transitions return `422 INVALID_WORKFLOW_TRANSITION`).

---

## 9. Condition Monitoring

| Method | Path | Description | Permission |
|---|---|---|---|
| POST | `/sensor-data` | Ingest sensor reading (also via MQTT/OPC-UA bridge) | `sensor.write` (service account) |
| GET | `/equipment/{id}/sensor-data` | Query time-series data (range, sensor_type) | `sensor.read` |
| GET | `/equipment/{id}/sensor-data/latest` | Latest reading per sensor_type | `sensor.read` |
| POST | `/alert-rules` | Define threshold alert rule | `sensor.configure` |

**GET `/equipment/{id}/sensor-data?sensor_type=Temperature&from=2026-08-01&to=2026-08-06`**
```json
{
  "success": true,
  "data": [
    { "reading_timestamp": "2026-08-06T08:00:00Z", "value": 82.4, "unit": "C" },
    { "reading_timestamp": "2026-08-06T09:00:00Z", "value": 83.1, "unit": "C" }
  ],
  "meta": { "count": 2 }
}
```

---

## 10. Document Management

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/documents` | List documents (filter: asset, type) | `document.read` |
| POST | `/documents` | Upload document (multipart) — requires explicit user confirmation for external uploads | `document.create` |
| GET | `/documents/{id}` | Get document metadata | `document.read` |
| GET | `/documents/{id}/download` | Download signed URL | `document.read` |
| POST | `/documents/{id}/versions` | Upload new version | `document.update` |

---

## 11. Maintenance

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/maintenance-orders` | List maintenance orders | `maintenance.read` |
| POST | `/maintenance-orders` | Create maintenance order | `maintenance.create` |
| PUT | `/maintenance-orders/{id}` | Update status/completion | `maintenance.update` |

---

## 12. Dashboard & Reporting

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/dashboards/executive` | Executive KPI summary | `dashboard.executive` |
| GET | `/dashboards/engineering` | Engineering/reliability dashboard | `dashboard.engineering` |
| GET | `/dashboards/inspection` | Inspection compliance dashboard | `dashboard.inspection` |
| GET | `/reports/{type}/export` | Export report (PDF/Excel) | `report.export` |

---

## 13. AI Copilot

| Method | Path | Description | Permission |
|---|---|---|---|
| POST | `/ai/query` | Natural-language question over asset/risk/inspection data (RAG) | `ai.query` |
| POST | `/ai/reports/generate` | Generate draft inspection/summary report | `ai.generate` |
| GET | `/ai/predictions/{asset_id}` | Get failure-risk / remaining-life predictions | `ai.read` |

**POST `/ai/query`**
```json
// Request
{ "question": "Which equipment has the highest risk in Unit 200?" }

// Response 200
{
  "success": true,
  "data": {
    "answer": "V-204 (Feed Separator) has the highest risk score (18.4, VeryHigh) in Unit 200, driven by a high POF from recent corrosion findings.",
    "sources": [
      { "type": "risk_assessment", "id": "uuid" },
      { "type": "finding", "id": "uuid" }
    ]
  }
}
```
Security note: AI queries are scoped to the requesting user's `org_id`/RBAC visibility — the RAG retrieval
layer filters context documents by the same permission set as the REST API before passing them to the LLM,
preventing cross-tenant/cross-role data leakage via prompt.

---

## 14. Audit Log (read-only)

| Method | Path | Description | Permission |
|---|---|---|---|
| GET | `/audit-logs` | Query audit trail (filter: entity_type, entity_id, user_id, date range) | `audit.read` |

---

*Related: [Database.md](../03-Database-Design/Database.md) · [BusinessFlow.md](../04-Process-Design/BusinessFlow.md) · Next: [Backend-Design](../07-Backend-Design/)*
