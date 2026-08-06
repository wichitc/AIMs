# System Integration Test (SIT)
## Enterprise Asset Integrity Management System (AIMS)

Executed against a docker-compose environment with a real PostgreSQL/TimescaleDB instance (not mocked —
per this project's standard: integration tests hit real infrastructure so schema/constraint mismatches
surface here rather than in production). `Actual Result` / `Status` columns are filled in during test
execution; they are left blank in this document as it defines the planned case set.

---

## Login & Access

| Test ID | Scenario | Precondition | Test Step | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| SIT-AIMS-001 | Successful login issues a scoped JWT | Active user `inspector1` exists with role `Inspector` | `POST /v1/auth/login` with valid credentials | `200`, `access_token` returned; decoded JWT contains `org_id` and `permissions[]` matching the user's assigned role | | |
| SIT-AIMS-001b | Login rejected for wrong password | User exists | `POST /v1/auth/login` with wrong password | `401 INVALID_CREDENTIALS` | | |
| SIT-AIMS-001c | Disabled account cannot log in | User `is_active=false` | `POST /v1/auth/login` with correct credentials | `401`, "Account is disabled" | | |
| SIT-AIMS-001d | Endpoint rejects request without a permission the caller lacks | Logged in as `Inspector` (no `asset.create`) | `POST /v1/assets` | `403 FORBIDDEN` | | |

## Asset CRUD

| Test ID | Scenario | Precondition | Test Step | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| SIT-AIMS-002 | Create asset with unique tag number | Authenticated as role with `asset.create` | `POST /v1/assets` with new `tag_number` | `201`, asset returned with `status=Operating` | | |
| SIT-AIMS-002b | Duplicate tag number rejected | Asset `V-101` already exists | `POST /v1/assets` with `tag_number=V-101` | `409 CONFLICT` | | |
| SIT-AIMS-002c | Asset hierarchy traversal | Asset has 2 equipment/component children | `GET /v1/assets/{id}/equipment` | `200`, both children returned | | |
| SIT-AIMS-002d | Criticality assessment updates the asset's current rating | Asset exists | `POST /v1/assets/{id}/criticality` with scores | `201`; subsequent `GET /v1/assets/{id}` reflects the new `current_criticality_id` | | |

## Inspection Flow

| Test ID | Scenario | Precondition | Test Step | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| SIT-AIMS-003 | Full inspection lifecycle | Inspection plan exists | Schedule inspection → submit 3 checklist results → raise 1 finding → complete inspection | Each step `2xx`; final `GET /v1/inspections/{id}` shows `status=Completed`, `actual_date` set | | |
| SIT-AIMS-003b | Cannot add results after completion | Inspection is `Completed` | `POST /v1/inspections/{id}/results` | `422`, "Cannot add results to a completed inspection" | | |
| SIT-AIMS-003c | Completing twice is rejected | Inspection is `Completed` | `POST /v1/inspections/{id}/complete` | `422`, "Inspection is already completed" | | |
| SIT-AIMS-003d | Finding equipment must belong to a valid equipment record | Inspection exists | `POST /v1/inspections/{id}/findings` with a random `equipment_id` | `4xx` — foreign key / not-found rejection | | |

## RBI Calculation

| Test ID | Scenario | Precondition | Test Step | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| SIT-AIMS-004 | Risk assessment persists server-calculated fields | Asset exists | `POST /v1/risk-assessments` with `pof_score` + COF inputs | `201`; `risk_score`, `risk_rank`, `recommended_interval_months`, `next_inspection_date` are present and match the documented formula (not client-supplied) | | |
| SIT-AIMS-004b | High-risk asset appears in ranked list | Assessment created with `risk_rank=VeryHigh` | `GET /v1/risk-assessments?risk_rank=VeryHigh` | `200`, includes the created assessment | | |
| SIT-AIMS-004c | Approval transitions status | Assessment `status=Draft` | `POST /v1/risk-assessments/{id}/approve` | `200`, `status=Approved`, `approved_by` set; `audit_log` has an `Approve` entry | | |

## Corrosion Calculation

| Test ID | Scenario | Precondition | Test Step | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| SIT-AIMS-005 | Corrosion calculation requires history | Equipment has 0-1 thickness readings | `POST /v1/equipment/{id}/corrosion-records/calculate` | `422 INSUFFICIENT_THICKNESS_HISTORY` | | |
| SIT-AIMS-005b | Corrosion calculation with sufficient history | Equipment has ≥2 thickness readings over time | Submit readings, then calculate | `200`; `governing_rate_mm_yr`, `remaining_life_years`, `next_inspection_date` returned and match [test_corrosion_calculation.py](../10-Source-Code/backend/tests/test_corrosion_calculation.py) formula | | |
| SIT-AIMS-005c | Trend query returns readings in order | ≥3 readings exist | `GET /v1/equipment/{id}/thickness-records` | `200`, ordered by `reading_date` ascending | | |

## Defect Workflow

| Test ID | Scenario | Precondition | Test Step | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| SIT-AIMS-006 | Illegal transition rejected end-to-end | Defect `workflow_status=Finding` | `PUT /v1/defects/{id}` with `target_status=Repair` | `422 BUSINESS_RULE_VIOLATION` (skips Assessment/Approval) | | |
| SIT-AIMS-006b | Full workflow to closure | Defect at `Finding` | Advance through Assessment→Approval→Repair→Verification→Closed | Each step `2xx`; `closed_date` set on final transition | | |

## Reporting

| Test ID | Scenario | Precondition | Test Step | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| SIT-AIMS-007 | Dashboard aggregates reflect underlying data | Known set of assets/risk assessments seeded | Frontend Dashboard queries `/assets`, `/risk-assessments`, `/inspections` | Displayed counts match seeded data | | |
| SIT-AIMS-007b | AI Copilot query returns org-scoped sources only | Two orgs seeded with distinct risk data | `POST /v1/ai/query` as a user in Org A asking about "highest risk equipment" | Sources reference only Org A entities, never Org B | | |
| SIT-AIMS-007c | AI report generation for unknown asset | — | `POST /v1/ai/reports/generate` with a non-existent `asset_id` | `404` | | |

## IoT / Condition Monitoring Data

| Test ID | Scenario | Precondition | Test Step | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| SIT-AIMS-008 | Sensor data ingestion and query | Equipment exists | `POST /v1/sensor-data` (simulating MQTT bridge) then `GET /v1/equipment/{id}/sensor-data` | `201` on ingest; query returns the reading within the requested time range | | |
| SIT-AIMS-008b | Latest-reading-per-sensor-type dedupes correctly | 5 Temperature + 3 Pressure readings exist | `GET /v1/equipment/{id}/sensor-data/latest` | Exactly one row per `sensor_type`, most recent by `reading_timestamp` | | |

## Audit Trail

| Test ID | Scenario | Precondition | Test Step | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| SIT-AIMS-009 | Every mutation writes an audit row in the same transaction | — | Create an asset, then immediately query `GET /v1/audit-logs?entity_type=Asset&entity_id={id}` | Exactly one `Create` entry, `new_value` matches the created record | | |
| SIT-AIMS-009b | Audit log has no update/delete route | — | Confirm no `PUT`/`DELETE /v1/audit-logs/*` route exists in the OpenAPI schema | Route absent (append-only, per Database.md §12.1) | | |

---

*Related: [API-Spec.md](../05-API-Specification/API-Spec.md) · [UnitTest.md](UnitTest.md) · Next: [UAT.md](UAT.md)*
