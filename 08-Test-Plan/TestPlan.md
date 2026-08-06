# Test Plan
## Enterprise Asset Integrity Management System (AIMS)

| Field | Value |
|---|---|
| Version | 1.0 |
| Status | Draft |
| Date | 2026-08-06 |

---

## 1. Objective

Verify that AIMS meets the functional requirements (BRD §5), non-functional requirements (BRD §6), and
business workflows (BusinessFlow.md / Swimlane.md) before each phase is considered production-ready, with
particular rigor on the calculation engines (RBI risk scoring, corrosion rate/remaining life, criticality)
and workflow state machines (defect lifecycle) that drive integrity decisions.

## 2. Test Levels

| Level | Scope | Owner | Document |
|---|---|---|---|
| Unit Test | Service-layer logic, calculation engines, validation, workflow rules | Developers | [UnitTest.md](UnitTest.md) |
| System Integration Test (SIT) | Cross-module flows through the real API against a real database | QA | [SIT.md](SIT.md) |
| User Acceptance Test (UAT) | Business-role scenarios against a staging environment | Business stakeholders + QA | [UAT.md](UAT.md) |
| Security Test | AuthN/AuthZ, injection, API security, audit trail | Security/QA | [SecurityTest.md](SecurityTest.md) |

## 3. Test Environments

| Environment | Purpose | Data |
|---|---|---|
| Local / CI | Unit tests, static analysis, build verification | None (pure functions) or ephemeral test DB |
| SIT | Integration testing against real Postgres + TimescaleDB + Redis via docker-compose | Seeded synthetic dataset |
| UAT / Staging | Business acceptance testing | Sanitized copy of representative data or synthetic dataset mirroring a real plant hierarchy |

## 4. Tools

| Purpose | Tool |
|---|---|
| Backend unit/integration tests | pytest, pytest-asyncio |
| Frontend unit tests | Jest, React Testing Library |
| API contract verification | FastAPI's generated OpenAPI schema (`/openapi.json`) diffed against [API-Spec.md](../05-API-Specification/API-Spec.md) |
| Load/availability (NFR-01/02/03) | k6 or Locust against a staging deployment (Phase 7+) |
| Security scanning | OWASP ZAP baseline scan, `pip-audit` / `npm audit` dependency scanning |

## 5. Entry / Exit Criteria

**Entry**: feature code merged, unit tests passing locally, API matches the documented spec.

**Exit** (per module):
- 100% of Unit Test cases in [UnitTest.md](UnitTest.md) passing, ≥80% line coverage on service-layer code (NFR-09)
- 100% of SIT cases in [SIT.md](SIT.md) at `Pass` status, zero `Critical`/`High` severity defects open
- UAT scenarios in [UAT.md](UAT.md) signed off by the corresponding business role
- No `Critical`/`High` findings open from [SecurityTest.md](SecurityTest.md)

## 6. Risk-Based Test Priority

Highest priority given to the modules with the greatest safety/compliance impact if wrong, per BRD §2/§7:

1. RBI risk scoring and interval recommendation (drives inspection scheduling — wrong output = missed inspection)
2. Corrosion rate / remaining-life calculation (drives repair/replace decisions)
3. Defect workflow state machine (illegal transitions could bypass approval/FFS gates)
4. Authentication/authorization/audit trail (compliance and data-integrity backbone)
5. Standard CRUD modules (Asset, Document, Maintenance) — lower risk, still covered by SIT

---

*Related: [BRD.md](../01-Business-Requirement/BRD.md) · [Backend-Design.md](../07-Backend-Design/Backend-Design.md) · Next: [UnitTest.md](UnitTest.md)*
