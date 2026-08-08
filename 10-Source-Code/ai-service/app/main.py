from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.modules.copilot.router import router as copilot_router
from app.modules.copilot.service import CopilotError


async def copilot_exception_handler(request: Request, exc: CopilotError) -> JSONResponse:
    # Matches the backend's ResponseEnvelope error shape (see backend/app/core/exceptions.py)
    # so the frontend's single ApiError parser works against both services identically —
    # previously this fell through to FastAPI's default {"detail": "..."} shape instead.
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": "AI_SERVICE_ERROR", "message": exc.message, "details": []},
        },
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="AIMS AI Engine Service",
        description="Enterprise Asset Integrity Management System — AI Copilot (RAG / LLM / Predictions)",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,  # set CORS_ORIGINS env var per environment — never "*"
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(CopilotError, copilot_exception_handler)

    app.include_router(copilot_router, prefix="/v1")

    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()
