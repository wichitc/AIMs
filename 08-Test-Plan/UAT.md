# User Acceptance Test (UAT)
## Enterprise Asset Integrity Management System (AIMS)

Executed on the staging environment by the business role named, using the actual frontend (not direct API
calls). Each scenario must be signed off by a representative of that role before the corresponding module
is considered acceptance-complete (see [TestPlan.md §5](TestPlan.md#5-entry--exit-criteria)).

---

## Role: Asset Engineer

| ID | Scenario | Preconditions | Steps | Expected Result | Sign-off |
|---|---|---|---|---|---|
| UAT-AIMS-001 | Create New Asset | Logged in as Asset Engineer; Location exists | 1. Navigate to Asset Register → 2. Select location in tree → 3. Create asset with tag number, class, design data → 4. Save | Asset created successfully and appears in the list under the selected location | |
| UAT-AIMS-002 | Register Equipment Hierarchy | Asset exists | 1. Open asset detail → Equipment tab → 2. Add a Component → 3. Add an Inspection Point under that Component | Both records appear in the Equipment tab with correct `level` and parent relationship | |
| UAT-AIMS-003 | Perform Criticality Assessment | Asset exists | 1. Open asset detail → 2. Submit safety/environmental/economic scores | Criticality badge updates on the asset header immediately; level matches the weighted score (safety-weighted per API 580) | |
| UAT-AIMS-004 | Review Risk Matrix and drill into highest-risk assets | Risk assessments exist across risk ranks | 1. Open Risk page → 2. Click a matrix cell | Ranked table filters to exactly the assets in that POF/COF cell | |
| UAT-AIMS-005 | Ask the AI Copilot a risk question | At least one risk assessment exists | 1. Ask "Which equipment has the highest risk?" | Answer names the correct asset and matches the Risk page's top-ranked entry; sources are shown | |

## Role: Inspector

| ID | Scenario | Preconditions | Steps | Expected Result | Sign-off |
|---|---|---|---|---|---|
| UAT-AIMS-006 | View assigned inspections | Inspections scheduled to this inspector | 1. Open Inspections list | Only relevant inspections shown, status badges are accurate | |
| UAT-AIMS-007 | Complete an inspection checklist in the field | Inspection is `Planned` | 1. Open inspection → 2. Submit several checklist results (Pass/Fail/NA + remarks) → 3. Mark inspection Complete | Each result saved individually (visible via "Last saved at" indicator); inspection status becomes `Completed` | |
| UAT-AIMS-008 | Raise a finding with severity | Inspection is in progress | 1. Select equipment → 2. Raise finding with type/severity/description | Finding recorded and later visible on the asset's Defects trail | |
| UAT-AIMS-009 | Record thickness readings | Equipment (Inspection Point) selected | 1. Submit a thickness reading via `POST /equipment/{id}/thickness-records` (through the inspection flow) | Reading appears in the equipment's thickness history, ordered by date | |
| UAT-AIMS-010 | Use the app on a tablet/mobile device | Device with a ≤768px viewport | 1. Open the Inspection Checklist Form on a phone/tablet | Layout is single-column, buttons are large enough to tap reliably, no horizontal scrolling | |

## Role: Manager

| ID | Scenario | Preconditions | Steps | Expected Result | Sign-off |
|---|---|---|---|---|---|
| UAT-AIMS-011 | View Executive Dashboard | Data seeded across assets/risk/inspections | 1. Open Dashboard | KPI tiles (BRD §7: availability, compliance, risk distribution) render and match underlying data | |
| UAT-AIMS-012 | Approve a Risk Assessment | Risk assessment `status=Draft` or `PendingApproval` | 1. Review assessment → 2. Approve | Status becomes `Approved`; action is attributable to this manager in the audit trail | |
| UAT-AIMS-013 | Approve a repair plan on the Defect board | Defect at `Approval` column | 1. Open Defects → 2. Click "Advance to Repair" on the card | Card moves to the `Repair` column; illegal-transition attempts are rejected with a clear error, not silently allowed | |
| UAT-AIMS-014 | Review audit trail for a disputed change | A record was recently modified | 1. Open Admin/Audit (or query `/audit-logs`) filtered by entity | Old/new values and the acting user are visible for the change in question | |

---

*Related: [Swimlane.md](../04-Process-Design/Swimlane.md) · [UIUX.md](../06-Frontend-Design/UIUX.md) · [SIT.md](SIT.md) · Next: [SecurityTest.md](SecurityTest.md)*
