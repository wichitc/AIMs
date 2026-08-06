from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.copilot.router import router as copilot_router


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

    app.include_router(copilot_router, prefix="/v1")

    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()
