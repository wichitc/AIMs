from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.modules.asset.router import router as asset_router
from app.modules.audit_log.router import router as audit_log_router
from app.modules.condition_monitoring.router import router as condition_monitoring_router
from app.modules.corrosion.router import router as corrosion_router
from app.modules.defect.router import router as defect_router
from app.modules.document.router import router as document_router
from app.modules.identity.router import router as identity_router
from app.modules.inspection.router import router as inspection_router
from app.modules.maintenance.router import router as maintenance_router
from app.modules.purchasing.router import router as purchasing_router
from app.modules.rbi.router import router as rbi_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AIMS Core API",
        description="Enterprise Asset Integrity Management System — Core API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,  # set CORS_ORIGINS env var per environment — never "*"
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    v1_prefix = "/v1"
    app.include_router(identity_router, prefix=v1_prefix)
    app.include_router(asset_router, prefix=v1_prefix)
    app.include_router(inspection_router, prefix=v1_prefix)
    app.include_router(rbi_router, prefix=v1_prefix)
    app.include_router(corrosion_router, prefix=v1_prefix)
    app.include_router(defect_router, prefix=v1_prefix)
    app.include_router(condition_monitoring_router, prefix=v1_prefix)
    app.include_router(maintenance_router, prefix=v1_prefix)
    app.include_router(document_router, prefix=v1_prefix)
    app.include_router(audit_log_router, prefix=v1_prefix)
    app.include_router(purchasing_router, prefix=v1_prefix)

    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()
