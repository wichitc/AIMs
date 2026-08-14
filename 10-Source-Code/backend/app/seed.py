"""Creates a demo organization, a full-access Administrator role/permission set, and a
login-ready admin user — none of this existed after migrations alone (schema only, no data),
so there was previously no way to log in. Idempotent: safe to re-run.

Usage: `python -m app.seed` (run after `alembic upgrade head`, inside the backend container
or a venv with DATABASE_URL pointed at the target database).
"""

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.modules.identity.models import Organization, Permission, Role, RolePermission, User, UserRole

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@12345"  # change immediately in any shared/staging environment
ADMIN_EMAIL = "admin@aims.local"

# Every permission code referenced by `require_permission(...)` across backend + ai-service
# (kept in sync manually — see API-Spec.md for the module list this maps to).
PERMISSION_CODES = [
    "organization.read", "organization.create",
    "user.read", "user.create",
    "role.read", "role.create",
    "location.read", "location.create",
    "asset.read", "asset.create", "asset.update",
    "inspection.read", "inspection.create", "inspection.execute",
    "risk.read", "risk.create", "risk.approve",
    "corrosion.read", "corrosion.create",
    "defect.read", "defect.create", "defect.update", "defect.approve",
    "sensor.read", "sensor.write",
    "maintenance.read", "maintenance.create", "maintenance.update",
    "document.read", "document.create",
    "audit.read",
    "material.read", "material.create",
    "supplier.read", "supplier.create",
    "sourcing.read", "sourcing.create",
    "purchase_requisition.read", "purchase_requisition.create", "purchase_requisition.approve",
    "ai.query", "ai.generate", "ai.read",
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        org = (await db.execute(select(Organization).where(Organization.code == "DEMO"))).scalar_one_or_none()
        if not org:
            org = Organization(name="AIMS Demo Corp", code="DEMO", org_type="Corporate")
            db.add(org)
            await db.flush()

        existing_codes = set(
            (await db.execute(select(Permission.code))).scalars().all()
        )
        permissions = []
        for code in PERMISSION_CODES:
            if code in existing_codes:
                continue
            module, action = code.split(".", 1)
            permission = Permission(code=code, module=module, action=action)
            db.add(permission)
            permissions.append(permission)
        await db.flush()

        all_permissions = (await db.execute(select(Permission))).scalars().all()

        role = (await db.execute(select(Role).where(Role.name == "Administrator"))).scalar_one_or_none()
        if not role:
            role = Role(name="Administrator", description="Full access — seeded for local/demo use", is_system_role=True)
            db.add(role)
            await db.flush()

        existing_role_permission_ids = {
            rp.permission_id
            for rp in (await db.execute(select(RolePermission).where(RolePermission.role_id == role.id))).scalars().all()
        }
        for permission in all_permissions:
            if permission.id in existing_role_permission_ids:
                continue
            db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        user = (await db.execute(select(User).where(User.username == ADMIN_USERNAME))).scalar_one_or_none()
        if not user:
            user = User(
                org_id=org.id,
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                full_name="AIMS Administrator",
                is_active=True,
            )
            db.add(user)
            await db.flush()

        existing_user_role = (
            await db.execute(
                select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
            )
        ).scalar_one_or_none()
        if not existing_user_role:
            db.add(UserRole(user_id=user.id, role_id=role.id, org_id=org.id))

        await db.commit()

    print("Seed complete.")
    print(f"  Login at:  http://localhost:3000/login")
    print(f"  Username:  {ADMIN_USERNAME}")
    print(f"  Password:  {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
