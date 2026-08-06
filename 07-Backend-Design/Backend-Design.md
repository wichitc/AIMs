# Backend Design
## Enterprise Asset Integrity Management System (AIMS) — Core API

| Field | Value |
|---|---|
| Version | 1.0 |
| Status | Draft |
| Framework | FastAPI (Python 3.12), SQLAlchemy 2.0 (async), Pydantic v2 |

---

## 1. Architecture Style — Clean Architecture

```
API Layer (router.py)          → HTTP concerns: routing, request/response schema, status codes
    ↓ depends on
Service Layer (service.py)     → Business logic, orchestration, workflow rules
    ↓ depends on
Repository Layer (repository.py) → Data access (SQLAlchemy queries), no business logic
    ↓ depends on
Model Layer (models.py)        → SQLAlchemy ORM entities (mirrors Database.md)
```

Rules:
- Routers never touch the database directly — they call a Service.
- Services never import SQLAlchemy directly — they call a Repository.
- Repositories return ORM models or primitives — they never return HTTP-shaped objects.
- Cross-module calls happen at the Service layer only (e.g., Inspection Service calling Asset Service),
  never Repository-to-Repository.

## 2. Source Tree

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory, router registration, exception handlers
│   ├── core/
│   │   ├── config.py             # Pydantic Settings (env-driven)
│   │   ├── database.py           # Async engine/session, Base
│   │   ├── security.py           # Password hashing, JWT encode/decode
│   │   ├── exceptions.py         # AppException hierarchy + handlers
│   │   └── dependencies.py       # get_current_user, require_permission()
│   ├── common/
│   │   ├── base_model.py         # UUIDMixin, AuditMixin, SoftDeleteMixin
│   │   └── response.py           # Standard envelope / pagination schemas
│   └── modules/
│       ├── identity/             # Organization, User, Role, Permission
│       ├── asset/                # Location, AssetClass, Asset, Equipment, Criticality
│       ├── inspection/           # InspectionPlan, Inspection, InspectionResult, Finding
│       ├── rbi/                  # RiskAssessment
│       ├── corrosion/            # ThicknessRecord, CorrosionRecord
│       ├── defect/                # Defect
│       ├── condition_monitoring/ # SensorData (TimescaleDB)
│       ├── maintenance/          # MaintenanceOrder
│       ├── document/             # Document
│       └── audit_log/            # AuditLog (write-through from all modules)
├── tests/
├── requirements.txt
└── Dockerfile
```

Each business module follows the same 5-file pattern (`models.py`, `schemas.py`, `repository.py`,
`service.py`, `router.py`). This session implements **Identity, Asset, and Inspection** as fully
layered reference modules; **RBI, Corrosion, Defect, Condition Monitoring, Maintenance, Document, and
Audit Log** are scaffolded with models + a working CRUD router so the pattern is immediately extensible —
they should be split into full repository/service layers as their business logic (RBI scoring, corrosion
calculation engine, defect workflow state machine) is built out.

## 3. Cross-Cutting Concerns

| Concern | Implementation |
|---|---|
| Authentication | OAuth2 Password/SSO flow → JWT access + refresh tokens (`core/security.py`) |
| Authorization | `require_permission("asset.create")` FastAPI dependency checks JWT claim `permissions[]` |
| Validation | Pydantic v2 schemas on every request body; DB-level `CHECK` constraints as second line of defense |
| Audit Trail | `common/audit.py` writes an `audit_log` row on every service-layer mutation (before/after JSON diff) |
| Error Handling | `core/exceptions.py` maps domain exceptions → standard error envelope + correct HTTP status |
| Multi-tenancy | Every query is scoped by `org_id` derived from the JWT, never from client-supplied input |
| Async I/O | All DB access uses SQLAlchemy async sessions; no blocking calls in request path |
| Dependency Injection | FastAPI `Depends()` wires DB session, current user, and repositories into services |

## 4. Testing Strategy (implemented in Phase 6)

- Unit tests: service layer logic with repository mocked
- Integration tests: repository layer against a real (test) PostgreSQL instance
- API tests: FastAPI `TestClient` against the full stack with a disposable test DB

---

*Related: [Architecture.md](../02-System-Architecture/Architecture.md) · [Database.md](../03-Database-Design/Database.md) · [API-Spec.md](../05-API-Specification/API-Spec.md) · Source: [10-Source-Code/backend](../10-Source-Code/backend/)*
