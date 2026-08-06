# Unit Test Documentation
## Enterprise Asset Integrity Management System (AIMS)

| Field | Value |
|---|---|
| Backend Framework | pytest / pytest-asyncio |
| Frontend Framework | Jest / React Testing Library |
| Coverage Target | ≥ 80% on service-layer / calculation-engine code (NFR-09) |

---

## 1. Strategy

Business-critical calculation logic (RBI scoring, corrosion rate, criticality, defect workflow rules) is
kept as **pure, dependency-free functions** specifically so it can be unit tested without a database or
mocks — see [Backend-Design.md §2](../07-Backend-Design/Backend-Design.md#2-source-tree). Service methods
that perform I/O (DB reads/writes, audit logging) call these pure functions and are covered at the
integration level instead (see [SIT.md](SIT.md)), where a real database exercises the full path.

## 2. Implemented Test Suite

Located at [10-Source-Code/backend/tests](../10-Source-Code/backend/tests/). **Run and passing: 39/39.**

```bash
cd 10-Source-Code/backend
pip install -r requirements.txt
pytest -v
```

| Test File | Module Under Test | Cases |
|---|---|---|
| `test_corrosion_calculation.py` | `app/modules/corrosion/calculation.py` — `compute_corrosion()` (FR-18/19) | Insufficient-history error; short-term vs. long-term governing-rate selection (API 570/653 convention); remaining-life and next-inspection-date math; zero-corrosion → indefinite life; reading-order independence |
| `test_rbi_calculation.py` | `app/modules/rbi/service.py` — `_governing_cof`, `_rank_from_score`, `_pof_category` (FR-13/14/15) | COF governance (worse of safety/environmental wins); risk-rank boundary values (Low/Medium/High/VeryHigh thresholds); POF→1-5 category bucketing; end-to-end risk-score formula (POF × COF weight) |
| `test_criticality.py` | `app/modules/asset/service.py` — `_rank_from_score`, `_CRITICALITY_WEIGHTS` | Weights sum to 1.0; safety weighted highest (API 580 convention); criticality-level boundary values; full weighted-score calculation |
| `test_defect_workflow.py` | `app/modules/defect/service.py` — `_VALID_TRANSITIONS` (FR-21) | Full happy-path Finding→...→Closed is allowed; failed-verification→Repair is allowed; `Closed` is terminal; steps cannot be skipped; no illegal backward transitions except the documented verification-failure case |

## 3. Test Cases Requiring a Database (documented here, executed under SIT)

These exercise repository/service I/O and are intentionally **not** unit tests — see
[SIT.md](SIT.md) for the corresponding integration test IDs.

| Area | Behavior | SIT Reference |
|---|---|---|
| Asset Service | Duplicate `tag_number` rejected with `409 CONFLICT` | SIT-AIMS-002 |
| Inspection Service | Cannot add results to a `Completed` inspection (`422`) | SIT-AIMS-003 |
| Defect Service | Illegal workflow transition rejected by the service, not just the pure table | SIT-AIMS-006 |
| Audit Log | Every mutation writes a matching `audit_log` row in the same transaction | SIT-AIMS-009 |

## 4. Planned Coverage — Remaining Backend Modules

| Module | Priority | Notes |
|---|---|---|
| `identity/service.py` (Auth) | High | Password verification, JWT claim construction, duplicate-username rejection |
| `document/router.py` | Medium | Metadata registration validation |
| `condition_monitoring/router.py` | Medium | Sensor payload validation, time-range query bounds |
| `ai-service` copilot | Medium | `NullLLMClient`/`LocalHashEmbedding` fallback behavior; org-scoped retrieval filter (never leaks cross-org context) |

## 5. Frontend Unit Tests (Jest + React Testing Library) — Planned

| Component | What to test |
|---|---|
| `lib/utils.ts` (`riskColor`, `severityColor`, `statusColor`) | Correct color class per enum value — pure functions, straightforward to cover at 100% |
| `lib/api-client.ts` | Envelope unwrapping; `ApiError` thrown on `success: false`; 401 clears token and redirects |
| `components/risk/RiskMatrix.tsx` | Cell counts and dominant-rank coloring for a given assessment list |
| `components/inspection/InspectionChecklistForm.tsx` | Form validation, submit calls the correct endpoint with the correct payload |

---

*Related: [TestPlan.md](TestPlan.md) · [Backend-Design.md](../07-Backend-Design/Backend-Design.md) · Next: [SIT.md](SIT.md)*
