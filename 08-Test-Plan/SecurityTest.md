# Security Test Plan
## Enterprise Asset Integrity Management System (AIMS)

Covers OWASP-aligned checks against the areas called out in the project brief: Authentication, Authorization,
SQL Injection, XSS, CSRF, API Security, and Audit Trail. Each row states the built-in mitigation (from the
actual implementation) alongside the test that verifies it — not just a checklist, but what to break.

---

## 1. Authentication

| Test ID | Check | Mitigation in Place | Test Method | Result |
|---|---|---|---|---|
| SEC-001 | Passwords are never stored in plaintext | `hash_password()` calls `bcrypt` directly ([security.py](../10-Source-Code/backend/app/core/security.py)) — switched off `passlib` after its bcrypt backend detection broke against modern bcrypt releases, caught by actually running the seed script | Inspect `user.password_hash` column value — must be a bcrypt hash, never the raw password | Pass (verified via live login test, see [Deployment.md §2.1](../09-Deployment/Deployment.md#21-test-login-local-dev-only)) |
| SEC-002 | Expired/invalid JWT is rejected | `decode_token()` raises on `JWTError`; `get_current_user` returns `401` | Send a request with a tampered/expired JWT | Expect `401 UNAUTHENTICATED` | |
| SEC-003 | Disabled accounts cannot obtain a token | `AuthService.login` checks `user.is_active` | Attempt login with a disabled account | Expect `401`, "Account is disabled" | |
| SEC-004 | Brute-force login attempts are rate-limited | API Gateway rate limit (100 req/min/user per [API-Spec.md §1.6](../05-API-Specification/API-Spec.md#16-security-baseline-applies-to-every-endpoint)) | Script 200 login attempts in 60s | Expect `429` after threshold | |
| SEC-005 | Refresh tokens cannot be used as access tokens | `get_current_user` checks `payload["type"] == "access"` | Present a refresh token to a protected endpoint | Expect `401`, "Token is not an access token" | |

## 2. Authorization (RBAC)

| Test ID | Check | Mitigation in Place | Test Method | Result |
|---|---|---|---|---|
| SEC-006 | Endpoints enforce specific permission codes, not just "logged in" | `require_permission("asset.create")` dependency on every mutating route | Call `POST /v1/assets` with a valid token lacking `asset.create` | Expect `403 FORBIDDEN` | |
| SEC-007 | A user cannot read another organization's data | Every query filters by `org_id` derived from the JWT (never client-supplied) | Authenticate as Org A, request `GET /v1/assets` with a crafted `org_id`-adjacent query param | Response contains only Org A assets — `org_id` is never accepted as a request parameter | |
| SEC-007b | A user cannot *write* data into another organization | `LocationCreate` previously accepted `org_id` directly in the request body (a write-side version of the same class of bug) — fixed to derive it from the JWT in the router/service, matching every other `*Create` schema | `POST /v1/locations` with a forged `org_id` in the body | Row is created under the caller's real org — forged value is silently dropped, not honored | Fixed and verified live: forged `org_id` request succeeded but the row landed under the real org_id (confirmed via direct DB query) |
| SEC-007c | A caller with only `user.create` cannot plant an account in another organization | `UserCreate` previously accepted `org_id` directly in the request body — same write-side gap as SEC-007b, found while building the Admin "Create User" form; fixed to derive it from the JWT in the router/service | `POST /v1/users` with a forged `org_id` in the body | New user is created under the caller's real org — forged value is silently dropped, not honored | Fixed and verified live: forged `org_id` (`...0099`) request succeeded but the row landed under the real org_id (confirmed via `GET /v1/users`) |
| SEC-008 | AI Copilot retrieval cannot leak cross-org context | `Retriever` filters `document_embedding` by `org_id` from JWT ([retriever.py](../10-Source-Code/ai-service/app/rag/retriever.py)) | Ask a question in Org A that would match Org B's embedded content | Sources returned reference only Org A entity IDs | |
| SEC-009 | Role/permission changes take effect on next login, not silently mid-session | Permissions are embedded in the JWT at issuance, not re-checked live | Revoke a permission, confirm existing token still has old claims until expiry/refresh | Documented behavior — flag as a design tradeoff (access-token TTL bounds exposure window, default 60 min) | |

## 3. SQL Injection

| Test ID | Check | Mitigation in Place | Test Method | Result |
|---|---|---|---|---|
| SEC-010 | No raw SQL string interpolation anywhere in the codebase | All queries use SQLAlchemy ORM `select()`/parameter binding — see [Backend-Design.md §3](../07-Backend-Design/Backend-Design.md#3-cross-cutting-concerns) | Static grep for `f"SELECT`, `.execute(f"`, string-concatenated SQL | Zero matches | |
| SEC-011 | Injection payloads in query/path params are inert | ORM parameterization | Submit `tag_number' OR '1'='1` as a filter value | Treated as a literal string; no query-plan change, no data leak | |
| SEC-012 | Injection payloads in JSON body fields are inert | Pydantic validates types before reaching the ORM | Submit SQLi payloads in `description`/`remarks` free-text fields | Stored as literal text, retrievable unchanged, no injection | |

## 4. Cross-Site Scripting (XSS)

| Test ID | Check | Mitigation in Place | Test Method | Result |
|---|---|---|---|---|
| SEC-013 | Free-text fields are not rendered as HTML | React escapes all interpolated text by default (no `dangerouslySetInnerHTML` anywhere in the frontend) | Submit `<script>alert(1)</script>` as a Finding description, view it in the UI | Rendered as literal text, not executed | |
| SEC-014 | API responses are JSON, not HTML | FastAPI returns `application/json` for all `/v1/*` routes | Inspect `Content-Type` header on error and success responses | Always `application/json` | |

## 5. CSRF

| Test ID | Check | Mitigation in Place | Test Method | Result |
|---|---|---|---|---|
| SEC-015 | CSRF is structurally not applicable | Stateless Bearer-token auth (`Authorization` header), no cookie-based session — a forged cross-site form POST cannot carry the token | Attempt a cross-origin form submission against a mutating endpoint without the `Authorization` header | Request fails with `401` (no token), confirming no ambient cookie auth exists | |
| SEC-016 | CORS is not left wide open in production | `allow_origins` is sourced from `settings.cors_origin_list` (`CORS_ORIGINS` env var), defaulting to `http://localhost:3000` only — never `*` — in both `backend` and `ai-service` | Verify `CORSMiddleware` config in the target environment reflects the actual deployed frontend origin(s), not the dev default | Fixed during Phase 6 (was previously `allow_origins=["*"]`) | Pass |

## 6. API Security

| Test ID | Check | Mitigation in Place | Test Method | Result |
|---|---|---|---|---|
| SEC-017 | All inputs validated before reaching business logic | Pydantic schemas with `Field()` constraints (length, pattern, range) on every request body | Submit out-of-range/malformed values (e.g. `severity="Extreme"`) | `400 VALIDATION_ERROR` before any DB write | |
| SEC-018 | Server-calculated fields cannot be spoofed by the client | `risk_score`, `risk_rank`, `governing_rate_mm_yr`, etc. are computed server-side and absent from `*Create` request schemas | Submit a `risk_score` field in the `POST /risk-assessments` body | Field is ignored; server-computed value is what's persisted | |
| SEC-019 | Error responses don't leak stack traces or internals | `AppException` handler returns only `code`/`message`/`details` ([exceptions.py](../10-Source-Code/backend/app/core/exceptions.py)) | Trigger a 500 in a non-debug environment | Response body contains no stack trace or file paths | |
| SEC-020 | Dependency vulnerabilities are tracked | `pip-audit` / `npm audit` in CI (Phase 7) | Run `npm audit` on the frontend | Confirmed clean during Phase 4 build (caught and fixed a Next.js 14.2.15 CVE by bumping to 14.2.35) | Pass |

## 7. Audit Trail

| Test ID | Check | Mitigation in Place | Test Method | Result |
|---|---|---|---|---|
| SEC-021 | Every mutation is logged with before/after state | `write_audit_log()` called from every service-layer create/update ([audit.py](../10-Source-Code/backend/app/common/audit.py)) | Perform a create and an update; query `/audit-logs` for that entity | Two entries, `old_value`/`new_value` populated correctly | |
| SEC-022 | Audit log is append-only | No `PUT`/`DELETE /audit-logs` route exists; production DB role has no `UPDATE`/`DELETE` grant on `audit_log` (per [Database.md §12.1](../03-Database-Design/Database.md)) | Attempt to modify an audit row directly via the app-level DB role | Rejected by the database, not just the API | |
| SEC-023 | Audit entries capture the acting user, not just "system" | `user_id` on every entry sourced from the authenticated `CurrentUser`, never client-supplied | Compare `audit_log.user_id` against the session that performed the action | Matches | |
| SEC-024 | Every module actually calls `write_audit_log()` — SEC-021 documents the pattern, but nothing enforced it being followed everywhere | The Document module's `POST /documents` and `POST /documents/upload` had never called `write_audit_log()` since Phase 3 — every other module's create/update endpoint did, this one silently didn't | Upload a document through the UI, then query `/audit-logs?entity_type=Document&entity_id=...` | Found via live testing: query returned zero entries for an uploaded document. Fixed — both endpoints now log `Create` with `file_name`/`document_type`. No automated check catches a *missing* audit call; this class of gap needs a code-review checklist item, not just a pattern to copy | Fixed |

## 8. Seed / Demo Data

| Test ID | Check | Mitigation in Place | Test Method | Result |
|---|---|---|---|---|
| SEC-024 | Seeded demo credentials (`admin` / `Admin@12345`, [seed.py](../10-Source-Code/backend/app/seed.py)) cannot reach staging/production | Seeding is gated behind `SEED_DEMO_DATA` (default `true` only in the local `docker-compose.yml`) | Confirm the staging/production deploy pipeline sets `SEED_DEMO_DATA=false` (or omits `app.seed` entirely) before first apply | Not yet closed — flagged as a pre-production checklist item; no K8s manifests exist yet to verify against |

---

*Related: [API-Spec.md §1.6](../05-API-Specification/API-Spec.md#16-security-baseline-applies-to-every-endpoint) · [Database.md](../03-Database-Design/Database.md) · Next: [Deployment.md](../09-Deployment/Deployment.md)*
