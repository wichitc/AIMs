import uuid
from datetime import date, datetime

from pydantic import BaseModel


class SourceRef(BaseModel):
    type: str
    id: uuid.UUID


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceRef]


class ReportGenerateRequest(BaseModel):
    asset_id: uuid.UUID


class ReportGenerateResponse(BaseModel):
    report_markdown: str
    sources: list[SourceRef]


class PredictionRead(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    prediction_type: str
    predicted_value: dict
    confidence_score: float
    model_version: str
    predicted_for_date: date | None
    generated_at: datetime

    model_config = {"from_attributes": True}
