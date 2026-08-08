import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.llm.client import get_llm_client
from app.rag.embeddings import get_embedding_provider
from app.modules.copilot.schemas import (
    PredictionRead,
    QueryRequest,
    QueryResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    SourceRef,
)
from app.modules.copilot.service import CopilotService

router = APIRouter(tags=["AI Copilot"])


def get_copilot_service(db: AsyncSession = Depends(get_db)) -> CopilotService:
    return CopilotService(db, llm=get_llm_client(), embeddings=get_embedding_provider())


@router.post("/ai/query", response_model=ResponseEnvelope[QueryResponse])
async def query(
    payload: QueryRequest,
    service: CopilotService = Depends(get_copilot_service),
    current_user: CurrentUser = Depends(require_permission("ai.query")),
):
    answer, sources = await service.answer_query(payload.question, uuid.UUID(current_user.org_id))
    result = QueryResponse(answer=answer, sources=[SourceRef(**s) for s in sources])
    return ResponseEnvelope(data=result)


@router.post("/ai/reports/generate", response_model=ResponseEnvelope[ReportGenerateResponse])
async def generate_report(
    payload: ReportGenerateRequest,
    service: CopilotService = Depends(get_copilot_service),
    current_user: CurrentUser = Depends(require_permission("ai.generate")),
):
    report, sources = await service.generate_report(payload.asset_id, uuid.UUID(current_user.org_id))
    result = ReportGenerateResponse(report_markdown=report, sources=[SourceRef(**s) for s in sources])
    return ResponseEnvelope(data=result)


@router.get("/ai/predictions/{asset_id}", response_model=ResponseEnvelope[list[PredictionRead]])
async def get_predictions(
    asset_id: uuid.UUID,
    service: CopilotService = Depends(get_copilot_service),
    current_user: CurrentUser = Depends(require_permission("ai.read")),
):
    predictions = await service.get_latest_predictions(asset_id)
    if not predictions:
        predictions = [await service.predict_failure(asset_id, uuid.UUID(current_user.org_id))]
    result = [PredictionRead.model_validate(p, from_attributes=True) for p in predictions]
    return ResponseEnvelope(data=result)
