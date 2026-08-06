import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.read_models import Asset, CorrosionRecord, Equipment, RiskAssessment
from app.llm.client import LLMClient
from app.llm.prompts import (
    QUERY_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    build_query_prompt,
    build_report_prompt,
)
from app.modules.copilot.models import AIPrediction
from app.rag.embeddings import EmbeddingProvider
from app.rag.retriever import Retriever

MODEL_VERSION = "rule-based-v1"


class CopilotError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class CopilotService:
    def __init__(self, db: AsyncSession, llm: LLMClient, embeddings: EmbeddingProvider):
        self.db = db
        self.llm = llm
        self.retriever = Retriever(db, embeddings)

    async def answer_query(self, question: str, org_id: uuid.UUID):
        contexts = await self.retriever.retrieve(question, org_id)
        prompt = build_query_prompt(question, contexts)
        answer = await self.llm.complete(QUERY_SYSTEM_PROMPT, prompt)
        sources = [{"type": c.entity_type, "id": c.entity_id} for c in contexts]
        return answer, sources

    async def generate_report(self, asset_id: uuid.UUID, org_id: uuid.UUID):
        asset = (
            await self.db.execute(select(Asset).where(Asset.id == asset_id, Asset.org_id == org_id))
        ).scalar_one_or_none()
        if not asset:
            raise CopilotError(404, f"Asset {asset_id} not found")

        contexts = await self.retriever.retrieve(f"summary of asset {asset.tag_number}", org_id)
        asset_summary = f"{asset.tag_number} — {asset.name} (status: {asset.status})"
        prompt = build_report_prompt(asset_summary, contexts)
        report = await self.llm.complete(REPORT_SYSTEM_PROMPT, prompt)
        sources = [{"type": c.entity_type, "id": c.entity_id} for c in contexts]
        return report, sources

    async def predict_failure(self, asset_id: uuid.UUID, org_id: uuid.UUID) -> AIPrediction:
        """Rule-based baseline (AI-Copilot-Design.md §5): combines latest risk_score with
        corrosion remaining_life_years into a failure-risk estimate. A confirmed seam for a
        trained model later — same table, same contract, only model_version changes."""
        asset = (
            await self.db.execute(select(Asset).where(Asset.id == asset_id, Asset.org_id == org_id))
        ).scalar_one_or_none()
        if not asset:
            raise CopilotError(404, f"Asset {asset_id} not found")

        latest_risk = (
            await self.db.execute(
                select(RiskAssessment)
                .where(RiskAssessment.asset_id == asset_id)
                .order_by(RiskAssessment.assessment_date.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        # CorrosionRecord is keyed by equipment_id, not asset_id directly — join via Equipment.
        latest_corrosion = (
            await self.db.execute(
                select(CorrosionRecord)
                .join(Equipment, Equipment.id == CorrosionRecord.equipment_id)
                .where(Equipment.asset_id == asset_id)
                .order_by(CorrosionRecord.assessment_date.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        risk_component = float(latest_risk.risk_score) / 20.0 if latest_risk else 0.3  # normalize ~0-1
        life_component = (
            max(0.0, 1.0 - (float(latest_corrosion.remaining_life_years) / 20.0)) if latest_corrosion else 0.3
        )
        failure_probability = round(min(1.0, max(0.0, 0.6 * risk_component + 0.4 * life_component)), 4)

        data_points = sum(1 for x in (latest_risk, latest_corrosion) if x is not None)
        confidence_score = round(0.4 + 0.3 * data_points, 4)  # 0.4 baseline, +0.3 per data source, max 1.0

        horizon_years = latest_corrosion.remaining_life_years if latest_corrosion else 5
        predicted_for_date = date.today() + timedelta(days=int(min(horizon_years, 10) * 365))

        prediction = AIPrediction(
            asset_id=asset_id,
            prediction_type="FailureRisk",
            predicted_value={
                "failure_probability": failure_probability,
                "basis": {
                    "risk_score": float(latest_risk.risk_score) if latest_risk else None,
                    "remaining_life_years": float(latest_corrosion.remaining_life_years)
                    if latest_corrosion
                    else None,
                },
            },
            confidence_score=min(confidence_score, 1.0),
            model_version=MODEL_VERSION,
            input_features={
                "has_risk_assessment": latest_risk is not None,
                "has_corrosion_record": latest_corrosion is not None,
            },
            predicted_for_date=predicted_for_date,
        )
        self.db.add(prediction)
        await self.db.commit()
        return prediction

    async def get_latest_predictions(self, asset_id: uuid.UUID) -> list[AIPrediction]:
        stmt = (
            select(AIPrediction)
            .where(AIPrediction.asset_id == asset_id)
            .order_by(AIPrediction.generated_at.desc())
            .limit(10)
        )
        return list((await self.db.execute(stmt)).scalars().all())
